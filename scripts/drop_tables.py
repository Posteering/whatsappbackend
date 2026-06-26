import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from app.core.config import settings

def drop():
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        conn.execute("DROP TABLE IF EXISTS cart_items CASCADE;")
        conn.execute("DROP TABLE IF EXISTS order_items CASCADE;")
        conn.execute("DROP TABLE IF EXISTS menu_items CASCADE;")
        conn.execute("DROP TABLE IF EXISTS vendor_classes CASCADE;")
        conn.execute("DROP TABLE IF EXISTS vendors CASCADE;")
        conn.execute("DROP TABLE IF EXISTS order_payments CASCADE;")
        conn.execute("DROP TABLE IF EXISTS invoices CASCADE;")
        conn.execute("DROP TABLE IF EXISTS order_status_updates CASCADE;")
        conn.execute("DROP TABLE IF EXISTS orders CASCADE;")
        conn.execute("DROP TABLE IF EXISTS cart CASCADE;")
        conn.execute("DROP TABLE IF EXISTS virtual_accounts CASCADE;")

if __name__ == "__main__":
    drop()
    print("Tables dropped.")
