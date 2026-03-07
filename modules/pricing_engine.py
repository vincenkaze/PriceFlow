import time
import threading
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Product, PriceHistory, DemandScore
from app.config import Config

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
        print(" PRICING ENGINE STARTED — checking DemandScore every {}s".format(self.interval))

    def _run_loop(self):
        with self.app.app_context():
            while self.running:
                try:
                    self._update_prices()
                except Exception as e:
                    print(f" Pricing error: {e}")
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

        for product in products:
            demand_score = demand_map.get(product.product_id, 0)
            stock_ratio = product.stock / 100.0 if product.stock > 0 else 0.0

            old_price = product.current_price
            new_price = old_price
            reason = "Stable"

            # Heuristic rules (from your pipeline.pdf)
            if demand_score > 80 and stock_ratio < 0.4:
                new_price = min(product.base_price * 1.5, old_price * 1.08)
                reason = "High demand + low stock"
            elif demand_score < 20 and stock_ratio > 0.7:
                new_price = max(product.base_price * 0.7, old_price * 0.93)
                reason = "Low demand + high stock"

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

        if updated > 0:
            print(f" Pricing updated {updated} products — some prices just moved!")

pricing_engine = PricingEngine()