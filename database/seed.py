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

print(" Checking schema...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

if 'categories' not in tables:
    print(" Creating tables from schema.sql...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    print(" All tables created successfully from schema.sql!")
else:
    print(" Tables already exist, skipping schema creation.")

conn.close()

app = create_app()

with app.app_context():
    # Clear data safely
    db.session.query(SimulatedUser).delete()
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.query(UserType).delete()
    db.session.commit()
    print(" Cleared old data...")

    # 1. 5 Psychological Profiles - Rebalanced: more viewers, fewer buyers
    profiles = [
        ("Optimist",        0.95, 0.25, 0.06, 0.30),   # 95% view, but only 6% buy
        ("Pessimist",       0.85, 0.12, 0.02, 0.85),   # mostly just looks
        ("Envious",         0.90, 0.30, 0.08, 0.50),   # window shoppers
        ("Bargain Hunter",  0.88, 0.20, 0.04, 0.95),  # waits for deals
        ("Impulse Buyer",   0.92, 0.35, 0.12, 0.15),  # only 12% actually buy
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

    # 3. 20 Sample Products with Images
    products_data = [
        # Electronics (8)
        ("PRISM Camera", 0, 5995.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuAdvDfCfUMKP1CGxNOSFu3WHQLHKa193NzdYwPEMJ3uZ8uqaXVyZ2bLgA8utCrZjsKM2yjC_VcvMYwcPPBmBs9FNid0Vkr0RCbQ6D6GGGyeuE5RYVIxYbUCqlgYiwppHo5EWesXf8DOMvErYzKHa-GuwbUGL63Ujd5QKSxYS41DPjmXD3fW4I8e6-PilKs9pIWz5BwqAwzgwyNVD22s1g32Vnlu-qjT2LsX1iDFsCMZTTf8MurHGhmvf9M2I8HDKw8yEU_x2eunKI4"),
        ("AURA Headphones", 0, 348.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuCGxSFPXvPhZj1WVKsrVmjQx94qMIPyRHBi2znIlV_sCPB_tfErtJh2TyCxSN9TxpaJJnH_rFMTle_mV1xrbc52u1rtYU11EdUbkNUIzO2UO0ZQLACoIuMzeof-V7pSoMTPJ6cJcQoRrR3jbvssgJCimU1OmCpfpdQlH-9Vluauyd_mLG1-WIR6BI-7YVUAnxg7fTaoxKuW1E8IzAdt69sDzcNUPeMKR0MvbnWu1pVtZhaeqVYgdQAcn6It1aYLlhLEE-Wg86Rfqyc"),
        ("GLIDE Mouse", 0, 99.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuD49-qydFuU7M7AbAGA0kGFckAK_zdKjFkp_2Cy63b9kGy3LEej0OufGbTBxa7AAd5tEamXvBNLgdVj_vUKVooiTRJ7kAVXo06ap2J4ZBqIDF1bRiTva8v6Bd2u9cXBqvmxYQ0VCFw99PO6H1ea5-rGJIT6bbF5qLTagqVb98X82xjmH7XFQwfOXKjs9FiVCQkVEfCUR51tijreRZqIwuyFe6CNWGgiV4srSYGmpoSRsnA3N4pEGNKd9CthwxuBGRT-bgufyNIa_yg"),
        ("NOVA Laptop", 0, 1099.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuA0eUXdUAq1PvYRNpTutOdddWYgzgDZ4uCw-W-gjNkCPuFVuXdPJfUkUElelh5fC9OtS0fT9loOGmpTf0cIYHFA17LNNUsbnEuluNTBCNPfenKNu63cM0FrBXI_XQNMDaCzbNZBOkhWUFcL5InKHXIXtrFsgZzuqv-WkXt_vfcuBy4wS7ZS6aC8VO9a4eBi97d4nBrSWBshcjA42Xc0XqDSamqbdfDhCqtu2zZsNljcLvuj0i_myYXHFYR7ZeqIJXP1O_MIqhyTPFo"),
        ("CORE Tablet", 0, 949.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuA06DdAY5xxRo9NLiTi4b2RjUSYP4Y53k8wiDlREI9dRi8hZw8W8gz96i59Ea9kWhBjKHUIMtaA6rifLyelC74o_3xEyQh3Ylr_GwDcOMZJ8lS1G1Cf3R5nUxqGcAYRmCOXXJbWJflyUWyjG8KzSqvc7KbzrGNtO_HdHolGHwEOyKYptNseYeRPIwOaOz-DcuNoRD9DG6ln9vMR9cX1KQzdP5PpXF09F3FPezh4PoyReYlsi-GeVgxvlygpSt9kp5fi05aGL07wbgA"),
        ("FLOW Tablet", 0, 799.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuBJgaca5zPSfVDT-PAWSx6LZOHZI81ZoiG8Eg5bmKWpvnK1aFl3U0WsgpZCM0lyynLfiLQT3SIctXDl6mKHdXEt38XDkaGD_53y_zhG3CiS-ds41OPq3B5dHRby4O--J1NUdKV_lPEWc_FW2JlhOKcnfliSfyQwug0_JXbHZJF72uupyaW4Zouuw0dtZh1RBBlXxxmv6XbaklILKRYR_MiXP6JLWRHYoJBp-yPssnZLU4ZW2eb7VCEZ8tlrAtjy3U3RgCU6TPbIHjU"),
        ("NEXUS Keyboard", 0, 179.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuDTUtWxvbgDrbKbnnYdrlEoLU4J5duG4Sn960e77X5fboz9icx2rYwYKsGUkS5hwysarh4sivNl9Uq7oeEuaOwKjXvVSMJWpq-AUPTEy1wR7YdC7AUcNXtpg055S6VMnOGsvfrTiq-kbhX-L4DfMqOIQpP1bYtcSACb8UJzFtuA9Mk0VhH_AKwEh8L8wHihMRHI_mGcVPG2kU2UuvagHt1UL3RUJ3XOEgpih3AqRkvVMPxERH1Yd4BnsuOe2lqFyTh2mGJWnBQPkBM"),
        ("CORE Soundbar", 0, 349.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuBoyeN8qTG4bbE5_M9M6JS0cfKW-nmHpE2PFznOI6Vf9HKHYCYiTFMbmBJtlVgB0KQQjBoxBvngEl0-2ZUHCvkGyBHNBsGPiVW8IjXfWlrL8k8dz30dqd2HCn3uIpBh_JBRga2eAUD3HrBfBb5MQvqlSyZrUfXM5zJRZbH-C_epbfF6_4bMtxOUo5APnYrXi-4r4NFnJdYEPMaI7Gc9h_qFw1EXPwb3QbkxaaABp5vYu6-m_PPvYeJVZQNMtmt1OO_8IKWb_ozkSrY"),

        # Fashion (6)
        ("SPEED Runner", 1, 120.00, "https://images.unsplash.com/photo-1637712901929-a30440e1bb28?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"),
        ("ZENITH Shades", 1, 155.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuAcFp0WR3FaJUnoiaulQ1yQlccBXrSZQjKg7srDd5aPRjiivwg-EOjQ3rccRhc9x-lLh0M1j1-hSUAjCcZrHYvZVnRIAIMralVmuJbWPk4QXf9tpeGRBTEj1OBZZ5KYLqgU-E5mQwpMdnmOBiRmoiYfuExEy5oXtUmERt2IH1jiUvuKGeM-vWWkgxRPBesAcMzb8TyMWpCZ9Ply_UBUnwhY8gc606OXLcOm2iddKbgLlLhQGaQKeTRTbLxJL-XaJt_uhVMK2cytq68"),
        ("HORIZON Bag", 1, 325.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuDjXTcz8RGYJ0DS3xSmhozZUV_6YCm3unZqVDz-YfcqqATwCuJuDvoNLlr-tgrmBUdhQ0qcwOxpJZikyQC_8Dr0CYQemEJGztIThShv_5c1Qq5zKQ8i6YAGICLfQdp2PNHtC-GlnranCzw0ZOQB1V1prmyUOTJOeurwbUP6UW1ZqXy0mRBhNqtKelTeW4In05K2NWhS3ZcACGTN9yEctTlpqiXtJOhY9DY0AHMbBxKbGuQpHsGWPyZ17JXDdIUVtDdc5SGTMYwyh6M"),
        ("ZENITH Mug", 1, 45.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuCG-7nUBFNbPDEDsVGTrEy2P3Mq03D-WjSnkUhlhztA27SALwioJ-31nJ6PnAK60lQauyg20m-qn8s5Ny4-YB47GicMhqpGwhUUK5EQekQTo6AWTXNY38oQfaJAUEdibBuIi3MnF9fwwJ4eHyS4uCnZMd-WrtRDOtw-A-D5RfcqvKw-cTv1qVtj7kxRoc1z5T49il3SP6eRbJeBKESvQGloUEo0KDPimuF5ybr7J-WFnMQ648LWqjBlskna_vPFUyfysm5OWt54KLI"),
        ("PULSE Tracker", 1, 129.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuA7XJFHH6SKRUBwzE0Z3oFJ464tyeSf5zMc_ne6dmn0DrOzyHdDKTK6zSP8uGHvUb6uQ0H6SaO8fgXzReFWvGNxGhlErIYMjLifuZao_XABUMRLypIhV8Xba9z1bPYvNQNcAf2VDMDyQhRrH2qYX3JwkJrvWEFbmo6U7DrtR_Fdtc6MSu7ClF6oDeVXj80t6CSWYwL44u-fXAS-yHV0ZWB9a-GVM7dvEed41ZSY3HGlTMRmVQyHfA1p_WHd0Tpd-FGvXhygByVCDSU"),
        ("QUANTUM Buds", 1, 199.00, "https://m.media-amazon.com/images/I/41KHWSkisXL._SX522_.jpg"),

        # Home & Kitchen (6)
        ("VYNE Chair", 2, 410.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuBeKRycWKyhPbu9qjCoqUsoS2ssiVZViPGa57S2N8kTQtC-VItgdZXA-BIZMVosFzSLi-XcAEWUXDZwIkLOXF6uI2aN1UaZMAlxyesQGTjhAEAqrOuCjO9jlc2UOAJEB7FVEi-yGcoJ6934n4dEZahKPeBWIoZH1GsVUGFJ9YmRdulT1HfzPNlAbXXMiIEPVAOPxPSu_RrmKcqdCFy2xUFYdrPMV99uLO1tUnzXiC7GdTRI7uAmChbob-MLmVFNPK--lQDRf6wFDeo"),
        ("STELLAR Lamp", 2, 89.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuBHZyZVvsTUEA05A5guYNl700Zd1jnTGc_6dQ8dwFtjpINUIPRCW-Z9kv-rpqOlwyI4QvUeXiitxjhjndpUCFKA635ioCHOXfBixG1dfw4Nn_8bwuPblLhnqnlK0AKWca_RjV1nAywDn_H5T9_tyvd00Y4pt-LEL21dbA3E91dKBwoOVGoNSYHieVkyAhHFmE2pccFJA5UMBpL1AO1tnIgFaZjLhLU9bCBfQJqUmiw9fmXPUocbeayQ7wnpfEB-Syd8x7wWnaecHKM"),
        ("TITAN Desk", 2, 850.00, "https://lh3.googleusercontent.com/aida-public/AB6AXuBaYuFqpiXD1Wokjvg7Q9-zy6DTUeVl9tHslfkNVb1oUbZwRojHylsj__Y5Lh130ldsZ4pOZinkoS8dsG4wjVZul4hFrXv1AwfH4nj8j4B-flPwKN86ve5gDQFsuo786m3-YRteYxulYedBixWafzrsrtMH-wONPpRw73l91gyyrY89zofsP_bi6gTXRkA5XBpClZ1THWa4CObAX3BxBHlX2sSinUF_RSXtzJ24GJM1DoJZre_6nfmFksb2r7IxL0wio5j2iTcqINI"),
        ("CORE Chair Pro", 2, 520.00, "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400"),
        ("Minimal Lamp", 2, 70.00, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400"),
        ("Modern Shelf", 2, 230.00, "https://www.ikea.com/in/en/images/products/kallax-shelving-unit-white__0644546_pe702768_s5.jpg?f=xl"),
    ]

    for name, cat_idx, base_price, img_url in products_data:
        prod = Product(
            name=name,
            category_id=categories[cat_idx].category_id,
            base_price=base_price,
            current_price=base_price,
            stock=random.randint(30, 150),
            min_price=round(base_price * 0.7, 2),
            max_price=round(base_price * 1.5, 2),
            image_url=img_url
        )
        db.session.add(prod)
    db.session.commit()
    print(" Created 20 realistic products with images")

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