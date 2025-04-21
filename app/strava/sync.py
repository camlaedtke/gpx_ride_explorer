"""
sync.py
-------
Celery task definitions for Strava activity synchronization in the AI-Bike-Coach backend.

Responsibilities:
- Define Celery tasks for fetching and storing Strava activities and streams.
- Trigger analytics recalculation after new activity ingestion.
- Used by webhook and manual sync flows.
"""

from celery import Celery
import datetime as dt
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, Activity, Stream
from app.strava.client import get_client
from app.analytics.pmc import recalc_metrics_for_activity
import logging

logger = logging.getLogger(__name__)
celery = Celery(__name__, broker="redis://redis:6379/0")

@celery.task
def enqueue_activity_fetch(user_id: str, strava_activity_id: int):
    """
    Fetch a single activity from Strava and store it in the database
    """
    try:
        db = SessionLocal()
        fetch_and_store_activity(db, user_id, strava_activity_id)
        db.close()
    except Exception as e:
        logger.error(f"Error fetching activity {strava_activity_id} for user {user_id}: {e}")
        raise


def fetch_and_store_activity(db: Session, user_id: str, strava_activity_id: int) -> Optional[uuid.UUID]:
    """
    Fetch a single activity from Strava and store in database
    Returns the UUID of the created activity
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    client = get_client(user_id=user_id)
    
    # Get activity details
    strava_activity = client.get_activity(strava_activity_id)
    
    # Check if activity already exists
    existing = db.query(Activity).filter(Activity.strava_id == strava_activity_id).first()
    if existing:
        logger.info(f"Activity {strava_activity_id} already exists, skipping")
        return existing.id
    
    # Create new activity
    new_activity = Activity(
        id=uuid.uuid4(),
        user_id=user.id,
        strava_id=strava_activity_id,
        name=strava_activity.name,
        start_time=strava_activity.start_date,
        distance_m=float(strava_activity.distance),
        moving_time_s=strava_activity.moving_time.total_seconds() if strava_activity.moving_time else None,
        elev_gain_m=float(strava_activity.total_elevation_gain) if strava_activity.total_elevation_gain else None,
        avg_power=float(strava_activity.average_watts) if strava_activity.average_watts else None,
        avg_hr=float(strava_activity.average_heartrate) if strava_activity.average_heartrate else None,
    )
    
    db.add(new_activity)
    db.flush()  # Get ID without committing
    
    # Get streams data
    try:
        streams = client.get_activity_streams(
            strava_activity_id,
            types=["time", "latlng", "altitude", "heartrate", "watts", "cadence", "velocity_smooth", "temp", "moving", "grade_smooth"]
        )
        
        if streams and 'time' in streams and 'latlng' in streams:
            # Create stream entries
            stream_objects = []
            
            time_data = streams['time'].data
            latlng_data = streams['latlng'].data
            
            # Optional streams
            altitude_data = streams.get('altitude', {}).data if 'altitude' in streams else [None] * len(time_data)
            heartrate_data = streams.get('heartrate', {}).data if 'heartrate' in streams else [None] * len(time_data)
            watts_data = streams.get('watts', {}).data if 'watts' in streams else [None] * len(time_data)
            cadence_data = streams.get('cadence', {}).data if 'cadence' in streams else [None] * len(time_data)
            velocity_data = streams.get('velocity_smooth', {}).data if 'velocity_smooth' in streams else [None] * len(time_data)
            temp_data = streams.get('temp', {}).data if 'temp' in streams else [None] * len(time_data)
            moving_data = streams.get('moving', {}).data if 'moving' in streams else [None] * len(time_data)
            grade_data = streams.get('grade_smooth', {}).data if 'grade_smooth' in streams else [None] * len(time_data)
            
            # Generate stream entries
            for i in range(len(time_data)):
                # Calculate timestamp
                timestamp = strava_activity.start_date + dt.timedelta(seconds=time_data[i])
                
                # Get lat/lng
                lat, lng = latlng_data[i] if latlng_data[i] else (None, None)
                
                stream_objects.append(
                    Stream(
                        id=uuid.uuid4(),
                        activity_id=new_activity.id,
                        timestamp=timestamp,
                        lat=lat,
                        lon=lng,
                        altitude=altitude_data[i] if i < len(altitude_data) else None,
                        distance=time_data[i] * (velocity_data[i] if i < len(velocity_data) and velocity_data[i] is not None else 0),
                        velocity_smooth=velocity_data[i] if i < len(velocity_data) else None,
                        heartrate=heartrate_data[i] if i < len(heartrate_data) else None,
                        cadence=cadence_data[i] if i < len(cadence_data) else None,
                        watts=watts_data[i] if i < len(watts_data) else None,
                        temp=temp_data[i] if i < len(temp_data) else None,
                        moving=moving_data[i] if i < len(moving_data) else None,
                        grade_smooth=grade_data[i] if i < len(grade_data) else None,
                    )
                )
            
            # Batch insert streams (more efficient for large datasets)
            if stream_objects:
                db.bulk_save_objects(stream_objects)
    except Exception as e:
        logger.error(f"Error fetching streams for activity {strava_activity_id}: {e}")
    
    # Commit changes
    db.commit()
    
    # Trigger analytics recalculation
    recalc_metrics_for_activity.delay(str(user.id), strava_activity_id)
    
    return new_activity.id


@celery.task
def sync_initial_activities(user_id: str, days_back: int = 30):
    """
    Synchronize a user's activities for the past X days
    """
    logger.info(f"Starting initial sync for user {user_id}, past {days_back} days")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        client = get_client(user_id=user_id)
        
        # Get activities from the past X days
        after_date = dt.datetime.now() - dt.timedelta(days=days_back)
        activities = client.get_activities(after=after_date)
        
        activity_count = 0
        for activity in activities:
            # Skip activities that aren't rides
            if activity.type != 'Ride':
                continue
                
            try:
                fetch_and_store_activity(db, user_id, activity.id)
                activity_count += 1
            except Exception as e:
                logger.error(f"Error syncing activity {activity.id}: {e}")
        
        logger.info(f"Completed initial sync for user {user_id}, synced {activity_count} activities")
        return activity_count
        
    except Exception as e:
        logger.error(f"Error in initial sync for user {user_id}: {e}")
        raise
    finally:
        db.close()