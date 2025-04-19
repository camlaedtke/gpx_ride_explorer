# db/models.py: SQLAlchemy models and TimescaleDB hypertable
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    strava_id = Column(Integer, unique=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(Integer)
    # TODO: Add more user fields as needed

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    strava_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    start_date = Column(DateTime)
    distance = Column(Float)
    moving_time = Column(Integer)
    elapsed_time = Column(Integer)
    tss = Column(Float)
    # TODO: Add more activity fields as needed
    user = relationship("User", back_populates="activities")

User.activities = relationship("Activity", order_by=Activity.id, back_populates="user")

# Streams hypertable (TimescaleDB): raw SQL migration required
# Example Alembic migration snippet:
# op.execute('''
# CREATE TABLE streams (
#     id SERIAL PRIMARY KEY,
#     activity_id INTEGER REFERENCES activities(id),
#     type TEXT,
#     data JSONB,
#     time TIMESTAMPTZ
# );
# SELECT create_hypertable('streams', 'time', if_not_exists => TRUE);
# ''')

# class Stream(Base):
#     __tablename__ = "streams"
#     id = Column(Integer, primary_key=True)
#     activity_id = Column(Integer, ForeignKey("activities.id"))
#     type = Column(String)
#     data = Column(JSON)
#     time = Column(DateTime)
#     # This table should be a TimescaleDB hypertable (see migration above)

# TODO: Add PRRecord model for personal records
