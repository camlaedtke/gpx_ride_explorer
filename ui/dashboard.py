"""
dashboard.py
------------
Dashboard tab for the Streamlit UI of the AI-Bike-Coach platform.

Responsibilities:
- Display summary cards (distance, duration, TSS, CTL/ATL/TSB, PR count).
- Show CTL/ATL/TSB chart and PR list for the user.
- Serve as the main analytics overview for the athlete.

TODO:
- Implement summary cards with real data from the backend.
- Add CTL/ATL/TSB chart using Plotly or Altair.
- Display PR list and enable drill-down to rides.
"""

# dashboard.py: Dashboard tab with API health check
import streamlit as st
import requests
import pandas as pd
import json

def show():
    st.header("Dashboard")
    
    # API Health Check
    st.subheader("System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response = requests.get("http://api:8000/health", timeout=2)
            if response.status_code == 200:
                st.success("✅ API is running")
                st.json(response.json())
            else:
                st.error(f"❌ API returned status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot connect to API: {e}")
    
    with col2:
        try:
            response = requests.get("http://api:8000/", timeout=2)
            if response.status_code == 200:
                st.success("✅ API root endpoint is accessible")
                st.json(response.json())
            else:
                st.error(f"❌ API root endpoint returned status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot connect to API root: {e}")
    
    # Placeholder for future dashboard components
    st.subheader("Coming Soon")
    st.info("Summary cards, CTL chart, PR list coming soon!")
    
    # Mock data for demonstration
    st.subheader("Sample Activity Data")
    data = {
        "Date": ["2025-04-15", "2025-04-16", "2025-04-18", "2025-04-19"],
        "Activity": ["Morning Ride", "Evening Ride", "Hill Repeats", "Recovery Ride"],
        "Distance (km)": [25.3, 18.7, 42.1, 15.5],
        "Duration": ["1h 12m", "0h 48m", "2h 05m", "0h 45m"],
        "TSS": [65, 42, 95, 30]
    }
    st.dataframe(pd.DataFrame(data))
