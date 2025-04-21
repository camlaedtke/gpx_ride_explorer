"""
pmc.py
------
Performance Management Chart (PMC) analytics for the AI-Bike-Coach platform.

Responsibilities:
- Calculate CTL (Chronic Training Load), ATL (Acute Training Load), and TSB (Training Stress Balance) from activity data.
- Provide functions for updating and recalculating user metrics after new rides.
- Used by Celery tasks and the dashboard UI.

TODO:
- Add more analytics (e.g., MMP, PR detection) as needed.
- Optimize for large user/activity datasets.
"""

import numpy as np
import pandas as pd
from celery import Celery
from app.db.session import SessionLocal
from app.db.models import Activity, User

celery = Celery(__name__, broker="redis://redis:6379/0")

def calc_ctl_atl(tss_series: pd.Series, tau:int):
    # simple EWMA implementation
    return tss_series.ewm(alpha=1/tau, adjust=False).mean()

@celery.task
def recalc_metrics_for_activity(user_id:str, strava_activity_id:int):
    """
    Rebuild CTL/ATL/TSB for the user of this activity.
    Called after new ride ingested.
    """
    db = SessionLocal()
    try:
        # This is a stub implementation for Phase 0.1
        # In future phases, we'll:
        # 1. Pull all activities with date and TSS for the user
        # 2. Compute CTL/ATL/TSB
        # 3. Write back to a daily snapshot table
        print(f"Recalculating metrics for user {user_id}, activity {strava_activity_id}")
    finally:
        db.close()