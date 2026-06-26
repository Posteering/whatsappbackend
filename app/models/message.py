import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    whatsapp_message_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    role: Mapped[str] = mapped_column(String) # user, assistant, system
    type: Mapped[str] = mapped_column(String, default="text") # text, image, audio, document
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_status: Mapped[str | None] = mapped_column(String, nullable=True) # sent, delivered, read, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")
