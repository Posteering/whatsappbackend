from app.database.session import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS vendor_status VARCHAR DEFAULT 'pending'"))
    conn.commit()
print("Success")
