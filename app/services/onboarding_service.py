import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

class OnboardingService:
    def __init__(self, db: Session):
        self.db = db
        self.whatsapp_client = WhatsAppClient()

    async def handle_user_greeting(self, phone_number: str) -> User:
        """
        Check if user exists, if not create them and send a greeting message.
        """
        stmt = select(User).where(User.phone_number == phone_number)
        user = self.db.execute(stmt).scalar_one_or_none()

        if not user:
            user = User(phone_number=phone_number)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            greeting_msg = (
                "👋 Hello! I am VIOLET, your virtual assistant.\n\n"
                "Before we get started, could you please tell me your name?"
            )
            await self.whatsapp_client.send_text_message(to=phone_number, text=greeting_msg)
            return user, True # True means it's a new user
        
        return user, False
