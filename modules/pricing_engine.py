import time
import threading
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Product, PriceHistory, DemandScore
from app.config import Config

# Import WebSocket emitter (optional - graceful fallback)
try:
    from modules.websocket_emitter import ws_emitter
except ImportError:
    ws_emitter = None

class PricingEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
        self.interval = 10  # seconds — adjust to see changes faster/slower

    def start(self, flask_app):
        if self.running:
            return
        self.app = flask_app
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[PRICE] Engine started - checking DemandScore every {}s".format(self.interval))

    def _run_loop(self):
        with self.app.app_context():
            while self.running:
                try:
                    self._update_prices()
                except Exception as e:
                    print(f"[PRICE] Error: {e}")
                time.sleep(self.interval)

    def _update_prices(self):
        # Get the most recent demand score for each product
        latest_scores = (
            db.session.query(DemandScore)
            .filter(DemandScore.calculated_at >= datetime.utcnow() - timedelta(minutes=20))
            .order_by(DemandScore.calculated_at.desc())
            .all()
        )

        # Keep only the latest per product
        demand_map = {}
        for score in latest_scores:
            pid = score.product_id
            if pid not in demand_map:
                demand_map[pid] = score.demand_score

        products = Product.query.all()
        updated = 0
        restocked = []

        for product in products:
            # ================== AUTO RESTOCK ==================
            # If stock drops below threshold, restock automatically
            base_stock = 80  # Default base stock level
            if product.stock <= Config.AUTO_RESTOCK_THRESHOLD:
                old_stock = product.stock
                product.stock = min(product.stock + Config.AUTO_RESTOCK_AMOUNT, base_stock)
                restocked.append({
                    'product_id': product.product_id,
                    'product_name': product.name,
                    'old_stock': old_stock,
                    'new_stock': product.stock,
                    'amount_added': Config.AUTO_RESTOCK_AMOUNT
                })
                print(f"[RESTOCK] {product.name}: {old_stock} -> {product.stock} units")

            demand_score = demand_map.get(product.product_id, 0)
            stock_ratio = product.stock / 100.0 if product.stock > 0 else 0.0

            old_price = product.current_price
            new_price = old_price
            reason = "Stable"

            # Heuristic rules - scaled for decayed scoring (scores in range 0-1000+)
            # High demand (100+): Strong price increase for peak demand
            if demand_score > 100 and stock_ratio < 0.4:
                new_price = min(product.base_price * 1.5, old_price * 1.08)
                reason = "High demand + low stock"
            # Low demand (<=10): Significant price cut for oversupply
            elif demand_score <= 10 and stock_ratio > 0.7:
                new_price = max(product.base_price * 0.7, old_price * 0.93)
                reason = "Low demand + high stock"
            # Moderate-high demand (50-100): Moderate price increase
            elif demand_score > 50 and stock_ratio < 0.4:
                new_price = min(product.base_price * 1.25, old_price * 1.05)
                reason = "Rising demand + scarce stock"
            # Very low demand (<=5): Slight price reduction for excess stock
            elif demand_score <= 5 and stock_ratio > 0.8:
                new_price = max(product.base_price * 0.85, old_price * 0.95)
                reason = "Fading demand + excess stock"

            new_price = round(new_price, 2)

            if abs(new_price - old_price) > 0.01:
                product.current_price = new_price
                product.last_updated = datetime.utcnow()

                history = PriceHistory(
                    product_id=product.product_id,
                    old_price=old_price,
                    new_price=new_price,
                    demand_score=demand_score,
                    stock=product.stock,
                    change_reason=reason,
                    timestamp=datetime.utcnow()
                )
                db.session.add(history)
                updated += 1

        db.session.commit()

        # Emit restock events if any products were restocked
        if restocked:
            print(f"[RESTOCK] {len(restocked)} products restocked")
            if ws_emitter:
                ws_emitter.emit_restock({
                    'products': restocked,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        if updated > 0 or restocked:
            print(f"[PRICE] Updated {updated} products - some prices just moved!")
            
            # Emit detailed WebSocket event for homepage real-time updates
            if ws_emitter:
                # Get updated products data for homepage
                updated_products = []
                for product in products:
                    if product.current_price != product.base_price:
                        demand_label = 'HIGH DEMAND' if product.stock < 30 else ('TRENDING' if product.stock < 50 else 'STABLE')
                        change_pct = ((product.current_price - product.base_price) / product.base_price) * 100
                        updated_products.append({
                            'product_id': product.product_id,
                            'current_price': float(product.current_price),
                            'base_price': float(product.base_price),
                            'change_percent': round(change_pct, 1),
                            'demand_label': demand_label,
                            'stock': product.stock
                        })
                
                ws_emitter.emit_price_change({
                    'updated_count': updated,
                    'products': updated_products,
                    'restocked': [r['product_id'] for r in restocked],
                    'timestamp': datetime.utcnow().isoformat()
                })

pricing_engine = PricingEngine()