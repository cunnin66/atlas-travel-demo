import streamlit as st
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.navigation import check_authentication, render_navigation

def show():
    """Display the destinations page"""
    
    # Check authentication - redirect to login if not authenticated
    if not check_authentication():
        return

    # Render navigation bar
    render_navigation()

    # Hero section
    st.markdown("## Where to?")
    st.markdown("---")

    # Mock destinations data (replace with actual data later)
    destinations = [
        {"name": "Paris, France", "image": "🇫🇷", "description": "City of Light"},
        {"name": "Tokyo, Japan", "image": "🇯🇵", "description": "Modern metropolis"},
        {"name": "New York, USA", "image": "🇺🇸", "description": "The Big Apple"},
        {"name": "Bali, Indonesia", "image": "🇮🇩", "description": "Tropical paradise"},
        {"name": "Rome, Italy", "image": "🇮🇹", "description": "Eternal City"},
        {"name": "Sydney, Australia", "image": "🇦🇺", "description": "Harbor city"},
    ]

    # Create destination grid
    cols_per_row = 3
    rows = (len(destinations) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            dest_idx = row * cols_per_row + col_idx
            if dest_idx < len(destinations):
                dest = destinations[dest_idx]
                with cols[col_idx]:
                    with st.container(border=True):
                        st.markdown(f"### {dest['image']} {dest['name']}")
                        st.markdown(dest['description'])
                        
                        button_cols = st.columns(2)
                        with button_cols[0]:
                            if st.button("🗺️ Plan", key=f"plan_{dest_idx}"):
                                st.session_state.selected_destination = dest['name']
                                st.session_state.current_page = "planner"
                                st.rerun()
                        with button_cols[1]:
                            if st.button("✏️ Edit", key=f"edit_{dest_idx}"):
                                st.session_state.edit_destination = dest['name']
                                # TODO: Implement edit functionality
                                st.info(f"Edit functionality for {dest['name']} coming soon!")

    # Add destination button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("➕ Add New Destination", key="add_destination"):
            # TODO: Implement add destination functionality
            st.info("Add destination functionality coming soon!")
