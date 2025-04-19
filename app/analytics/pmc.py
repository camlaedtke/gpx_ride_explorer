"""
pmc.py
------
Performance Management Chart (PMC) analytics for the AI-Bike-Coach platform.

Responsibilities:
- Calculate CTL (Chronic Training Load), ATL (Acute Training Load), and TSB (Training Stress Balance) from activity data.
- Provide functions for updating and recalculating user metrics after new rides.
- Used by Celery tasks and the dashboard UI.

TODO:
- Complete recalc_metrics_for_activity to update daily metrics in the database.
- Add more analytics (e.g., MMP, PR detection) as needed.
- Optimize for large user/activity datasets.
"""

import numpy as np
import pandas as pd
from app.db.session import SessionLocal
from app.db.models import Activity

def calc_ctl_atl(tss_series: pd.Series, tau:int):
    # simple EWMA implementation
    return tss_series.ewm(alpha=1/tau, adjust=False).mean()

def recalc_metrics_for_activity(activity_id:str):
    """
    Rebuild CTL/ATL/TSB for the user of this activity.
    Called after new ride ingested.
    """
    db = SessionLocal()
    # pull all activities with date, tss
    # compute ctl/atl, write back daily snapshot table