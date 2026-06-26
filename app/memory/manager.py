import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.memory import AIMemory

class MemoryManager:
    def __init__(self, db: Session):
        self.db = db

    def save_memory(self, user_id: uuid.UUID, memory_type: str, content: str, embedding: list[float]):
        """
        Saves a new memory with its pgvector embedding.
        """
        memory = AIMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def retrieve_relevant_memories(self, user_id: uuid.UUID, query_embedding: list[float], limit: int = 5):
        """
        Retrieves the most relevant memories using pgvector cosine similarity (<=>).
        """
        stmt = (
            select(AIMemory)
            .where(AIMemory.user_id == user_id)
            .order_by(AIMemory.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return result.scalars().all()
