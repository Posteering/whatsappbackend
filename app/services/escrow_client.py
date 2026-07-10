import requests
import logging
import uuid
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.posteering.com/api/v1"


class EscrowClient:
    """
    Client for the Posteering Escrow Partner API.
    Uses a simple X-API-Key header — no HMAC signing needed.
    Get your key from admin@posteering.com
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: requests.Response):
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}

        if not response.ok:
            logger.error(f"Escrow API error {response.status_code}: {data}")
            return None, data

        return data, None

    def create_escrow(
        self,
        *,
        amount_ngn: float,
        payer_email: str,
        recipient_email: str,
        description: str,
        ttl_hours: int = 24,
        webhook_url: str = None,
        metadata: dict = None,
    ):
        """
        Create a new escrow hold.
        amount_ngn: Amount in Naira (will be converted to kobo)
        Returns (escrow_data, error)
        """
        # API expects amount in kobo (1 NGN = 100 kobo)
        amount_kobo = int(amount_ngn * 100)

        if amount_kobo < 10000:
            return None, {"message": "Minimum escrow amount is ₦100"}

        payload = {
            "type": "goods",
            "amount": amount_kobo,
            "currency": "NGN",
            "payerEmail": payer_email,
            "recipientEmail": recipient_email,
            "description": description,
            "ttlHours": ttl_hours,
        }

        if webhook_url:
            payload["webhookUrl"] = webhook_url
        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(
                f"{BASE_URL}/escrow/partner/create",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Escrow create request failed: {e}")
            return None, {"message": str(e)}

    def get_escrow(self, ref: str):
        """
        Get the current status of an escrow by its reference.
        Returns (escrow_data, error)
        """
        try:
            response = requests.get(
                f"{BASE_URL}/escrow/partner/{ref}",
                headers=self.headers,
                timeout=10,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Escrow get request failed: {e}")
            return None, {"message": str(e)}

    def release_escrow(self, ref: str, reason: str = "Order delivered and confirmed"):
        """
        Release escrowed funds to the recipient (vendor).
        Escrow must be in 'funded' status.
        Returns (result_data, error)
        """
        try:
            response = requests.patch(
                f"{BASE_URL}/escrow/partner/{ref}/release",
                headers=self.headers,
                json={"reason": reason},
                timeout=10,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Escrow release request failed: {e}")
            return None, {"message": str(e)}

    def cancel_escrow(self, ref: str, reason: str = "Order cancelled by customer"):
        """
        Cancel escrow and refund the payer (customer).
        Returns (result_data, error)
        """
        try:
            response = requests.patch(
                f"{BASE_URL}/escrow/partner/{ref}/cancel",
                headers=self.headers,
                json={"reason": reason},
                timeout=10,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Escrow cancel request failed: {e}")
            return None, {"message": str(e)}


# Singleton instance
escrow_client = EscrowClient(api_key=settings.POSTEERING_ESCROW_KEY)
