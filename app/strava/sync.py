"""
sync.py
-------
Celery task definitions for Strava activity synchronization in the AI-Bike-Coach backend.

Responsibilities:
- Define Celery tasks for fetching and storing Strava activities and streams.
- Trigger analytics recalculation after new activity ingestion.
- Used by webhook and manual sync flows.

TODO:
- Complete mapping of Strava activity/stream data to DB models.
- Add bulk sync and error handling.
- Optimize for large activity/stream payloads (batch inserts).
"""

from celery import Celery
from app.db.session import SessionLocal
from app.db.models import User, Activity
from app.strava.client import get_client
from app.analytics.pmc import recalc_metrics_for_activity

celery = Celery(__name__, broker="redis://redis:6379/0")

@celery.task
def enqueue_activity_fetch(user_id:int, strava_activity_id:int):
    db = SessionLocal()
    user = db.query(User).filter_by(strava_athlete_id=user_id).first()
    client = get_client(user.access_token)
    act = client.get_activity(strava_activity_id)
    streams = client.get_activity_streams(strava_activity_id,
                types=["time", "latlng", "altitude","heartrate",
                       "watts","cadence"])
    # TODO: map to Activity + Streams rows, commit.
    recalc_metrics_for_activity.delay(str(user.id), strava_activity_id)