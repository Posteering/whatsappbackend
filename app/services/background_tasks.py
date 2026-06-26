from celery import shared_task
from app.database.session import SessionLocal
from app.models.analytics import Analytics
from app.services.conversation_service import ConversationService
import asyncio
import logging

logger = logging.getLogger(__name__)

@shared_task
def track_analytics_event(user_id: str, event_type: str, event_data: dict):
    """
    Background task to save analytics events without blocking the main API.
    """
    try:
        db = SessionLocal()
        analytics_entry = Analytics(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data
        )
        db.add(analytics_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error tracking analytics event: {e}")
    finally:
        db.close()

@shared_task
def process_incoming_message_task(phone_number: str, message_text: str):
    """
    Background task to process an incoming WhatsApp message via ConversationService.
    """
    db = SessionLocal()
    try:
        service = ConversationService(db)
        # Celery tasks are synchronous, but ConversationService methods are async
        asyncio.run(service.process_incoming_message(phone_number, message_text))
    except Exception as e:
        logger.error(f"Error processing message: {e}")
    finally:
        db.close()

@shared_task
def send_payment_reminders_task():
    """
    Periodic task to send payment reminders to users with pending payments older than 24 hours.
    """
    import datetime
    from app.models.payment import Payment
    from app.whatsapp.client import WhatsAppClient
    
    db = SessionLocal()
    try:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
        pending_payments = db.query(Payment).filter(
            Payment.status == "pending",
            Payment.created_at <= cutoff
        ).all()
        
        if pending_payments:
            whatsapp = WhatsAppClient()
            for payment in pending_payments:
                msg = f"Reminder: Your payment of ₦{payment.amount:,.2f} is still pending. Please use this link to complete your order: {payment.payment_link}"
                # The whatsapp client is async, so we use asyncio to run it
                asyncio.run(whatsapp.send_text_message(to=payment.user.phone_number, text=msg))
    except Exception as e:
        logger.error(f"Error sending payment reminders: {e}")
    finally:
        db.close()
