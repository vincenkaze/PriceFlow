import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import DemandScore, Product

def seed_demand_history():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        if not products:
            print("No products found. Run seed.py first.")
            return

        db.session.query(DemandScore).delete()
        db.session.commit()
        print(f"Seeding demand history for {len(products)} products...")

        now = datetime.utcnow()
        for product in products:
            base_score = random.randint(25, 40)
            for i in range(30):
                score = base_score + i * 2 + random.randint(-5, 5)
                score = max(1, min(120, score))
                ts = now - timedelta(minutes=(30 - i) * 15)

                ds = DemandScore(
                    product_id=product.product_id,
                    demand_score=score,
                    period_start=ts - timedelta(minutes=15),
                    period_end=ts,
                    calculated_at=ts
                )
                db.session.add(ds)

        db.session.commit()
        print(f"Seeded 30 demand score records per product — trend charts will show data on next refresh.")

if __name__ == '__main__':
    seed_demand_history()