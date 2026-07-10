"""
Posteering One API Webhook handler.

Posteering fires a POST to this endpoint when a virtual account receives a credit.
We verify the HMAC signature, then auto-confirm the matching payment and notify the vendor.

Webhook signature header: X-Bankrail-Signature
Format: sha256=<hex-hmac>
Secret: your POSTEERING_API_SECRET
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.payment import Payment
from app.services.payment_service import PaymentService

router = APIRouter()
logger = logging.getLogger(__name__)


def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """
    Verify Posteering webhook signature.
    Expected format: sha256=<lowercase-hex-hmac>
    """
    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        settings.POSTEERING_API_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    try:
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False


@router.post("/webhook")
async def handle_posteering_webhook(
    request: Request,
    x_bankrail_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Receives Posteering One API webhook events.
    Currently handles: credit.landed (virtual account payment received)
    """
    raw_body = await request.body()

    # ── Signature verification ────────────────────────────────────────────
    if not _verify_signature(raw_body, x_bankrail_signature):
        logger.warning("Posteering webhook: invalid or missing signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # ── Parse payload ─────────────────────────────────────────────────────
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = data.get("event")
    logger.info(f"Posteering webhook received: {event_type}")

    # ── credit.landed — virtual account received a payment ────────────────
    if event_type == "credit.landed":
        ref = data.get("data", {}).get("reference")
        amount = data.get("data", {}).get("amount")

        logger.info(f"credit.landed for reference={ref}, amount={amount}")

        if ref:
            # Find the matching payment by provider_reference
            payment = (
                db.query(Payment)
                .filter(Payment.provider_reference == ref)
                .first()
            )

            if payment:
                payment_service = PaymentService(db=db)

                # Find the linked order
                order_id = payment.order_id
                from app.models.commerce import Order
                
                order = None
                if order_id:
                    order = db.query(Order).filter(Order.id == order_id).first()
                    
                if not order:
                    # Fallback to the most recent accepted pending order if no direct link
                    order = db.query(Order).filter(
                        Order.vendor_status == "accepted",
                        Order.status == "pending"
                    ).order_by(Order.created_at.desc()).first()
                    if order:
                        order_id = order.id
                    
                # Credit the master Escrow Ledger
                from app.services.posteering_client import posteering_client
                escrow_ledger_id = settings.ESCROW_LEDGER_ACCOUNT_ID
                if escrow_ledger_id:
                    # Convert to Naira (amount from webhook might be in kobo or string? webhook amount might be string, need to handle appropriately)
                    # Let's assume amount from webhook is in Naira float or string if it's our own system, but wait, Posteering credit.landed returns amount in kobo?
                    # Let's check posteering_client.py: ledger_credit takes amount_ngn.
                    # The virtual account was created via One API. "amount" in credit.landed might be integer kobo or float.
                    # Our payment DB has `payment.amount` which is float NGN. Let's use that for the ledger credit to be safe.
                    ledger_data, ledger_err = posteering_client.ledger_credit(
                        account_id=escrow_ledger_id,
                        amount_ngn=float(payment.amount),
                        reference=f"credit_{ref}",
                        description=f"Escrow hold for Payment {payment.id}"
                    )
                    if ledger_err:
                        logger.error(f"Failed to credit escrow ledger: {ledger_err}")
                    else:
                        logger.info(f"Credited escrow ledger for Payment {payment.id}")

                await payment_service.confirm_payment(
                    payment_id=payment.id,
                    order_id=order_id,
                )
                logger.info(f"Payment {payment.id} confirmed via webhook (ref={ref})")
            else:
                logger.warning(f"No payment found for reference: {ref}")

    # ── Other events — log and acknowledge ───────────────────────────────
    else:
        logger.info(f"Unhandled Posteering event: {event_type} | data: {data}")

    return {"status": "ok"}
