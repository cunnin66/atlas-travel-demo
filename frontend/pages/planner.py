import os
import sys

import streamlit as st
from components.menu import menu_with_redirect
from pages.destination import get_destination
from utils import request_with_auth


def submit_trip_request(dest_id, prompt):
    response = request_with_auth(
        "POST", "/qa/plan", json={"destination_id": dest_id, "prompt": prompt}
    )
    if response.status_code == 200:
        st.success("Trip request completed successfully!")
        return response.json()
    else:
        st.error(
            f"Error: Unable to submit trip request (status code {response.status_code})"
        )


if "selected_destination" in st.session_state:
    destination = get_destination(st.session_state.selected_destination)
else:
    destination = None

menu_with_redirect()

if destination is None:
    st.subheader("Unknown Destination!")

    st.markdown(
        """
    Oops! There was an error: no destination selected. Please navigate back to the [Home Page](./home) to choose a destination.
    """
    )
    if st.button("< Back", type="secondary"):
        st.switch_page("pages/home.py")

else:
    st.subheader(f"🗺️ Plan Your Trip for {destination['name']}")
    st.write(
        "Tell us what you're looking to do on your trip, and we'll help you plan it!"
    )
    st.markdown(
        """
        **Example criteria to include:**
        - Length of trip
        - Budget
        - Interests and Activity Preferences
        - Travel constraints
        """
    )

    prompt = st.text_area("")
    with st.container(horizontal_alignment="left", horizontal=True):
        if st.button("< Back", type="secondary"):
            st.switch_page("pages/home.py")
        if st.button("Go", type="primary"):
            # Clear any previous plan
            if "current_plan" in st.session_state:
                del st.session_state["current_plan"]

            # Show loading message
            with st.spinner("Creating your travel plan..."):
                plan = submit_trip_request(destination["id"], prompt)
                if plan:
                    st.session_state["current_plan"] = plan

    # Display the plan if it exists in session state
    if "current_plan" in st.session_state and st.session_state["current_plan"]:
        plan = st.session_state["current_plan"]
        if "answer_markdown" in plan and plan["answer_markdown"]:
            st.markdown(plan["answer_markdown"])
