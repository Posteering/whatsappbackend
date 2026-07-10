"""
Safe migration script: adds virtual account columns to the vendors table.
Run this once: python migrate_add_va_columns.py
"""
import sys
sys.path.insert(0, ".")

from app.database.session import engine
from sqlalchemy import text

migrations = [
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS ledger_account_id VARCHAR;",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS virtual_account_number VARCHAR;",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS virtual_account_bank VARCHAR;",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS virtual_account_bank_code VARCHAR;",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS virtual_account_provider VARCHAR;",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS virtual_account_tracking_id VARCHAR;",
]

with engine.connect() as conn:
    for stmt in migrations:
        try:
            conn.execute(text(stmt))
            print(f"[OK] {stmt}")
        except Exception as e:
            print(f"[WARN] {stmt}\n   -> {e}")
    conn.commit()

print("\nMigration complete!")
