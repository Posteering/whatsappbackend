"""
Posteering One API client.
Signing logic is taken directly from the official Python signer:
  https://posteering.com/docs/one-api/authentication#sign-a-request

Canonical string format (7 fields joined by \n):
  1. HTTP method (uppercased)
  2. Request path (no query string)
  3. Sorted, percent-encoded query string (empty string if none)
  4. One-Api-Hmac-Timestamp value (ISO 8601 UTC)
  5. One-Api-Hmac-Nonce value (unique per request)
  6. Signed-headers: comma-separated lowercase names (non-empty)
  7. Lowercase hex SHA-256 of raw request body bytes

Then, for each signed header, one extra line:
  <lowercase-header-name>:<header-value>
"""

import hashlib
import hmac
import uuid
import json
import logging
import requests
from datetime import datetime, timezone
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://one.posteering.com"


def _build_sorted_query(query: dict | None) -> str:
    """Sorted, percent-encoded query string. Returns '' if no query params."""
    if not query:
        return ""
    return "&".join(
        f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
        for k, v in sorted(query.items())
    )


def sign_one_api_request(
    *,
    method: str,
    path: str,
    key_id: str,
    secret: str,
    body: bytes = b"",
    query: dict | None = None,
    sign_headers: list[str] | None = None,
    header_values: dict | None = None,
    timestamp: str | None = None,
    nonce: str | None = None,
) -> dict:
    """
    Produces the five HMAC auth headers for a One API request.
    Matches the official Python reference signer exactly.
    """
    method = method.upper()
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    nonce = nonce or str(uuid.uuid4())
    sign_headers = sign_headers or ["one-api-hmac-timestamp", "one-api-hmac-nonce"]
    signed_headers_str = ",".join(sign_headers)
    body_hash = hashlib.sha256(body).hexdigest()

    lines = [
        method,
        path,
        _build_sorted_query(query),
        timestamp,
        nonce,
        signed_headers_str,
        body_hash,
    ]

    # Known header values map (lowercase names)
    known = {
        "one-api-hmac-timestamp": timestamp,
        "one-api-hmac-nonce": nonce,
        "one-api-hmac-key-id": key_id,
        "one-api-hmac-signed-headers": signed_headers_str,
        **(header_values or {}),
    }

    # Append each signed header's value binding line
    for name in sign_headers:
        n = name.strip().lower()
        lines.append(f"{n}:{known.get(n, '')}")

    canonical = "\n".join(lines)
    print("--- CANONICAL STRING ---")
    print(repr(canonical))
    print("------------------------")
    signature = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "One-Api-Hmac-Key-Id": key_id,
        "One-Api-Hmac-Timestamp": timestamp,
        "One-Api-Hmac-Nonce": nonce,
        "One-Api-Hmac-Signed-Headers": signed_headers_str,
        "One-Api-Hmac-Signature": signature,
    }


