# AI-Bike-Coach FastAPI backend entrypoint
from fastapi import FastAPI
from .config import settings
from .strava.webhook import router as strava_webhook_router

app = FastAPI(title="AI-Bike-Coach API")

# Register Strava webhook endpoints
app.include_router(strava_webhook_router, prefix="/strava")

@app.get("/")
def root():
    return {"message": "AI-Bike-Coach API running"}

# TODO: Add more routers (auth, analytics, agent, etc.)
