"""
client.py
---------
Strava API client wrapper for the AI-Bike-Coach backend.

Responsibilities:
- Provide a configured stravalib Client instance for Strava API calls.
- Handle access token assignment and client credentials.
- Used by Strava sync tasks and webhook handlers.
- Refresh tokens automatically when they expire.
"""

from stravalib import Client
from app.config import settings
from app.db.session import SessionLocal
from app.db.models import User
import datetime as dt

def get_client(access_token:str|None=None, user_id:str|None=None):
    """
    Returns a configured Strava client instance.
    
    If access_token is provided, uses it directly.
    If user_id is provided, fetches (and refreshes if needed) the token for that user.
    Otherwise, returns a client without an access token (can only be used for authorization).
    """
    client = Client()
    client.client_id = settings.STRAVA_CLIENT_ID
    client.client_secret = settings.STRAVA_CLIENT_SECRET
    
    if access_token:
        client.token = access_token
        return client
    
    if user_id:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Check if token needs to be refreshed
            if user.token_expires_at and user.token_expires_at <= dt.datetime.now() + dt.timedelta(minutes=5):
                # Token is expired or will expire soon, refresh it
                refresh_response = client.refresh_access_token(
                    client_id=settings.STRAVA_CLIENT_ID,
                    client_secret=settings.STRAVA_CLIENT_SECRET,
                    refresh_token=user.refresh_token
                )
                
                # Update user with new tokens
                user.access_token = refresh_response['access_token']
                user.refresh_token = refresh_response['refresh_token']
                user.token_expires_at = dt.datetime.fromtimestamp(refresh_response['expires_at'])
                db.commit()
            
            # Set the access token on the client
            client.token = user.access_token
    
    return client
