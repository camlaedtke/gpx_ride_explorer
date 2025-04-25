"""
ride_explorer.py
---------------
Ride Explorer tab for the Streamlit UI of the AI-Bike-Coach platform.

Responsibilities:
- Allow users to select and explore individual rides from the database.
- Display GPX map, ride details, and charts for the selected activity.
- Integrate with backend for activity and stream data.

TODO:
- Add map and chart visualizations for ride data.
- Enable drill-down to power, HR, and other metrics per ride.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

def show():
    st.header("Ride Explorer")
    
    # API Health Check
    st.subheader("API Connection")
    try:
        response = requests.get("http://api:8000/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Connected to API")
            api_healthy = True
        else:
            st.error(f"❌ API returned status code {response.status_code}")
            api_healthy = False
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Cannot connect to API: {e}")
        api_healthy = False
    
    if not api_healthy:
        st.warning("Cannot fetch activities from the database. Please ensure the API is running properly.")
        return
    
    # Fetch activities from the API
    st.subheader("Your Activities")
    
    try:
        # In a real app, we would need user authentication here
        # For now, we'll just fetch all activities
        response = requests.get("http://api:8000/activities", timeout=5)
        
        if response.status_code == 200:
            activities = response.json()
            
            if not activities:
                st.info("No activities found in the database. Try syncing with Strava first!")
                return
                
            # Convert to DataFrame for display
            activities_df = pd.DataFrame([
                {
                    'id': a['id'],
                    'name': a['name'],
                    'date': datetime.fromisoformat(a['start_time']).strftime('%Y-%m-%d'),
                    'distance': f"{a['distance_m']/1000:.1f} km",
                    'duration': str(timedelta(seconds=int(a['moving_time_s']))) if a['moving_time_s'] else "N/A",
                    'elevation': f"{a['elev_gain_m']:.0f} m" if a['elev_gain_m'] else "N/A",
                    'avg_power': f"{a['avg_power']:.0f} W" if a['avg_power'] else "N/A",
                    'avg_hr': f"{a['avg_hr']:.0f} bpm" if a['avg_hr'] else "N/A",
                    'raw_data': a
                }
                for a in activities
            ])
            
            # Display activities list
            st.dataframe(
                activities_df[['name', 'date', 'distance', 'duration', 'elevation', 'avg_power', 'avg_hr']],
                use_container_width=True
            )
            
            # Select an activity to explore in detail
            selected_activity_id = st.selectbox(
                "Select an activity to view details:", 
                options=activities_df['id'].tolist(),
                format_func=lambda x: f"{activities_df[activities_df['id']==x]['name'].values[0]} ({activities_df[activities_df['id']==x]['date'].values[0]})"
            )
            
            if selected_activity_id:
                selected_activity = activities_df[activities_df['id'] == selected_activity_id]['raw_data'].values[0]
                
                st.subheader(f"Activity Details: {selected_activity['name']}")
                
                # Display activity metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Distance", f"{selected_activity['distance_m']/1000:.1f} km")
                with col2:
                    if selected_activity['elev_gain_m']:
                        st.metric("Elevation", f"{selected_activity['elev_gain_m']:.0f} m")
                    else:
                        st.metric("Elevation", "N/A")
                with col3:
                    if selected_activity['moving_time_s']:
                        st.metric("Duration", str(timedelta(seconds=int(selected_activity['moving_time_s']))))
                    else:
                        st.metric("Duration", "N/A")
                with col4:
                    if selected_activity['avg_power']:
                        st.metric("Avg Power", f"{selected_activity['avg_power']:.0f} W")
                    else:
                        st.metric("Avg Power", "N/A")
                
                # Fetch stream data for the selected activity
                try:
                    stream_response = requests.get(f"http://api:8000/activities/{selected_activity_id}/streams", timeout=5)
                    
                    if stream_response.status_code == 200:
                        streams = stream_response.json()
                        
                        if streams:
                            # Convert stream data for visualization
                            stream_df = pd.DataFrame(streams)
                            
                            # Map visualization
                            st.subheader("Route Map")
                            
                            # Check if lat/lon data is available
                            if 'lat' in stream_df.columns and 'lon' in stream_df.columns and not stream_df['lat'].isna().all():
                                fig = px.scatter_mapbox(
                                    stream_df, 
                                    lat="lat", 
                                    lon="lon", 
                                    zoom=11,
                                    color="watts" if "watts" in stream_df.columns and not stream_df['watts'].isna().all() else None,
                                    hover_data={
                                        "altitude": True if "altitude" in stream_df.columns else False,
                                        "heartrate": True if "heartrate" in stream_df.columns else False,
                                        "watts": True if "watts" in stream_df.columns else False
                                    },
                                    mapbox_style="open-street-map"
                                )
                                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No GPS data available to display the route map.")
                            
                            # Power and HR charts
                            st.subheader("Power & Heart Rate")
                            
                            # Create a time axis in minutes
                            if 'timestamp' in stream_df.columns:
                                stream_df['time_mins'] = (pd.to_datetime(stream_df['timestamp']) - pd.to_datetime(stream_df['timestamp'].iloc[0])).dt.total_seconds() / 60
                                
                                fig = go.Figure()
                                
                                # Add power data if available
                                if 'watts' in stream_df.columns and not stream_df['watts'].isna().all():
                                    fig.add_trace(go.Scatter(
                                        x=stream_df['time_mins'], 
                                        y=stream_df['watts'],
                                        mode='lines',
                                        name='Power (watts)',
                                        line=dict(color='orange')
                                    ))
                                
                                # Add heart rate data if available
                                if 'heartrate' in stream_df.columns and not stream_df['heartrate'].isna().all():
                                    fig.add_trace(go.Scatter(
                                        x=stream_df['time_mins'], 
                                        y=stream_df['heartrate'],
                                        mode='lines',
                                        name='Heart Rate (bpm)',
                                        line=dict(color='red')
                                    ))
                                
                                if 'watts' in stream_df.columns or 'heartrate' in stream_df.columns:
                                    fig.update_layout(
                                        xaxis_title='Time (minutes)',
                                        yaxis_title='Value',
                                        height=400,
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("No power or heart rate data available for this activity.")
                            else:
                                st.info("No time series data available to create charts.")
                        else:
                            st.info("No stream data available for this activity.")
                    else:
                        st.warning(f"Could not fetch stream data: {stream_response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching stream data: {e}")
                    
        else:
            st.warning(f"Could not fetch activities: {response.status_code}")
            if response.status_code == 404:
                st.info("The activities endpoint might not be implemented yet.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {e}")
