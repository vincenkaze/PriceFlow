import time
import threading
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Product, PriceHistory, UserAction
from app.config import Config

class PricingEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
        self.update_interval = 8   # update prices every 8 seconds (slower than simulation for visibility)

    def start(self, flask_app):
        if self.running:
            return
        self.app = flask_app
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(" PRICING ENGINE STARTED — Prices will now react to demand & stock!")

    def _run_loop(self):
        with self.app.app_context():
            while self.running:
                try:
                    self._update_prices()
                except Exception as e:
                    print(f" Pricing error: {e}")
                time.sleep(self.update_interval)

    def _update_prices(self):
        products = Product.query.all()
        updated = 0

        for product in products:
            # Calculate recent demand (last 15 minutes)
            demand = db.session.query(UserAction).filter(
                UserAction.product_id == product.product_id,
                UserAction.timestamp >= datetime.utcnow() - timedelta(minutes=15)
            ).count()

            # Weighted demand (purchase = heavy)
            weighted_demand = db.session.query(UserAction).filter(
                UserAction.product_id == product.product_id,
                UserAction.timestamp >= datetime.utcnow() - timedelta(minutes=15)
            ).with_entities(
                db.func.sum(db.case(
                    (UserAction.action_type == 'view', 1),
                    (UserAction.action_type == 'cart', 3),
                    (UserAction.action_type == 'purchase', 5),
                    else_=0
                ))
            ).scalar() or 0

            stock_ratio = product.stock / 100.0 if product.stock > 0 else 0

            # Heuristic pricing logic
            old_price = product.current_price
            new_price = old_price

            if weighted_demand > 80 and stock_ratio < 0.4:      # High demand + low stock
                new_price = min(product.max_price or product.base_price * 1.5, old_price * 1.08)
                reason = "High demand + low stock"
            elif weighted_demand < 20 and stock_ratio > 0.7:    # Low demand + high stock
                new_price = max(product.min_price or product.base_price * 0.7, old_price * 0.93)
                reason = "Low demand + high stock"
            else:
                reason = "Stable"

            if abs(new_price - old_price) > 0.01:
                product.current_price = round(new_price, 2)
                product.last_updated = datetime.utcnow()

                # Log price history
                history = PriceHistory(
                    product_id=product.product_id,
                    old_price=old_price,
                    new_price=product.current_price,
                    demand_score=weighted_demand,
                    stock=product.stock,
                    change_reason=reason,
                    timestamp=datetime.utcnow()
                )
                db.session.add(history)
                updated += 1

        db.session.commit()

        if updated > 0:
            print(f" Pricing updated {updated} products — some prices just moved!")

pricing_engine = PricingEngine()