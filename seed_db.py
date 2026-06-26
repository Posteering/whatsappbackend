import sys
import os

# Add the app directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: ensures all models registered
from app.models.commerce import VendorClass, Vendor, MenuItem
from app.models.rider import DispatchRider

def seed():
    # Ensure pgvector extension exists (required for ai_memories table)
    import psycopg2
    from app.core.config import settings
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.close()

    # Ensure all tables exist before seeding
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ─── Vendor Classes ─────────────────────────────────────────────────────────
    if db.query(VendorClass).count() > 0:
        print("Database already seeded with vendor classes.")
    else:
        print("Seeding Vendor Classes...")
        classes = [
            VendorClass(name="Food", description="Restaurants, bakeries, and food vendors."),
            VendorClass(name="Groceries", description="Supermarkets and provisions stores."),
            VendorClass(name="Pharmacy", description="Medication, wellness, and supplements."),
            VendorClass(name="Electronics", description="Computer and phone accessories."),
            VendorClass(name="Clothing", description="Fashion, boutiques, and tailors."),
            VendorClass(name="Gifts", description="Flowers, gift baskets, and souvenir shops."),
            VendorClass(name="Automotive", description="Car parts, batteries, and accessories."),
            VendorClass(name="Services", description="Printing, branding, and professional services."),
            VendorClass(name="Hardware", description="Tools, paints, and building materials."),
            VendorClass(name="Logistics", description="Bulk goods packaging and storage."),
            VendorClass(name="Laundry", description="Dry cleaning and laundry services."),
        ]
        db.add_all(classes)
        db.commit()
        print(f"  Added {len(classes)} vendor classes.")

    # ─── Vendors ─────────────────────────────────────────────────────────────────
    if db.query(Vendor).count() > 0:
        print("Database already seeded with vendors.")
    else:
        print("Seeding Vendors...")
        # Get class IDs
        class_map = {vc.name: vc.id for vc in db.query(VendorClass).all()}

        vendors_data = [
            dict(name="Ikeja City Mall Groceries", class_id=class_map.get("Groceries"), location="Ikeja",    contact_phone="08011111111", description="Fresh groceries and provisions.", rating=4.5),
            dict(name="Surulere Pharmacy",          class_id=class_map.get("Pharmacy"),  location="Surulere", contact_phone="08022222222", description="Medication, wellness, and supplements.", rating=4.8),
            dict(name="Yaba Tech Hub Accessories",  class_id=class_map.get("Electronics"), location="Yaba",  contact_phone="08033333333", description="Computer and phone accessories.", rating=4.2),
            dict(name="Lekki Phase 1 Boutique",     class_id=class_map.get("Clothing"),  location="Lekki",   contact_phone="08044444444", description="Designer clothes and fashion.", rating=4.9),
            dict(name="Victoria Island Florist",    class_id=class_map.get("Gifts"),      location="Victoria Island", contact_phone="08055555555", description="Fresh flowers and gift baskets.", rating=4.7),
            dict(name="Gbagada Bakery",             class_id=class_map.get("Food"),       location="Gbagada", contact_phone="08066666666", description="Freshly baked bread, cakes, and pastries.", rating=4.6),
            dict(name="Maryland Auto Parts",        class_id=class_map.get("Automotive"), location="Maryland", contact_phone="08077777777", description="Car parts, batteries, and accessories.", rating=4.3),
            dict(name="Festac Print Shop",          class_id=class_map.get("Services"),  location="Festac",   contact_phone="08088888888", description="Printing, branding, and graphic design.", rating=4.4),
            dict(name="Apapa Hardware Store",       class_id=class_map.get("Hardware"),  location="Apapa",    contact_phone="08099999999", description="Tools, paints, and building materials.", rating=4.1),
            dict(name="Oshodi Market Logistics",    class_id=class_map.get("Logistics"), location="Oshodi",   contact_phone="08100000000", description="Bulk goods packaging and storage.", rating=4.0),
        ]
        vendors = [Vendor(**v) for v in vendors_data]
        db.add_all(vendors)
        db.commit()
        print(f"  Added {len(vendors)} vendors.")

    # ─── Menu Items ──────────────────────────────────────────────────────────────
    if db.query(MenuItem).count() > 0:
        print("Database already seeded with menu items.")
    else:
        print("Seeding Menu Items...")
        vendor_map = {v.name: v.id for v in db.query(Vendor).all()}
        menu_items = [
            # Gbagada Bakery
            MenuItem(vendor_id=vendor_map.get("Gbagada Bakery"), name="Agege Bread",        price=500.0,  description="Soft, fresh-baked white bread.", is_available=True),
            MenuItem(vendor_id=vendor_map.get("Gbagada Bakery"), name="Chocolate Cake",     price=8500.0, description="Whole chocolate cake (1kg).", is_available=True),
            MenuItem(vendor_id=vendor_map.get("Gbagada Bakery"), name="Meat Pie",           price=700.0,  description="Golden pastry filled with seasoned minced meat.", is_available=True),
            # Surulere Pharmacy
            MenuItem(vendor_id=vendor_map.get("Surulere Pharmacy"), name="Paracetamol 500mg", price=350.0, description="Pain and fever relief (pack of 12).", is_available=True),
            MenuItem(vendor_id=vendor_map.get("Surulere Pharmacy"), name="Vitamin C 1000mg",  price=1200.0, description="Immune support supplement.", is_available=True),
            # Ikeja City Mall Groceries
            MenuItem(vendor_id=vendor_map.get("Ikeja City Mall Groceries"), name="Bag of Rice (5kg)", price=9500.0, description="Premium long-grain parboiled rice.", is_available=True),
            MenuItem(vendor_id=vendor_map.get("Ikeja City Mall Groceries"), name="Groundnut Oil (2L)", price=4200.0, description="Pure refined groundnut oil.", is_available=True),
        ]
        db.add_all(menu_items)
        db.commit()
        print(f"  Added {len(menu_items)} menu items.")

    # ─── Dispatch Riders ─────────────────────────────────────────────────────────
    if db.query(DispatchRider).count() > 0:
        print("Database already seeded with riders.")
    else:
        print("Seeding Dispatch Riders...")
        riders = [
            DispatchRider(name="John Doe",       vehicle_type="Bike",  current_location="Ikeja",           phone_number="09011111111", is_available=True,  rating=4.8),
            DispatchRider(name="Ahmed Musa",     vehicle_type="Van",   current_location="Surulere",        phone_number="09022222222", is_available=True,  rating=4.6),
            DispatchRider(name="Chinedu Okeke",  vehicle_type="Bike",  current_location="Yaba",            phone_number="09033333333", is_available=True,  rating=4.9),
            DispatchRider(name="Tunde Bakare",   vehicle_type="Truck", current_location="Lekki",           phone_number="09044444444", is_available=True,  rating=4.7),
            DispatchRider(name="Segun Ade",      vehicle_type="Bike",  current_location="Victoria Island", phone_number="09055555555", is_available=True,  rating=4.5),
            DispatchRider(name="Emeka Eze",      vehicle_type="Van",   current_location="Gbagada",         phone_number="09066666666", is_available=True,  rating=4.4),
            DispatchRider(name="Ibrahim Sani",   vehicle_type="Bike",  current_location="Maryland",        phone_number="09077777777", is_available=True,  rating=4.8),
            DispatchRider(name="Samuel Ojo",     vehicle_type="Bike",  current_location="Festac",          phone_number="09088888888", is_available=False, rating=4.3),
            DispatchRider(name="Victor Etim",    vehicle_type="Truck", current_location="Apapa",           phone_number="09099999999", is_available=True,  rating=4.2),
            DispatchRider(name="Idris Abubakar", vehicle_type="Bike",  current_location="Oshodi",          phone_number="09100000000", is_available=True,  rating=4.6),
        ]
        db.add_all(riders)
        db.commit()
        print(f"  Added {len(riders)} dispatch riders.")

    print("Seeding complete.")
    db.close()

if __name__ == "__main__":
    seed()
