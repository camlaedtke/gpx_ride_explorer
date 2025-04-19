from pydantic import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    STRAVA_CLIENT_ID: str
    STRAVA_CLIENT_SECRET: str
    OPENAI_API_KEY: str
    REDIS_URL: str = "redis://redis:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()
