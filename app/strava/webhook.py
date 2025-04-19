# strava/webhook.py: FastAPI router for Strava webhooks
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/webhook")
async def strava_webhook_challenge(request: Request):
    # Strava webhook verification challenge
    args = dict(request.query_params)
    if args.get("hub.mode") == "subscribe":
        return {"hub.challenge": args.get("hub.challenge")}
    return {"status": "ok"}

@router.post("/webhook")
async def strava_webhook_event(request: Request):
    # TODO: Validate event, enqueue Celery sync task
    event = await request.json()
    # TODO: Add signature validation
    # TODO: Enqueue Celery task to fetch activity
    return {"status": "ok"}
