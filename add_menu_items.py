from app.database.session import SessionLocal
from app.models.commerce import MenuItem
import uuid

def add_menu_items():
    db = SessionLocal()
    
    kokolet_id = uuid.UUID('016457c7-6e19-43f9-a87e-886f7c950fa4')
    knife_bud_id = uuid.UUID('d47b21f2-a0a7-48f2-b62e-07ed7aff2590')
    
    items = [
        # Kokolet Food
        MenuItem(vendor_id=kokolet_id, name="Eba and Egusi Soup", description="Delicious Eba with rich Egusi soup and assorted meat.", price=2500.0),
        MenuItem(vendor_id=kokolet_id, name="Amala and Ewedu", description="Hot Amala served with Ewedu, Gbegiri and Ogunfe.", price=3000.0),
        MenuItem(vendor_id=kokolet_id, name="Fried Turkey", description="Spicy fried turkey wings.", price=2000.0),
        MenuItem(vendor_id=kokolet_id, name="Fried Beef", description="Well seasoned fried beef.", price=1000.0),
        
        # Knife bud
        MenuItem(vendor_id=knife_bud_id, name="1kg Fresh Beef", description="Fresh, clean, and well-cut beef.", price=5000.0),
        MenuItem(vendor_id=knife_bud_id, name="1kg Chicken Parts", description="Frozen chicken parts.", price=4000.0),
        MenuItem(vendor_id=knife_bud_id, name="Fresh Goat Meat", description="1kg fresh goat meat cut to size.", price=7000.0),
    ]
    
    try:
        db.add_all(items)
        db.commit()
        print("Successfully added menu items!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_menu_items()
