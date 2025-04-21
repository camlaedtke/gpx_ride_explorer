"""
sync_routes.py
-------------
API routes for manually triggering Strava activity synchronization.

Responsibilities:
- Provide endpoints for manual activity sync operations
- Trigger Celery tasks for sync operations
- Return status information about sync operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from app.db.session import SessionLocal
from app.db.models import User, Activity
from app.strava.sync import sync_initial_activities, fetch_and_store_activity
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SyncRequest(BaseModel):
    user_id: str
    days_back: int = 30


class ActivitySyncRequest(BaseModel):
    user_id: str
    strava_activity_id: int


@router.post("/initial-sync")
async def initial_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    """
    Trigger initial synchronization of activities for a user
    """
    # Verify user exists
    db = SessionLocal()
    user = db.query(User).filter(User.id == request.user_id).first()
    db.close()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {request.user_id} not found")
    
    # Schedule sync task in the background
    task = sync_initial_activities.delay(request.user_id, request.days_back)
    
    return {
        "status": "started",
        "message": f"Initial sync started for user {request.user_id}, past {request.days_back} days",
        "task_id": task.id
    }


@router.post("/sync-activity")
async def sync_activity(request: ActivitySyncRequest):
    """
    Sync a specific Strava activity
    """
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {request.user_id} not found")
        
        # Check if activity already exists
        existing = db.query(Activity).filter(Activity.strava_id == request.strava_activity_id).first()
        if existing:
            return {
                "status": "exists",
                "message": f"Activity {request.strava_activity_id} already exists",
                "activity_id": str(existing.id)
            }
        
        # Fetch and store activity
        activity_id = fetch_and_store_activity(db, request.user_id, request.strava_activity_id)
        
        return {
            "status": "success",
            "message": f"Activity {request.strava_activity_id} synced successfully",
            "activity_id": str(activity_id)
        }
    except Exception as e:
        logger.error(f"Error syncing activity: {e}")
        raise HTTPException(status_code=500, detail=f"Error syncing activity: {str(e)}")
    finally:
        db.close()