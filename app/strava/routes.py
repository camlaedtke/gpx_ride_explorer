"""
routes.py
---------
Strava OAuth authentication routes for the AI-Bike-Coach backend.

Responsibilities:
- Provide FastAPI routes for Strava OAuth login and callback.
- Handle OAuth token exchange and user creation/update.
- Store Strava tokens in the database for use by the sync and webhook handlers.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import datetime as dt
import uuid
import requests
import json

from app.db.session import SessionLocal
from app.db.models import User
from app.config import settings
from app.strava.client import get_client

router = APIRouter()

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/login")
async def strava_login(request: Request):
    """
    Initiates the Strava OAuth flow by redirecting to Strava's authorization page.
    """
    client = get_client()
    # Make sure to use the complete URL for the callback
    redirect_uri = f"{request.base_url.scheme}://{request.base_url.netloc}/auth/callback"
    
    authorize_url = client.authorization_url(
        client_id=settings.STRAVA_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope=['read', 'activity:read_all', 'profile:read_all']
    )
    
    return RedirectResponse(authorize_url)

@router.get("/callback")
async def strava_callback(
    code: str, 
    scope: str = None, 
    db: Session = Depends(get_db)
):
    """
    Handles the Strava OAuth callback, exchanges the authorization code for tokens,
    and creates or updates the user in the database.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    try:
        # Use the Strava Token Exchange API directly to avoid any issues with stravalib
        token_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': settings.STRAVA_CLIENT_ID,
            'client_secret': settings.STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Token exchange failed: {response.text}"
            )
        
        token_data = response.json()
        
        # Extract token data
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_at = dt.datetime.fromtimestamp(token_data['expires_at'])
        
        # Extract athlete data directly from the response
        athlete_data = token_data.get('athlete', {})
        strava_athlete_id = athlete_data.get('id')
        
        if not strava_athlete_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve athlete ID from Strava")
        
        # Check if user exists and update, or create new user
        user = db.query(User).filter(User.strava_athlete_id == strava_athlete_id).first()
        
        if user:
            # Update existing user
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expires_at = expires_at
        else:
            # Create new user
            user = User(
                id=uuid.uuid4(),
                strava_athlete_id=strava_athlete_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at
            )
            db.add(user)
        
        db.commit()
        
        # Redirect to a success page or the main app
        return RedirectResponse(url="/auth/success")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")

@router.get("/success")
async def auth_success():
    """
    Simple success page confirming successful authentication.
    """
    return {"message": "Successfully authenticated with Strava!"}