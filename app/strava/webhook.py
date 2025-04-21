"""
webhook.py
----------
Strava webhook endpoint handlers for the AI-Bike-Coach backend.

Responsibilities:
- Expose FastAPI routes for Strava webhook verification and event handling.
- Trigger Celery tasks to fetch new activities on webhook events.
- Used by Strava to notify of new activities.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from app.db.session import SessionLocal
from app.strava.sync import enqueue_activity_fetch
from app.config import settings
import hmac
import hashlib

router = APIRouter()

@router.get("/webhook", response_class=PlainTextResponse)
async def webhook_validation(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """
    Handles the Strava webhook validation handshake.
    Strava sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
    We need to return the hub.challenge value to verify.
    """
    # The verify_token should be a secret value set in your Strava webhook config
    # For now, we'll use the client_secret as the verify_token 
    # In a production app, you might want a separate secret for this
    verify_token = settings.STRAVA_CLIENT_SECRET
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return hub_challenge
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def webhook_event(req: Request):
    """
    Handles Strava webhook events (new activities, deleted activities, etc.)
    """
    # Get the request body as bytes for signature verification
    body_bytes = await req.body()
    body = await req.json()
    
    # Verify X-Hub-Signature if present
    strava_signature = req.headers.get("X-Hub-Signature")
    if strava_signature:
        computed_signature = hmac.new(
            settings.STRAVA_CLIENT_SECRET.encode(),
            body_bytes,
            hashlib.sha1
        ).hexdigest()
        
        if not hmac.compare_digest(f"sha1={computed_signature}", strava_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process webhook event
    if body.get("aspect_type") == "create" and body.get("object_type") == "activity":
        activity_id = body["object_id"]
        user_id = body["owner_id"]
        enqueue_activity_fetch.delay(user_id, activity_id)
    
    return {"status": "ok"}