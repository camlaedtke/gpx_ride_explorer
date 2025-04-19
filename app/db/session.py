"""
session.py
----------
SQLAlchemy session and engine setup for the AI-Bike-Coach backend.

Responsibilities:
- Create SQLAlchemy engine using app settings (DATABASE_URL).
- Provide SessionLocal factory for DB sessions throughout the app.
- Used by all modules requiring DB access (analytics, Strava sync, agent, etc.).

TODO:
- Add connection pool tuning as needed for production.
- Add support for async sessions if required.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)