class PosteeringClient:
    """
    HTTP client for the Posteering One API.
    Automatically signs every request using the official HMAC scheme.
    """

    def __init__(self, key_id: str, secret: str, context: str = "violet-prod-1"):
        self.key_id = key_id
        self.secret = secret
        self.context = context  # One-Context header (your partner context name)

    def _request(
        self,
        method: str,
        path: str,
        json_data: dict | None = None,
        query: dict | None = None,
    ) -> requests.Response:
        body_bytes = (
            json.dumps(json_data, separators=(",", ":")).encode("utf-8")
            if json_data is not None
            else b""
        )

        # Include One-Context in signed headers (required for passthrough routes)
        sign_headers = [
            "one-api-hmac-timestamp",
            "one-api-hmac-nonce",
            "one-context",
        ]
        header_values = {"one-context": self.context}

        auth_headers = sign_one_api_request(
            method=method,
            path=path,
            key_id=self.key_id,
            secret=self.secret,
            body=body_bytes,
            query=query,
            sign_headers=sign_headers,
            header_values=header_values,
        )

        headers = {
            "Content-Type": "application/json",
            "One-Context": self.context,
            **auth_headers,
        }

        url = BASE_URL + path
        logger.debug(f"POST {url} | headers: {list(headers.keys())}")

        return requests.request(
            method=method,
            url=url,
            headers=headers,
            data=body_bytes if body_bytes else None,
            params=query,
            timeout=15,
        )

    def post(self, path: str, json_data: dict, query: dict | None = None) -> requests.Response:
        return self._request("POST", path, json_data=json_data, query=query)

    def get(self, path: str, query: dict | None = None) -> requests.Response:
        return self._request("GET", path, query=query)

    # ── Virtual account helpers ──────────────────────────────────────────────

    def create_virtual_account(
        self,
        reference: str,
    ) -> tuple[dict | None, dict | None]:
        """
        Provision a Bankrail FBO virtual account (Providus) for a vendor/holder.
        Returns (data, error). On success, data includes:
          - virtualAccount: the account number
          - bankCode: e.g. '101'
          - provider: e.g. 'providus'
          - trackingId: Posteering internal tracking ID
        """
        from app.core.config import settings
        path = "/api/v1/one/products/bankrail-fbo/passthrough/fbo/provision"
        callback_url = f"{settings.WEBHOOK_BASE_URL}/api/v1/webhooks/posteering/fbo"
        try:
            resp = self.post(path, {
                "holderRef": reference,
                "purposeTag": "wallet",
                "callbackUrl": callback_url,
                "currency": "NGN"
            })
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}

            if not resp.ok:
                logger.error(f"Virtual account creation failed {resp.status_code}: {data}")
                return None, data
            return data, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Virtual account request error: {e}")
            return None, {"message": str(e)}

    # ── Ledger product helpers ───────────────────────────────────────────────
    # The Ledger is self-serve — provisioned immediately, no approval needed.
    # Base passthrough path: /api/v1/one/products/ledger/passthrough/

    LEDGER_BASE = "/api/v1/one/products/ledger/passthrough"

    def _ledger(self, method: str, sub_path: str, body: dict | None = None) -> tuple[dict | None, dict | None]:
        """Internal helper for all ledger passthrough calls."""
        path = f"{self.LEDGER_BASE}{sub_path}"
        try:
            resp = self._request(method, path, json_data=body)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            if not resp.ok:
                logger.error(f"Ledger {method} {path} failed {resp.status_code}: {data}")
                return None, data
            return data, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ledger request error: {e}")
            return None, {"message": str(e)}

    def ledger_create_account(
        self,
        account_class: str = "asset",
        currencies: list[str] | None = None,
        reference: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[dict | None, dict | None]:
        """
        Create a new ledger account.
        account_class: 'asset' (for vendors/customers) or 'liability'
        currencies: list of ISO codes e.g. ['NGN']
        Returns (account_data, error)
        """
        body: dict = {
            "class": account_class,
            "currencies": currencies or ["NGN"],
        }
        if reference:
            body["reference"] = reference
        if metadata:
            body["metadata"] = metadata
        return self._ledger("POST", "/accounts", body)

    def ledger_get_account(self, account_id: str) -> tuple[dict | None, dict | None]:
        """Get a ledger account by its ID. Returns (account_data, error)."""
        return self._ledger("GET", f"/accounts/{account_id}")

    def ledger_get_balance(self, account_id: str, currency: str = "NGN") -> tuple[dict | None, dict | None]:
        """Get the balance of a ledger account. Returns (balance_data, error)."""
        return self._ledger("GET", f"/accounts/{account_id}/balances/{currency}")

    def ledger_credit(
        self,
        account_id: str,
        amount_ngn: float,
        reference: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> tuple[dict | None, dict | None]:
        """
        Post a credit entry to a ledger account (money coming IN).
        amount_ngn: Amount in Naira.
        Returns (entry_data, error)
        """
        body: dict = {
            "account_id": account_id,
            "amount": int(amount_ngn * 100),  # kobo
            "currency": "NGN",
            "type": "credit",
            "reference": reference,
            "description": description,
        }
        if metadata:
            body["metadata"] = metadata
        return self._ledger("POST", "/entries", body)

    def ledger_debit(
        self,
        account_id: str,
        amount_ngn: float,
        reference: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> tuple[dict | None, dict | None]:
        """
        Post a debit entry to a ledger account (money going OUT).
        amount_ngn: Amount in Naira.
        Returns (entry_data, error)
        """
        body: dict = {
            "account_id": account_id,
            "amount": int(amount_ngn * 100),  # kobo
            "currency": "NGN",
            "type": "debit",
            "reference": reference,
            "description": description,
        }
        if metadata:
            body["metadata"] = metadata
        return self._ledger("POST", "/entries", body)

    def ledger_transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount_ngn: float,
        reference: str,
        description: str = "",
    ) -> tuple[dict | None, dict | None]:
        """
        Transfer funds between two ledger accounts atomically.
        Returns (transfer_data, error)
        """
        body = {
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": int(amount_ngn * 100),  # kobo
            "currency": "NGN",
            "reference": reference,
            "description": description,
        }
        return self._ledger("POST", "/transfers", body)

    def ledger_list_transactions(
        self,
        account_id: str,
        limit: int = 20,
    ) -> tuple[dict | None, dict | None]:
        """List recent transactions on a ledger account. Returns (data, error)."""
        return self._ledger("GET", f"/accounts/{account_id}/entries?limit={limit}")



# Singleton instance
posteering_client = PosteeringClient(
    key_id=settings.POSTEERING_KEY_ID,
    secret=settings.POSTEERING_API_SECRET,
    context=settings.POSTEERING_CONTEXT_ID,
)
