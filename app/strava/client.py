"""
client.py
---------
Strava API client wrapper for the AI-Bike-Coach backend.

Responsibilities:
- Provide a configured stravalib Client instance for Strava API calls.
- Handle access token assignment and client credentials.
- Used by Strava sync tasks and webhook handlers.

TODO:
- Add automatic token refresh logic.
- Add error handling for API failures.
- Support additional Strava endpoints as needed.
"""

from stravalib import Client
from app.config import settings

def get_client(access_token:str|None=None):
    client = Client()
    if access_token:
        client.token = access_token
    client.client_id = settings.STRAVA_CLIENT_ID
    client.client_secret = settings.STRAVA_CLIENT_SECRET
    return client
