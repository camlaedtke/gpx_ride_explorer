"""
ride_explorer.py
---------------
Ride Explorer tab for the Streamlit UI of the AI-Bike-Coach platform.

Responsibilities:
- Allow users to select and explore individual rides from the database.
- Display GPX map, ride details, and charts for the selected activity.
- Integrate with backend for activity and stream data.

TODO:
- Integrate GPX explorer component with DB-backed activity selection.
- Add map and chart visualizations for ride data.
- Enable drill-down to power, HR, and other metrics per ride.
"""
import streamlit as st
import requests
import pandas as pd
import os

def show():
    st.header("Ride Explorer")
    
    # API Health Check
    st.subheader("API Connection")
    try:
        response = requests.get("http://api:8000/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Connected to API")
        else:
            st.error(f"❌ API returned status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Cannot connect to API: {e}")
    
    # Sample GPX file selection
    st.subheader("Sample GPX Files")
    gpx_files = [f for f in os.listdir("/app/data") if f.endswith(".gpx")]
    
    if gpx_files:
        selected_file = st.selectbox("Select a GPX file to visualize:", gpx_files)
        st.info(f"Selected: {selected_file}")
        
        # Placeholder for map visualization
        st.subheader("Map View")
        st.info("GPX map visualization will appear here in future versions.")
        
        # Placeholder for metrics
        st.subheader("Ride Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Distance", "42.5 km")
        with col2:
            st.metric("Elevation", "756 m")
        with col3:
            st.metric("Duration", "2h 15m")
            
        # Placeholder for power/heart rate chart
        st.subheader("Power & Heart Rate")
        st.info("Power and heart rate charts will appear here in future versions.")
    else:
        st.warning("No GPX files found in the data directory. Sample files will be available in future versions.")
