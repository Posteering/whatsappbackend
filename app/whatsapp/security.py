import hmac
import hashlib
from fastapi import Request, HTTPException
from app.core.config import settings

async def verify_whatsapp_signature(request: Request):
    """
    Dependency to verify the X-Hub-Signature-256 header sent by WhatsApp.
    """
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing signature")
    
    # The signature looks like 'sha256=abcdef...'
    try:
        sha_name, signature_hash = signature.split("=")
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid signature format")
        
    if sha_name != "sha256":
        raise HTTPException(status_code=403, detail="Unsupported signature algorithm")

    # We need the raw body to compute the HMAC
    body = await request.body()
    
    # Calculate expected hash using our App Secret
    expected_hash = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, signature_hash):
        raise HTTPException(status_code=403, detail="Signature mismatch")
        
    return True
