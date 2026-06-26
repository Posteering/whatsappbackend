from fastapi import APIRouter, Request, Response, HTTPException, Depends, Query
from app.core.config import settings
from app.whatsapp.security import verify_whatsapp_signature
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"), 
    hub_challenge: str = Query(None, alias="hub.challenge"), 
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Webhook verification for WhatsApp Cloud API.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp", dependencies=[Depends(verify_whatsapp_signature)])
async def receive_message(request: Request):
    """
    Receive incoming messages and status updates from WhatsApp.
    """
    from app.core.celery_app import celery_app

    payload = await request.json()
    logger.warning(f"Received webhook payload: {payload}")
    
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # Check for messages
                if "messages" in value:
                    for message in value["messages"]:
                        # Extract sender phone number and text body
                        phone_number = message.get("from")
                        message_text = None
                        
                        if message.get("type") == "text":
                            message_text = message["text"]["body"]
                        elif message.get("type") == "image":
                            media_id = message["image"]["id"]
                            caption = message["image"].get("caption", "")
                            message_text = f"[IMAGE_UPLOADED: {media_id}] {caption}"
                        elif message.get("type") == "interactive":
                            interactive = message.get("interactive", {})
                            if interactive.get("type") == "button_reply":
                                btn_id = interactive["button_reply"]["id"]
                                btn_title = interactive["button_reply"]["title"]
                                message_text = f"[INTERACTIVE_BTN: {btn_id}] {btn_title}"
                            elif interactive.get("type") == "list_reply":
                                list_id = interactive["list_reply"]["id"]
                                list_title = interactive["list_reply"]["title"]
                                message_text = f"[INTERACTIVE_BTN: {list_id}] {list_title}"

                        if message_text:
                            # Dispatch to Celery background task
                            celery_app.send_task(
                                "app.services.background_tasks.process_incoming_message_task",
                                args=[phone_number, message_text]
                            )
                
                # Check for statuses (delivered/read)
                elif "statuses" in value:
                    for status in value["statuses"]:
                        pass # Could process delivery receipts here

    except Exception as e:
        logger.warning(f"Exception in webhook: {e}", exc_info=True)
        
    return {"status": "ok"}
