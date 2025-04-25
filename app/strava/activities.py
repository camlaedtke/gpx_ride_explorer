"""
activities.py
------------
API routes for activities and streams in the AI-Bike-Coach backend.

Responsibilities:
- Provide FastAPI routes for listing activities and detailed activity data
- Fetch activity streams for the ride explorer
- Serve as the data layer between the UI and the database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.session import SessionLocal
from app.db.models import Activity, Stream, User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/activities", response_model=List[Dict[str, Any]])
async def get_activities(db: Session = Depends(get_db)):
    """
    Get all activities.
    In a production app, this would filter by authenticated user.
    """
    try:
        activities = db.query(Activity).order_by(Activity.start_time.desc()).all()
        # Convert to dictionaries for JSON serialization
        return [
            {
                "id": str(activity.id),
                "strava_id": activity.strava_id,
                "user_id": str(activity.user_id),
                "name": activity.name,
                "start_time": activity.start_time.isoformat(),
                "distance_m": activity.distance_m,
                "moving_time_s": activity.moving_time_s,
                "elev_gain_m": activity.elev_gain_m,
                "avg_power": activity.avg_power,
                "avg_hr": activity.avg_hr
            }
            for activity in activities
        ]
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@router.get("/activities/{activity_id}", response_model=Dict[str, Any])
async def get_activity(activity_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific activity by ID
    """
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
        
        return {
            "id": str(activity.id),
            "strava_id": activity.strava_id,
            "user_id": str(activity.user_id),
            "name": activity.name,
            "start_time": activity.start_time.isoformat(),
            "distance_m": activity.distance_m,
            "moving_time_s": activity.moving_time_s,
            "elev_gain_m": activity.elev_gain_m,
            "avg_power": activity.avg_power,
            "avg_hr": activity.avg_hr
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity {activity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activity: {str(e)}")

@router.get("/activities/{activity_id}/streams", response_model=List[Dict[str, Any]])
async def get_activity_streams(activity_id: str, db: Session = Depends(get_db)):
    """
    Get all stream data points for a specific activity
    """
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
        
        streams = db.query(Stream).filter(Stream.activity_id == activity_id).order_by(Stream.timestamp).all()
        
        return [
            {
                "id": str(stream.id),
                "timestamp": stream.timestamp.isoformat(),
                "lat": stream.lat,
                "lon": stream.lon,
                "altitude": stream.altitude,
                "distance": stream.distance,
                "velocity_smooth": stream.velocity_smooth,
                "heartrate": stream.heartrate,
                "cadence": stream.cadence,
                "watts": stream.watts,
                "temp": stream.temp,
                "moving": stream.moving,
                "grade_smooth": stream.grade_smooth
            }
            for stream in streams
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching streams for activity {activity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching streams: {str(e)}")