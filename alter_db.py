import sys
import os
from sqlalchemy import text
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import engine

def alter():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN image_url VARCHAR;"))
            conn.commit()
            print("Successfully added image_url to menu_items.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    alter()
