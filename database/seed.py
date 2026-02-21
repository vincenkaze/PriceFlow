import sys
import os
import sqlite3

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import Category, UserType, Product, SimulatedUser
import random

#  STEP 1: Execute your original schema.sql directly (pure Python, no CLI needed)
db_path = 'instance/pricing_dev.db'
schema_path = 'database/schema.sql'

print(" Running your full schema.sql...")
conn = sqlite3.connect(db_path)
with open(schema_path, 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print(" All tables created successfully from schema.sql!")

app = create_app()

with app.app_context():
    # Clear data safely
    db.session.query(SimulatedUser).delete()
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.query(UserType).delete()
    db.session.commit()
    print(" Cleared old data...")

    # 1. 5 Psychological Profiles
    profiles = [
        ("Optimist",        0.90, 0.60, 0.35, 0.20),
        ("Pessimist",       0.70, 0.20, 0.08, 0.80),
        ("Envious",         0.85, 0.50, 0.25, 0.40),
        ("Bargain Hunter",  0.75, 0.40, 0.12, 0.90),
        ("Impulse Buyer",   0.95, 0.70, 0.45, 0.10),
    ]

    user_types = []
    for name, v, c, p, s in profiles:
        ut = UserType(type_name=name, view_probability=v, cart_probability=c,
                      purchase_probability=p, price_sensitivity=s)
        db.session.add(ut)
        user_types.append(ut)
    db.session.commit()
    print(f" Created 5 psychological profiles")

    # 2. Categories
    cats = ["Electronics", "Fashion", "Home & Kitchen"]
    categories = [Category(name=name) for name in cats]
    db.session.add_all(categories)
    db.session.commit()
    print(" Created categories")

    # 3. 20 Sample Products
    products_data = [
        ("Sony WH-1000XM5", 0, 299.99), ("iPhone 16 Pro", 0, 1199.99),
        ("Nike Air Force 1", 1, 119.99), ("Leather Jacket", 1, 189.99),
        ("Dyson V15 Vacuum", 2, 699.99), ("Instant Pot Duo", 2, 89.99),
        ("Samsung 55\" 4K TV", 0, 599.99), ("MacBook Air M3", 0, 1299.99),
        ("Adidas Ultraboost", 1, 179.99), ("Sony Wireless Earbuds", 0, 129.99),
        ("Coffee Maker", 2, 49.99), ("Gaming Chair", 2, 249.99),
        ("Apple Watch Ultra", 0, 799.99), ("Denim Jeans", 1, 59.99),
        ("Air Fryer", 2, 79.99), ("JBL Bluetooth Speaker", 0, 69.99),
        ("Winter Hoodie", 1, 69.99), ("Robot Vacuum", 2, 399.99),
        ("Laptop Stand", 0, 39.99), ("Nike Sneakers", 1, 89.99),
    ]

    for name, cat_idx, base_price in products_data:
        prod = Product(
            name=name,
            category_id=categories[cat_idx].category_id,
            base_price=base_price,
            current_price=base_price,
            stock=random.randint(30, 150),
            min_price=round(base_price * 0.7, 2),
            max_price=round(base_price * 1.5, 2)
        )
        db.session.add(prod)
    db.session.commit()
    print(" Created 20 realistic products")

    # 4. 200 Simulated Users
    for _ in range(200):
        ut = random.choice(user_types)
        sim = SimulatedUser(type_id=ut.type_id)
        db.session.add(sim)
    db.session.commit()
    print(f" Created 200 simulated users with personalities!")

    print("\n SEED COMPLETE — The system is now FULLY ALIVE!")
    print("Restart with: python run.py")
    print("You should now see real ticks every 4 seconds!")