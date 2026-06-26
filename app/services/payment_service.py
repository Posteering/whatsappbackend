import uuid
import logging
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.whatsapp_client = WhatsAppClient()

    async def generate_payment_link(self, user_id: uuid.UUID, phone_number: str, amount: float, conversation_id: uuid.UUID = None, order_id: uuid.UUID = None):
        """
        Mock implementation of a payment link generation for NGN.
        Would integrate with Paystack/Flutterwave here.
        """
        payment = Payment(
            user_id=user_id,
            conversation_id=conversation_id,
            amount=amount,
            currency="NGN",
            status="pending",
            provider="paystack_mock"
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        # In a real system, we'd also link payment to order_id in our Commerce schemas.
        # We will pass the payment.id back to the frontend to confirm.
        
        payment_link = f"https://pay.easyeat.mock/{payment.id}?order_id={order_id}"
        payment.payment_link = payment_link
        self.db.commit()

        # Send invoice and link via WhatsApp
        invoice_msg = (
            f"🧾 *Invoice for your order*\n\n"
            f"Amount Due: ₦{amount:,.2f}\n"
            f"Please pay using the secure link below:\n{payment_link}\n\n"
            f"Thank you!"
        )
        await self.whatsapp_client.send_text_message(to=phone_number, text=invoice_msg)
        return payment

    class MockInvoice:
        def __init__(self, invoice_id, invoice_number, amount):
            self.id = invoice_id
            self.invoice_number = invoice_number
            self.amount = amount

    class MockVirtualAccount:
        def __init__(self, bank_name, account_number, account_name):
            self.bank_name = bank_name
            self.account_number = account_number
            self.account_name = account_name

    async def create_invoice(self, order_id: uuid.UUID, amount: float):
        """Mock method for creating a Posteering invoice."""
        inv_id = str(uuid.uuid4())
        inv_number = f"INV-{str(order_id)[:6].upper()}"
        return self.MockInvoice(invoice_id=inv_id, invoice_number=inv_number, amount=amount)

    async def create_virtual_account(self, invoice_id: str):
        """Mock method for generating a virtual account."""
        import random
        # Generate a fake 10-digit account number
        acct_no = "".join([str(random.randint(0, 9)) for _ in range(10)])
        return self.MockVirtualAccount(
            bank_name="Providus Bank (Mock)",
            account_number=acct_no,
            account_name="Posteering / Kokolet Food"
        )

    async def confirm_payment(self, payment_id: uuid.UUID, order_id: uuid.UUID = None):
        """
        Confirms a payment and triggers Event 2 notification to the vendor.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            payment.status = "paid"
            self.db.commit()
        
        if order_id:
            from app.models.commerce import Order, Vendor
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = "paid"
                self.db.commit()
                vendor = self.db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
                if vendor and vendor.contact_phone:
                    await self.whatsapp_client.send_interactive_buttons(
                        to=vendor.contact_phone,
                        text=f"✅ *Payment Confirmed!*\nOrder ID: {order.id}\nAmount: ₦{order.total_amount:,.2f}\nThe customer has paid. Please proceed with fulfilling the order!",
                        buttons=[{"id": f"COMPLETE_ORDER_{order.id}", "title": "✅ Mark Completed"}]
                    )
        return payment
