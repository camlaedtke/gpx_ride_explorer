"""
main.py
--------
Entrypoint for the AI-Bike-Coach FastAPI backend application.

Responsibilities:
- Initialize the FastAPI app instance.
- Register API routers (e.g., Strava webhook, authentication, analytics, agent, etc.).
- Provide a root endpoint for health/status checks.

TODO:
- Add routers for authentication, analytics, agent, and other modules as they are implemented.
- Implement global exception handlers and middleware if needed.
- Add OpenAPI/Swagger customization if required.
- Integrate logging and monitoring.
"""

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
