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
import requests
from app.config import settings

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
    
    # Check if activity already exists
    existing = db.query(Activity).filter(Activity.strava_id == strava_activity_id).first()
    if existing:
        logger.info(f"Activity {strava_activity_id} already exists, skipping")
        return existing.id
    
    # Use direct API calls instead of stravalib for more reliable authentication
    headers = {"Authorization": f"Bearer {user.access_token}"}
    
    # Get activity details
    activity_url = f"https://www.strava.com/api/v3/activities/{strava_activity_id}"
    response = requests.get(activity_url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Error fetching activity {strava_activity_id}: {response.text}")
        raise Exception(f"Failed to fetch activity: {response.text}")
        
    strava_activity = response.json()
    
    # Create new activity from the API response
    new_activity = Activity(
        id=uuid.uuid4(),
        user_id=user.id,
        strava_id=strava_activity_id,
        name=strava_activity['name'],
        start_time=dt.datetime.fromisoformat(strava_activity['start_date']),
        distance_m=float(strava_activity['distance']),
        moving_time_s=strava_activity['moving_time'],
        elev_gain_m=float(strava_activity['total_elevation_gain']) if strava_activity.get('total_elevation_gain') else None,
        avg_power=float(strava_activity['average_watts']) if strava_activity.get('average_watts') else None,
        avg_hr=float(strava_activity['average_heartrate']) if strava_activity.get('average_heartrate') else None,
    )
    
    db.add(new_activity)
    db.flush()  # Get ID without committing
    
    # Get streams data
    try:
        streams_url = f"https://www.strava.com/api/v3/activities/{strava_activity_id}/streams"
        params = {
            'keys': 'time,latlng,altitude,heartrate,watts,cadence,velocity_smooth,temp,moving,grade_smooth',
            'key_by_type': True
        }
        
        streams_response = requests.get(streams_url, headers=headers, params=params)
        
        if streams_response.status_code == 200:
            streams = streams_response.json()
            
            # Process each stream type
            if streams:
                # Create stream entries
                stream_objects = []
                
                # Get the time stream which is required
                if 'time' in streams and 'latlng' in streams:
                    time_data = streams['time']['data']
                    latlng_data = streams['latlng']['data']
                    
                    # Optional streams
                    altitude_data = streams['altitude']['data'] if 'altitude' in streams else [None] * len(time_data)
                    heartrate_data = streams['heartrate']['data'] if 'heartrate' in streams else [None] * len(time_data)
                    watts_data = streams['watts']['data'] if 'watts' in streams else [None] * len(time_data)
                    cadence_data = streams['cadence']['data'] if 'cadence' in streams else [None] * len(time_data)
                    velocity_data = streams['velocity_smooth']['data'] if 'velocity_smooth' in streams else [None] * len(time_data)
                    temp_data = streams['temp']['data'] if 'temp' in streams else [None] * len(time_data)
                    moving_data = streams['moving']['data'] if 'moving' in streams else [None] * len(time_data)
                    grade_data = streams['grade_smooth']['data'] if 'grade_smooth' in streams else [None] * len(time_data)
                    
                    # Calculate start time
                    start_time = dt.datetime.fromisoformat(strava_activity['start_date'])
                    
                    # Generate stream entries
                    for i in range(len(time_data)):
                        # Calculate timestamp
                        timestamp = start_time + dt.timedelta(seconds=time_data[i])
                        
                        # Get lat/lng
                        lat, lng = latlng_data[i] if i < len(latlng_data) and latlng_data[i] else (None, None)
                        
                        # Convert moving boolean to integer (0/1)
                        moving_int = 1 if moving_data and i < len(moving_data) and moving_data[i] else 0
                        
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
                                moving=moving_int,  # Use the integer value instead of boolean
                                grade_smooth=grade_data[i] if i < len(grade_data) else None,
                            )
                        )
                    
                    # Batch insert streams (more efficient for large datasets)
                    if stream_objects:
                        db.bulk_save_objects(stream_objects)
        else:
            logger.warning(f"Could not fetch streams: {streams_response.status_code} - {streams_response.text}")
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
        
        # Using a more direct way to get activities with proper authentication
        # First, ensure we have a valid token by checking and refreshing if needed
        if user.token_expires_at and user.token_expires_at <= dt.datetime.now() + dt.timedelta(minutes=5):
            logger.info(f"Token for user {user_id} is expired or will expire soon, refreshing...")
            
            # Refresh the token using the Strava API directly
            refresh_url = "https://www.strava.com/oauth/token"
            refresh_data = {
                'client_id': settings.STRAVA_CLIENT_ID,
                'client_secret': settings.STRAVA_CLIENT_SECRET,
                'refresh_token': user.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            refresh_response = requests.post(refresh_url, data=refresh_data)
            if refresh_response.status_code != 200:
                logger.error(f"Failed to refresh token: {refresh_response.text}")
                raise ValueError(f"Failed to refresh Strava token: {refresh_response.text}")
            
            token_data = refresh_response.json()
            user.access_token = token_data['access_token']
            user.refresh_token = token_data['refresh_token']
            user.token_expires_at = dt.datetime.fromtimestamp(token_data['expires_at'])
            db.commit()
            logger.info(f"Successfully refreshed token for user {user_id}")
        
        # Now get activities with the valid token
        after_date = dt.datetime.now() - dt.timedelta(days=days_back)
        after_timestamp = int(after_date.timestamp())
        
        # Use direct API call instead of stravalib to have more control
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {user.access_token}"}
        
        # Strava paginates results, so we may need multiple requests
        page = 1
        per_page = 50
        all_activities = []
        
        while True:
            params = {
                'after': after_timestamp,
                'page': page,
                'per_page': per_page
            }
            
            response = requests.get(activities_url, headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to get activities: {response.text}")
                raise ValueError(f"Failed to get Strava activities: {response.text}")
            
            activities_page = response.json()
            all_activities.extend(activities_page)
            
            # Break if we got fewer results than requested (last page)
            if len(activities_page) < per_page:
                break
            
            page += 1
        
        activity_count = 0
        for activity in all_activities:
            # Skip activities that aren't rides
            if activity['type'] != 'Ride':
                continue
            
            try:
                activity_id = activity['id']
                fetch_and_store_activity(db, user_id, activity_id)
                activity_count += 1
            except Exception as e:
                logger.error(f"Error syncing activity {activity['id']}: {e}")
        
        logger.info(f"Completed initial sync for user {user_id}, synced {activity_count} activities")
        return activity_count
        
    except Exception as e:
        logger.error(f"Error in initial sync for user {user_id}: {e}")
        raise
    finally:
        db.close()