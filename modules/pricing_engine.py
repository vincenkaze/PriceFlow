import time
import threading
import logging
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Product, PriceHistory, DemandScore, PricingRule
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

    def _get_pricing_rules(self, product):
        """Fetch pricing rules - first try category-specific, then global"""
        # Try category-specific rule first
        rule = PricingRule.query.filter(
            PricingRule.category_id == product.category_id,
            PricingRule.is_active == True
        ).first()
        
        if not rule:
            # Fall back to global rule
            rule = PricingRule.query.filter(
                PricingRule.is_global == True,
                PricingRule.is_active == True
            ).first()
        
        # Return defaults if no rule found
        if not rule:
            return {
                'demand_threshold_high': 80,
                'demand_threshold_low': 20,
                'stock_threshold_low': 10,
                'price_increase_pct': 5.0,
                'price_decrease_pct': 5.0,
                'min_price_pct': 0.7,
                'max_price_pct': 1.5
            }
        
        return {
            'demand_threshold_high': rule.demand_threshold_high,
            'demand_threshold_low': rule.demand_threshold_low,
            'stock_threshold_low': rule.stock_threshold_low,
            'price_increase_pct': rule.price_increase_pct,
            'price_decrease_pct': rule.price_decrease_pct,
            'min_price_pct': rule.min_price_pct,
            'max_price_pct': rule.max_price_pct
        }

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

        # DEBUG: Log actual demand score range for calibration
        # TODO: Remove after calibration is complete
        scores = list(demand_map.values())
        if scores:
            score_min = min(scores)
            score_max = max(scores)
            score_avg = sum(scores) / len(scores)
            # Count products in each threshold range (aligned with pricing heuristics)
            tier_very_high = sum(1 for s in scores if s > 100)
            tier_high = sum(1 for s in scores if 50 < s <= 100)
            tier_mid = sum(1 for s in scores if 10 < s <= 50)
            tier_low = sum(1 for s in scores if 5 < s <= 10)
            tier_very_low = sum(1 for s in scores if s <= 5)
            logging.debug(f"[DEMAND] Range: {score_min:.1f} - {score_max:.1f}, Avg: {score_avg:.1f} | Tiers: >100:{tier_very_high}, 51-100:{tier_high}, 11-50:{tier_mid}, 6-10:{tier_low}, <=5:{tier_very_low}")

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

            # Get pricing rules from database
            rules = self._get_pricing_rules(product)
            demand_high = rules['demand_threshold_high']
            demand_low = rules['demand_threshold_low']
            stock_low_threshold = rules['stock_threshold_low']
            increase_pct = rules['price_increase_pct'] / 100.0
            decrease_pct = rules['price_decrease_pct'] / 100.0
            min_price_pct = rules['min_price_pct']
            max_price_pct = rules['max_price_pct']
            mid_price_pct = rules.get('price_mid_pct', (min_price_pct + max_price_pct) / 2)
            min_aggressive_pct = rules.get('price_min_aggressive_pct', min_price_pct * 0.95)

            old_price = product.current_price
            new_price = old_price
            reason = "Stable"

            # Balanced pricing rules based on demand-stock balance
            # Uses rules from database
            
            # Zone 1: INCREASE - High demand + Low stock
            if demand_score > demand_high and stock_ratio < 0.3:
                new_price = min(product.base_price * max_price_pct, old_price * (1 + increase_pct))
                reason = "High demand + low stock"
            # Zone 2: INCREASE - Moderate-high demand + Adequate stock
            elif demand_score > (demand_high * 0.75) and stock_ratio < 0.5:
                new_price = min(product.base_price * mid_price_pct, old_price * (1 + increase_pct * 0.5))
                reason = "Rising demand"
            
            # Zone 3: DECREASE - Low demand + High stock
            elif demand_score < demand_low and stock_ratio > 0.6:
                new_price = max(product.base_price * min_price_pct, old_price * (1 - decrease_pct))
                reason = "Low demand + high stock"
            # Zone 4: DECREASE - Very low demand OR Excess stock
            elif demand_score < (demand_low * 0.5) or stock_ratio > 0.8:
                new_price = max(product.base_price * min_aggressive_pct, old_price * (1 - decrease_pct * 1.5))
                reason = "Weak demand" if demand_score < (demand_low * 0.5) else "Excess stock"
            
            # Zone 5: STABLE - Everything else (no price change)
            else:
                reason = "Stable"
                pass  # new_price stays as old_price

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
                        # Get latest demand score for this product
                        demand = DemandScore.query.filter_by(product_id=product.product_id)\
                            .order_by(DemandScore.calculated_at.desc()).first()
                        demand_score = demand.demand_score if demand else 0
                        
                        # Label based on actual demand score, not stock
                        if demand_score >= 80:
                            demand_label = 'HIGH DEMAND'
                        elif demand_score >= 60:
                            demand_label = 'TRENDING'
                        elif demand_score <= 30:
                            demand_label = 'LOW DEMAND'
                        else:
                            demand_label = 'STABLE'
                        
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