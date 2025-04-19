# strava/client.py: Strava API client wrapper
from urllib.parse import urlencode
from app.config import settings

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"

class StravaClient:
    def get_authorize_url(self, scope=["activity:read_all"]):
        params = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": "http://localhost:8000/strava/auth/redirect",  # TODO: Make configurable
            "approval_prompt": "auto",
            "scope": ",".join(scope),
        }
        return f"{STRAVA_AUTHORIZE_URL}?{urlencode(params)}"

    # TODO: Add methods for token refresh, activity fetch, etc.

strava_client = StravaClient()
