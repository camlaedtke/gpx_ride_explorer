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
from datetime import datetime, timezone

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
    
    # Webhook Status Section
    st.subheader("Strava Webhook Status")
    
    # Try to fetch webhook subscriptions
    try:
        # Get User Info (to get the Strava Athlete ID)
        user_response = requests.get("http://api:8000/auth/user-info", timeout=2)
        
        if user_response.status_code == 200:
            user_info = user_response.json()
            strava_athlete_id = user_info.get('strava_athlete_id')
            
            st.info(f"Connected Strava account: Athlete ID {strava_athlete_id}")
            
            # Webhook test form
            with st.expander("Test Webhook", expanded=False):
                st.write("Simulate a Strava webhook event for testing")
                
                # Form to test the webhook
                with st.form("webhook_test_form"):
                    activity_id = st.number_input("Strava Activity ID", min_value=1, value=12345678)
                    submitted = st.form_submit_button("Simulate Event")
                    
                    if submitted:
                        try:
                            payload = {
                                "strava_activity_id": int(activity_id),
                                "strava_athlete_id": strava_athlete_id
                            }
                            webhook_response = requests.post(
                                "http://api:8000/strava/webhook-test", 
                                json=payload,
                                timeout=5
                            )
                            
                            if webhook_response.status_code == 200:
                                result = webhook_response.json()
                                st.success(f"✅ {result.get('message', 'Event processed!')}")
                                st.code(json.dumps(result, indent=2))
                            else:
                                st.error(f"❌ Failed to process webhook test: {webhook_response.status_code}")
                                st.code(webhook_response.text)
                        except Exception as e:
                            st.error(f"❌ Error testing webhook: {str(e)}")
        else:
            st.warning("⚠️ Not connected to Strava. Please log in first.")
    except Exception as e:
        st.error(f"❌ Error checking webhook status: {str(e)}")
    
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
