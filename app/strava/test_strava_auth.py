"""
test_strava_auth.py
------------------
A simple script to test Strava API authentication and basic API access.
This will help diagnose issues with the Strava API integration.
"""

import requests
import datetime as dt
from app.config import settings
from app.db.session import SessionLocal
from app.db.models import User
import logging
import json
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_strava_auth():
    """
    Test Strava authentication and basic API access.
    This will:
    1. Get the latest user from the database
    2. Check their token
    3. Refresh the token if needed
    4. Try to fetch athlete information
    5. Try to list a few activities
    """
    logger.info("Starting Strava API authentication test")
    
    # Connect to the database
    db = SessionLocal()
    try:
        # Get the most recently authenticated user
        user = db.query(User).order_by(User.token_expires_at.desc()).first()
        
        if not user:
            logger.error("No authenticated users found in the database")
            return False
        
        logger.info(f"Found user with ID: {user.id}")
        logger.info(f"Strava athlete ID: {user.strava_athlete_id}")
        logger.info(f"Token expires at: {user.token_expires_at}")
        
        # Check if token needs refreshing
        if user.token_expires_at and user.token_expires_at <= dt.datetime.now() + dt.timedelta(minutes=5):
            logger.info("Token is expired or will expire soon, refreshing...")
            
            refresh_url = "https://www.strava.com/oauth/token"
            refresh_data = {
                'client_id': settings.STRAVA_CLIENT_ID,
                'client_secret': settings.STRAVA_CLIENT_SECRET,
                'refresh_token': user.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            logger.info(f"Client ID: {settings.STRAVA_CLIENT_ID}")
            # Do not log the full client secret, just show if it's present
            logger.info(f"Client Secret is set: {'Yes' if settings.STRAVA_CLIENT_SECRET else 'No'}")
            # Show a few characters of refresh token for verification
            if user.refresh_token:
                masked_token = user.refresh_token[:4] + "..." + user.refresh_token[-4:]
                logger.info(f"Refresh token: {masked_token}")
            else:
                logger.error("Refresh token is missing")
                return False
                
            refresh_response = requests.post(refresh_url, data=refresh_data)
            
            if refresh_response.status_code != 200:
                logger.error(f"Failed to refresh token: {refresh_response.status_code}")
                logger.error(f"Response: {refresh_response.text}")
                return False
            
            token_data = refresh_response.json()
            user.access_token = token_data['access_token']
            user.refresh_token = token_data['refresh_token']
            user.token_expires_at = dt.datetime.fromtimestamp(token_data['expires_at'])
            db.commit()
            logger.info("Successfully refreshed token")
        else:
            logger.info("Token is still valid, no refresh needed")
        
        # Try to get athlete information
        logger.info("Testing API access - fetching athlete information")
        athlete_url = "https://www.strava.com/api/v3/athlete"
        headers = {"Authorization": f"Bearer {user.access_token}"}
        
        athlete_response = requests.get(athlete_url, headers=headers)
        
        if athlete_response.status_code != 200:
            logger.error(f"Failed to get athlete info: {athlete_response.status_code}")
            logger.error(f"Response: {athlete_response.text}")
            return False
        
        athlete_data = athlete_response.json()
        logger.info(f"Successfully fetched athlete info for: {athlete_data.get('firstname')} {athlete_data.get('lastname')}")
        
        # Try to list some activities
        logger.info("Testing API access - listing recent activities")
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        params = {
            'per_page': 3,  # Just get a few activities
            'page': 1
        }
        
        activities_response = requests.get(activities_url, headers=headers, params=params)
        
        if activities_response.status_code != 200:
            logger.error(f"Failed to get activities: {activities_response.status_code}")
            logger.error(f"Response: {activities_response.text}")
            return False
        
        activities_data = activities_response.json()
        logger.info(f"Successfully fetched {len(activities_data)} activities")
        
        # Print activity details
        for activity in activities_data:
            logger.info(f"Activity: {activity.get('name')} - {activity.get('type')} - {activity.get('id')}")
        
        logger.info("Strava API authentication test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_strava_auth()
    sys.exit(0 if success else 1)