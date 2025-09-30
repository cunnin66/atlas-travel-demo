import os
import sys

import streamlit as st
from components.menu import menu_with_redirect
from pages.destination import get_destination
from utils import parse_sse_stream, request_with_auth, stream_request_with_auth

if "current_plan" in st.session_state:
    del st.session_state["current_plan"]


def stream_trip_request(dest_id, prompt):
    """Stream trip planning request and display real-time updates"""
    # Create placeholders for dynamic content
    status_placeholder = st.empty()
    messages_placeholder = st.empty()

    # Initialize message list
    messages = []
    final_result = None

    # Start streaming request
    response = stream_request_with_auth(
        "/qa/stream", json_data={"destination_id": dest_id, "prompt": prompt}
    )

    if not response:
        st.error("Failed to connect to the planning service")
        return None

    if response.status_code != 200:
        st.error(
            f"Error: Unable to submit trip request (status code {response.status_code})"
        )
        return None

    try:
        # Process the stream
        for data in parse_sse_stream(response):
            if data.get("type") == "message":
                # Add status message
                message = data.get("content", "")
                with messages_placeholder.container():
                    st.write(f"🔄 {message}")

            elif data.get("type") == "complete":
                # Final result received
                final_result = data.get("content", "")
                status_placeholder.success("✅ Trip planning completed!")
                messages_placeholder.empty()  # Clear status messages
                break

            elif data.get("type") == "error":
                error_msg = data.get("content", "Unknown error occurred")
                st.error(f"❌ Error: {error_msg}")
                return None

    except Exception as e:
        st.error(f"Error processing stream: {str(e)}")
        return None

    return {"answer_markdown": final_result} if final_result else None


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
    with st.container(horizontal=True):
        with st.container():
            st.subheader(f"🗺️ Plan Your Trip for {destination['name']}")
            st.write(
                "Tell us what you're looking to do on your trip, and we'll help you plan it!"
            )
        with st.columns(2)[1]:
            st.markdown(
                """
            **Example criteria to include:**
            - Length of trip
            - Budget
            - Interests and Activity Preferences
            - Travel constraints
            """
            )

    prompt = st.text_area(
        "", value=f"Help me plan my trip to {destination['name']}, where ..."
    )
    with st.container(horizontal_alignment="left", horizontal=True):
        if st.button("< Back", type="secondary"):
            st.switch_page("pages/home.py")
        if st.button("Go", type="primary"):
            # Clear any previous plan
            if "current_plan" in st.session_state:
                del st.session_state["current_plan"]

            # Stream the trip planning process
            plan = stream_trip_request(destination["id"], prompt)
            if plan:
                st.session_state["current_plan"] = plan
                st.rerun()  # Refresh to show the final result

    # Display the plan if it exists in session state
    if "current_plan" in st.session_state and st.session_state["current_plan"]:
        plan = st.session_state["current_plan"]
        if "answer_markdown" in plan and plan["answer_markdown"]:
            st.markdown(plan["answer_markdown"])
