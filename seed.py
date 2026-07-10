"""
Seed Script — Creates a test vendor in a fresh database.

Run this ONCE after setting up your .env and running migrations:

    python seed.py

After running, you will be shown the Vendor ID and phone number
to use on the Login page.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.commerce import Vendor
from app.models.user import User
import uuid

db = SessionLocal()

try:
    PHONE = "2348000000001"   # change to any number
    NAME  = "Test Kitchen"

    # Create the User (who owns this vendor)
    user = db.query(User).filter(User.phone_number == PHONE).first()
    if not user:
        user = User(phone_number=PHONE, name="Demo Owner")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create the Vendor
    vendor = db.query(Vendor).filter(Vendor.contact_phone == PHONE).first()
    if not vendor:
        vendor = Vendor(
            name=NAME,
            location="Lagos, Nigeria",
            description="Seed vendor for testing",
            contact_phone=PHONE,
            is_active=True,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

    print("\n" + "="*55)
    print("  Seed complete! Use these credentials to log in:")
    print("="*55)
    print(f"  Vendor ID    : {vendor.id}")
    print(f"  Phone Number : +{PHONE}")
    print("="*55 + "\n")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
