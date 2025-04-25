"""
webhook.py
----------
Strava webhook endpoint handlers for the AI-Bike-Coach backend.

Responsibilities:
- Expose FastAPI routes for Strava webhook verification and event handling.
- Trigger Celery tasks to fetch new activities on webhook events.
- Used by Strava to notify of new activities.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import PlainTextResponse, JSONResponse, Response
from sqlalchemy.orm import Session  # Added missing import
from app.db.session import SessionLocal
from app.db.models import User
from app.strava.sync import enqueue_activity_fetch
from app.config import settings
import hmac
import hashlib
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/webhook")
async def webhook_validation(request: Request):
    """
    Handle Strava webhook validation.
    
    Strava sends a GET request with these parameters:
    - hub.mode
    - hub.challenge
    - hub.verify_token
    
    We must respond with a 200 OK and a JSON object: {"hub.challenge": challenge}
    """
    # Log headers and query parameters
    logger.info(f"--- Webhook Validation Request Start ---")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query Params: {dict(request.query_params)}")
    
    # Extract the specific 'hub.challenge' parameter
    challenge = request.query_params.get("hub.challenge")
    
    if challenge:
        logger.info(f"Found hub.challenge: '{challenge}'")
        logger.info(f"Returning challenge as JSON: {{'hub.challenge': '{challenge}'}}")
        logger.info(f"--- Webhook Validation Request End ---")
        # Return the challenge in the exact format Strava expects: {"hub.challenge": challenge}
        return JSONResponse(content={"hub.challenge": challenge})
    else:
        logger.warning("No 'hub.challenge' parameter found in the request.")
        logger.info(f"--- Webhook Validation Request End ---")
        # Still return 200 OK even if no challenge, as Strava might ping it
        return JSONResponse(content={"message": "Webhook endpoint ready, no challenge provided."})

@router.post("/webhook")
async def webhook_event(req: Request, db: Session = Depends(get_db)):
    """
    Handles Strava webhook events (new activities, deleted activities, etc.)
    """
    # Get the request body as bytes for signature verification
    body_bytes = await req.body()
    body = await req.json()
    
    logger.info(f"Received webhook event: {body}")
    
    # Verify X-Hub-Signature if present
    strava_signature = req.headers.get("X-Hub-Signature")
    if strava_signature:
        computed_signature = hmac.new(
            settings.STRAVA_CLIENT_SECRET.encode(),
            body_bytes,
            hashlib.sha1
        ).hexdigest()
        
        if not hmac.compare_digest(f"sha1={computed_signature}", strava_signature):
            logger.warning(f"Invalid signature: {strava_signature}")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        logger.info("Signature verification passed")
    else:
        logger.warning("No X-Hub-Signature header present")
    
    # Process webhook event
    try:
        if body.get("aspect_type") == "create" and body.get("object_type") == "activity":
            strava_activity_id = body["object_id"]
            strava_athlete_id = body["owner_id"]
            
            logger.info(f"Processing new activity: {strava_activity_id} from athlete: {strava_athlete_id}")
            
            # Map Strava athlete ID to our internal user ID
            user = db.query(User).filter(User.strava_athlete_id == strava_athlete_id).first()
            
            if user:
                logger.info(f"Found matching user: {user.id}")
                # Use our internal user ID for the task
                enqueue_activity_fetch.delay(str(user.id), strava_activity_id)
                return {"status": "ok", "message": f"Activity {strava_activity_id} queued for processing"}
            else:
                logger.warning(f"No user found for Strava athlete ID: {strava_athlete_id}")
                return {"status": "error", "message": f"No user found for Strava athlete ID: {strava_athlete_id}"}
        
        # Log other event types but don't process them
        logger.info(f"Ignoring event: {body.get('object_type')} / {body.get('aspect_type')}")
        return {"status": "ok", "message": "Event ignored"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@router.post("/webhook-test")
async def test_webhook_event(
    strava_activity_id: int = Body(...),
    strava_athlete_id: int = Body(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to simulate a Strava webhook event.
    This endpoint allows you to manually trigger the webhook processing
    for a specific activity and athlete.
    """
    logger.info(f"Test webhook for activity {strava_activity_id} from athlete {strava_athlete_id}")
    
    # Map Strava athlete ID to our internal user ID
    user = db.query(User).filter(User.strava_athlete_id == strava_athlete_id).first()
    
    if not user:
        logger.warning(f"No user found for Strava athlete ID: {strava_athlete_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"No user found for Strava athlete ID: {strava_athlete_id}"
        )
    
    # Enqueue the activity fetch task
    logger.info(f"Enqueueing activity {strava_activity_id} for user {user.id}")
    task = enqueue_activity_fetch.delay(str(user.id), strava_activity_id)
    
    return {
        "status": "ok",
        "message": f"Activity {strava_activity_id} queued for processing",
        "task_id": task.id,
        "user_id": str(user.id)
    }