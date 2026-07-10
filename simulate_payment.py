import asyncio
import sys
sys.path.insert(0, ".")
from app.database.session import SessionLocal
from app.models.commerce import Order, Vendor
from app.models.user import User
from app.whatsapp.client import WhatsAppClient

async def simulate_payment():
    print("Looking for the most recent accepted order...")
    db = SessionLocal()
    
    # Find the latest order that is waiting for payment (vendor_status = 'accepted', status = 'pending')
    order = db.query(Order).filter(
        Order.vendor_status == "accepted",
        Order.status == "pending"
    ).order_by(Order.created_at.desc()).first()

    if not order:
        print("❌ No accepted orders found waiting for payment.")
        db.close()
        return

    print(f"Found Order: #{str(order.id)[:8]} (Total: NGN {order.total_amount})")
    print("Marking order as PAID...")
    
    order.status = "paid"
    db.commit()

    customer = db.query(User).filter(User.id == order.user_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()

    wa_client = WhatsAppClient()

    # Notify Customer
    if customer:
        print(f"Notifying Customer ({customer.phone_number})...")
        await wa_client.send_text_message(
            to=customer.phone_number,
            text=f"✅ *Payment Successful!*\nYour payment of ₦{order.total_amount:,.2f} for Order #{str(order.id)[:8]} has been securely held in escrow.\n\nThe vendor is now processing your order."
        )

    # Notify Vendor
    if vendor:
        print(f"Notifying Vendor ({vendor.contact_phone})...")
        await wa_client.send_text_message(
            to=vendor.contact_phone,
            text=f"💸 *Payment Received!*\nThe customer has successfully paid ₦{order.total_amount:,.2f} for Order #{str(order.id)[:8]}.\n\nPlease prepare the order and click *Complete Order* when it is ready or dispatched.",
            # We can optionally send an interactive button to complete the order here, 
            # but they can also do it from the Vendor Dashboard menu.
        )

    print("✅ Payment simulation complete!")
    db.close()

if __name__ == "__main__":
    asyncio.run(simulate_payment())
