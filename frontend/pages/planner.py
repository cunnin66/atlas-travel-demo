import os
import sys

import streamlit as st

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.navigation import check_authentication, render_navigation


def show():
    """Display the planner page"""

    # Check authentication - redirect to login if not authenticated
    if not check_authentication():
        return

    # Render navigation bar
    render_navigation()

    st.title("🗺️ Plan Your Trip")

    # Check if a destination was selected from home page
    if "selected_destination" in st.session_state:
        st.success(f"Planning trip to: {st.session_state.selected_destination}")

    st.write("TODO: Build this page.")

    st.markdown(
        """
    This is the main AI planning interface where you can:
    - Input your travel preferences and requirements
    - Chat with the AI travel agent
    - Generate personalized itineraries
    - Modify and refine travel plans
    - Export itineraries
    - Real-time streaming responses from the AI agent
    """
    )
