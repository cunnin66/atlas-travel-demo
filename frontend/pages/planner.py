import os
import sys

import streamlit as st
from components.menu import menu_with_redirect
from pages.destination import get_destination
from utils import request_with_auth


def submit_trip_request(prompt):
    response = request_with_auth("POST", "/trip-requests", json={"prompt": prompt})
    if response.status_code == 200:
        st.success("Trip request submitted successfully!")
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
            submit_trip_request(prompt)
