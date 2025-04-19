"""
webhook.py
----------
Strava webhook endpoint handlers for the AI-Bike-Coach backend.

Responsibilities:
- Expose FastAPI routes for Strava webhook verification and event handling.
- Trigger Celery tasks to fetch new activities on webhook events.
- Used by Strava to notify of new activities.

TODO:
- Add GET /webhook for Strava verification handshake.
- Add X‑Strava‑Signature header validation for security.
- Improve error handling and logging.
"""

from fastapi import APIRouter, Request, Depends
from app.db.session import SessionLocal
from app.strava.sync import enqueue_activity_fetch

router = APIRouter()

@router.post("/webhook")
async def webhook_event(req: Request):
    body = await req.json()
    if body.get("aspect_type") == "create":
        activity_id = body["object_id"]
        user_id = body["owner_id"]
        enqueue_activity_fetch.delay(user_id, activity_id)
    return {"status": "ok"}