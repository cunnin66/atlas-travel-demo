import os
import sys

import streamlit as st
from components.destination_modal import add_destination
from components.menu import menu_with_redirect
from utils import request_with_auth


def get_destinations():
    """Get destinations"""
    response = request_with_auth("GET", "/destinations")
    if response.status_code == 200:
        return response.json()
    else:
        return []


menu_with_redirect()
st.markdown("## Where to?")

destinations = get_destinations()

if not destinations:
    with st.container(border=True):
        st.markdown(
            "No destinations found. Please add your first destination below to get started."
        )

else:
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
                    with st.container(border=True, height="stretch"):
                        st.markdown(f"### {dest['name']}")
                        with st.container(height="stretch"):
                            st.markdown(
                                dest["description"] or "No description provided"
                            )

                        button_cols = st.columns(2)
                        with button_cols[0]:
                            if st.button(
                                "Plan",
                                key=f"plan_{dest_idx}",
                                width="stretch",
                                type="primary",
                            ):
                                st.session_state.selected_destination = dest["name"]
                                st.switch_page("pages/planner.py")
                                st.rerun()
                        with button_cols[1]:
                            if st.button(
                                "Edit",
                                key=f"edit_{dest_idx}",
                                width="stretch",
                                type="secondary",
                            ):
                                st.session_state.edit_destination = dest["name"]
                                st.switch_page("pages/destination.py")
                                st.rerun()


# Add destination button
# st.markdown("---")
def save_destination(name, description):
    """Save destination"""
    pass


col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("➕ Add New Destination", key="add_destination"):
        add_destination()
