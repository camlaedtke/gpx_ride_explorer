"""
models.py
---------
SQLAlchemy ORM models for the AI-Bike-Coach backend database.

Responsibilities:
- Define database tables and relationships for users, activities, and streams.
- Provide ORM mapping for use in queries and business logic.
- Support hypertable/time-series features (e.g., TimescaleDB) for activity streams.

TODO:
- Complete the Stream and PRRecord models.
- Add SQLAlchemy relationships (User.activities, Activity.streams, etc.).
- Write Alembic migration scripts for all tables and hypertables.
- Add model-level validation and utility methods as needed.
- Document each model class and its fields.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, \
    ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid, datetime as dt

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    strava_athlete_id = Column(Integer, unique=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    strava_id = Column(BigInteger, unique=True, index=True)
    name = Column(String)
    start_time = Column(DateTime)
    distance_m = Column(Float)
    moving_time_s = Column(Integer)
    elev_gain_m = Column(Float)
    avg_power = Column(Float)
    avg_hr = Column(Float)
    tss = Column(Float)
    np = Column(Float)
    # relationships …