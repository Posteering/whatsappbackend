import logging
from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

class EscalationService:
    def __init__(self, db: Session):
        self.db = db
        self.whatsapp_client = WhatsAppClient()

    async def escalate_to_human(self, conversation_id: str, phone_number: str):
        """
        Escalates the conversation to a human agent via Email and WhatsApp Group.
        """
        # 1. Update DB Status
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.status = "escalated"
            self.db.commit()

        # 2. Notify the user
        msg_to_user = "I'm passing this over to our human support team. VIOLET will pause for now, and someone from our team will reply to you shortly."
        await self.whatsapp_client.send_text_message(to=phone_number, text=msg_to_user)

        # 3. Alert the Team Admin
        admin_number = "2347071149334"
        admin_msg = f"🚨 *HUMAN ESCALATION REQUEST*\n\nUser Phone: {phone_number}\nConversation ID: {conversation_id}\n\nPlease review this chat in the admin dashboard and follow up."
        await self.whatsapp_client.send_text_message(to=admin_number, text=admin_msg)

        logger.warning(f"ESCALATION TRIGGERED: Conversation {conversation_id} for user {phone_number} needs human attention!")
