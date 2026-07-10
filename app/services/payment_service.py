import uuid
import logging
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.whatsapp.client import WhatsAppClient
from app.services.posteering_client import posteering_client

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.whatsapp_client = WhatsAppClient()

    async def generate_payment_link(
        self,
        user_id: uuid.UUID,
        phone_number: str,
        amount: float,
        conversation_id: uuid.UUID = None,
        order_id: uuid.UUID = None,
        vendor_email: str = None,
        payer_email: str = None,
        description: str = "Order Payment",
    ):
        """
        Creates a Posteering One API virtual account for the order.
        The customer pays into the virtual account; funds are held and
        routed to the vendor on confirmation.
        """
        payment = Payment(
            user_id=user_id,
            conversation_id=conversation_id,
            order_id=order_id,
            amount=amount,
            currency="NGN",
            status="pending",
            provider="posteering_one_api",
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        # Create virtual account via Posteering One API
        reference = str(order_id or payment.id)
        va_data, error = posteering_client.create_virtual_account(
            reference=reference,
            holder_name="Violet Customer",
            holder_phone=phone_number.lstrip("+"),
        )

        if error or not va_data:
            logger.error(f"Virtual account creation failed: {error}")
            # Fallback message while Posteering servers recover
            invoice_msg = (
                f"🧾 *Payment Due*\n\n"
                f"💰 Amount: *₦{amount:,.2f}*\n"
                f"📋 {description}\n\n"
                f"⚠️ Payment system is temporarily unavailable. "
                f"Please try again in a few minutes or contact support."
            )
            await self.whatsapp_client.send_text_message(to=phone_number, text=invoice_msg)
            return payment

        # Extract virtual account details from response
        bank_name    = va_data.get("bank_name", "")
        account_no   = va_data.get("account_number", "")
        account_name = va_data.get("account_name", "Violet Pay")
        va_ref       = va_data.get("reference", reference)

        payment.provider_reference = va_ref
        payment.payment_link = f"bankaccount://{bank_name}/{account_no}"
        self.db.commit()

        # Send bank transfer details to customer via WhatsApp
        invoice_msg = (
            f"🏦 *Virtual Account — Pay via Bank Transfer*\n\n"
            f"Please transfer *₦{amount:,.2f}* to the account below.\n"
            f"Your payment is processed automatically once received.\n\n"
            f"🏛️ Bank: *{bank_name}*\n"
            f"💳 Account Number: *{account_no}*\n"
            f"👤 Account Name: *{account_name}*\n"
            f"📋 Reference: `{va_ref}`\n\n"
            f"⏰ This account is valid for *24 hours*.\n"
            f"Do NOT share this account number with anyone else."
        )
        await self.whatsapp_client.send_text_message(to=phone_number, text=invoice_msg)
        return payment

    async def confirm_payment(
        self,
        payment_id: uuid.UUID,
        order_id: uuid.UUID = None,
    ):
        """
        Marks payment as paid and notifies the vendor to fulfill the order.
        Called automatically by the Posteering webhook when payment lands.
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
                        text=(
                            f"✅ *Payment Received!*\n"
                            f"Order ID: {order.id}\n"
                            f"Amount: ₦{order.total_amount:,.2f}\n\n"
                            f"The customer has paid via bank transfer. "
                            f"Please proceed with fulfilling the order!"
                        ),
                        buttons=[
                            {"id": f"COMPLETE_ORDER_{order.id}", "title": "✅ Mark Completed"}
                        ],
                    )
        return payment

    async def cancel_payment(
        self,
        payment_id: uuid.UUID,
        order_id: uuid.UUID = None,
        reason: str = "Order cancelled",
    ):
        """Marks a payment as cancelled and updates the order status."""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            payment.status = "cancelled"
            self.db.commit()

        if order_id:
            from app.models.commerce import Order
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = "cancelled"
                self.db.commit()

        return payment
