import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def send_text_message(self, to: str, text: str):
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        return await self._send_request(payload)

    async def send_interactive_buttons(self, to: str, text: str, buttons: list[dict]):
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": text
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn["id"],
                                "title": btn["title"]
                            }
                        } for btn in buttons[:3] # WhatsApp allows max 3 buttons
                    ]
                }
            }
        }
        return await self._send_request(payload)

    async def send_interactive_list(self, to: str, text: str, button_text: str, sections: list[dict]):
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": text
                },
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        return await self._send_request(payload)

    async def _send_request(self, payload: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.api_url}/messages", json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp API error: {e.response.text}")
                raise
