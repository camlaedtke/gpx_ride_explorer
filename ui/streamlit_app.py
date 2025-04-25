"""
streamlit_app.py
---------------
Main entrypoint for the Streamlit UI of the AI-Bike-Coach platform.

Responsibilities:
- Provide sidebar navigation for Dashboard, Ride Explorer, and Chat tabs.
- Route to the appropriate UI module based on user selection.
- Initialize Streamlit app configuration.

TODO:
- Integrate chat agent for the Chat tab.
- Add user authentication/session state.
- Improve navigation and add more UI features as backend matures.
"""

# Placeholder for Streamlit UI multipage app
import streamlit as st
# Modified import statement for better compatibility within Docker container
import dashboard, ride_explorer

st.set_page_config(page_title="AI-Bike-Coach", layout="wide")

st.sidebar.title("AI-Bike-Coach")
page = st.sidebar.radio("Navigation", ["Dashboard", "Ride Explorer", "Chat"])

if page == "Dashboard":
    dashboard.show()
elif page == "Ride Explorer":
    ride_explorer.show()
else:
    st.header("Chat")
    st.write("Chat with your AI Bike Coach!")
    # TODO: Integrate chat agent
