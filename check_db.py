import sqlite3

db_name = "instance/pricing_dev.db"  # switch between both

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

print(f"\n Checking {db_name}\n")

cursor.execute("""
SELECT product_id, old_price, new_price, change_reason
FROM price_history
ORDER BY timestamp DESC
LIMIT 5
""")

print("\n Recent Price Changes:")
for row in cursor.fetchall():
    print(row)

conn.close()