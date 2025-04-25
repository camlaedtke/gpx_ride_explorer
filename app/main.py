"""
main.py
--------
Entrypoint for the AI-Bike-Coach FastAPI backend application.

Responsibilities:
- Initialize the FastAPI app instance.
- Register API routers (e.g., Strava webhook, authentication, analytics, agent, etc.).
- Provide a root endpoint for health/status checks.

TODO:
- Add routers for analytics, agent, and other modules as they are implemented.
- Implement global exception handlers and middleware if needed.
- Add OpenAPI/Swagger customization if required.
- Integrate logging and monitoring.
"""

# AI-Bike-Coach FastAPI backend entrypoint
from fastapi import FastAPI
from .config import settings
from .strava.webhook import router as strava_webhook_router
from .strava.routes import router as strava_auth_router
from .strava.sync_routes import router as strava_sync_router
from .strava.activities import router as activities_router
from .db.session import engine
from .db import models

app = FastAPI(title="AI-Bike-Coach API")

# Register Strava webhook endpoints
app.include_router(strava_webhook_router, prefix="/strava")

# Register Strava auth endpoints
app.include_router(strava_auth_router, prefix="/auth")

# Register Strava sync endpoints
app.include_router(strava_sync_router, prefix="/sync")

# Register activities endpoints
app.include_router(activities_router)

@app.get("/")
def root():
    return {"message": "AI-Bike-Coach API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Create DB tables on startup if they don't exist
models.Base.metadata.create_all(bind=engine)

# TODO: Add more routers (analytics, agent, etc.)
