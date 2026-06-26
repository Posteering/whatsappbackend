from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.commerce import Vendor, MenuItem, Order, OrderItem
from app.models.user import User
import uuid

router = APIRouter()

from pydantic import BaseModel

class VendorLoginRequest(BaseModel):
    vendor_id: uuid.UUID
    phone_number: str

@router.post("/login")
def vendor_login(req: VendorLoginRequest, db: Session = Depends(get_db)):
    # Normalize input phone
    clean_phone = req.phone_number.strip().replace("+", "").replace(" ", "")
    if clean_phone.startswith("0") and len(clean_phone) == 11:
        clean_phone = "234" + clean_phone[1:]

    vendor = db.query(Vendor).filter(Vendor.id == req.vendor_id).first()
    
    if not vendor or vendor.contact_phone != clean_phone:
        raise HTTPException(status_code=401, detail="Invalid Vendor ID or Phone Number")
    
    # Look up the owner's personal name from the User table
    user = db.query(User).filter(User.phone_number == vendor.contact_phone).first()
    owner_name = user.name if user and user.name else None
    
    return {
        "status": "success",
        "vendor_id": str(vendor.id),
        "vendor_name": vendor.name,
        "owner_name": owner_name,
        "location": vendor.location,
        "rating": vendor.rating,
    }

class AddMenuItemRequest(BaseModel):
    name: str
    price: float
    description: str | None = None
    image_url: str | None = None

@router.post("/{vendor_id}/catalog")
def add_catalog_item(vendor_id: uuid.UUID, req: AddMenuItemRequest, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    new_item = MenuItem(
        vendor_id=vendor_id,
        name=req.name,
        price=req.price,
        description=req.description,
        image_url=req.image_url,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"status": "success", "item": {"id": str(new_item.id), "name": new_item.name, "price": new_item.price, "description": new_item.description, "image_url": new_item.image_url}}

@router.delete("/{vendor_id}/catalog/{item_id}")
def delete_catalog_item(vendor_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.vendor_id == vendor_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"status": "success"}

@router.get("/{vendor_id}/catalog")
def get_vendor_catalog(vendor_id: uuid.UUID, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    items = db.query(MenuItem).filter(MenuItem.vendor_id == vendor_id).all()
    return {"vendor": vendor.name, "catalog": items}

@router.get("/{vendor_id}/transactions")
def get_vendor_transactions(vendor_id: uuid.UUID, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    orders = db.query(Order).filter(Order.vendor_id == vendor_id).order_by(Order.created_at.desc()).all()
    
    transactions = []
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        transactions.append({
            "order_id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "items": [{"item_id": i.menu_item_id, "quantity": i.quantity, "price": i.price_at_purchase} for i in items]
        })
        
    return {"vendor": vendor.name, "transactions": transactions}

@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: uuid.UUID, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Simple cascade simulation (in reality should rely on foreign key cascades)
    db.query(MenuItem).filter(MenuItem.vendor_id == vendor_id).delete()
    # Leaving orders for history or delete if strict
    db.delete(vendor)
    db.commit()
    
    return {"status": "success", "message": "Vendor account deleted successfully"}
