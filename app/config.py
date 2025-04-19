"""
config.py
---------
Configuration module for the AI-Bike-Coach backend.

Responsibilities:
- Define the Settings class using Pydantic BaseSettings for environment-based configuration.
- Load sensitive credentials and connection strings (database, Redis, Strava, OpenAI, etc.) from environment variables or .env file.
- Provide a singleton instance (settings) for use throughout the app.

TODO:
- Add validation for required fields and custom error messages.
- Add support for additional configuration options as new features are added.
- Consider splitting secrets and non-secrets if security requirements increase.
"""

from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_ANON_KEY: str
    STRAVA_CLIENT_ID: str
    STRAVA_CLIENT_SECRET: str
    OPENAI_API_KEY: str
    REDIS_URL: str = "redis://redis:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()
