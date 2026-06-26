import anthropic
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        # Use the synchronous client since Celery workers run in sync context
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = "claude-sonnet-4-5"

    async def generate_response(self, system_prompt: str, user_message: str, context: list = None) -> str:
        messages = []

        if context:
            for msg in context:
                if msg["role"] in ("user", "assistant"):
                    messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        logger.warning("Claude does not support embeddings. Returning empty list.")
        return []
