# Placeholder for Streamlit UI multipage app
import streamlit as st
from ui import dashboard, ride_explorer

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
