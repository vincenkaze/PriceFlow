import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import DemandScore, Product

PATTERNS = ['rising', 'stable', 'falling']

def gen_scores(base, count, pattern):
    scores = []
    for i in range(count):
        if pattern == 'rising':
            scores.append(int(base + i * 5 + random.randint(-5, 15)))
        elif pattern == 'falling':
            scores.append(int(base - i * 5 + random.randint(-15, 5)))
        else:
            scores.append(int(base + random.randint(-10, 10)))
    return scores

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
            pattern = random.choice(PATTERNS)
            scores = gen_scores(base_score, 30, pattern)
            for i, score in enumerate(scores):
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