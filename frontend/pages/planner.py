import json
import os
import sys
import time
from typing import Dict, List, Optional

import streamlit as st
from components.menu import menu_with_redirect
from pages.destination import get_destination
from utils import parse_sse_stream, request_with_auth, stream_request_with_auth

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "current_plan_id" not in st.session_state:
    st.session_state.current_plan_id = None
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False


def add_message_to_history(role: str, content: str, plan_data: Optional[Dict] = None):
    """Add a message to the conversation history"""
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": time.time(),
        "plan_data": plan_data,
    }
    st.session_state.conversation_history.append(message)


def stream_trip_request(dest_id: int, prompt: str, plan_id: Optional[str] = None):
    """Stream trip planning request using the AI agent stream endpoint"""

    # Prepare request data
    request_data = {"destination_id": dest_id, "prompt": prompt}
    if plan_id:
        request_data["plan_id"] = plan_id

    # Create placeholders for streaming updates
    status_container = st.empty()

    # Start streaming request to AI agent endpoint
    response = stream_request_with_auth("/qa/stream", json_data=request_data)

    if not response:
        st.error("Failed to connect to the planning service")
        return None

    if response.status_code != 200:
        st.error(
            f"Error: Unable to submit trip request (status code {response.status_code})"
        )
        return None

    try:
        status_messages = []

        # Process the stream
        for data in parse_sse_stream(response):
            if data.get("type") == "status":
                # Show streaming status
                status_message = data.get("content", "")
                status_messages.append(status_message)

                with status_container.container():
                    st.info(f"🤖 {status_message}")

            elif data.get("type") == "plan_complete":
                # Final result received
                plan_data = data.get("plan", {})
                plan_id = data.get("plan_id")
                is_edit = data.get("is_edit", False)

                # Clear status messages
                status_container.empty()

                # Store plan ID for future edits
                st.session_state.current_plan_id = plan_id

                return {"plan_data": plan_data, "plan_id": plan_id, "is_edit": is_edit}

            elif data.get("type") == "error":
                error_msg = data.get("content", "Unknown error occurred")
                status_container.error(f"❌ Error: {error_msg}")
                return None

    except Exception as e:
        st.error(f"Error processing stream: {str(e)}")
        return None

    return None


def display_conversation_history():
    """Display the conversation history in a chat-like format"""
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                if message.get("plan_data"):
                    # Display the plan markdown
                    plan_markdown = message["plan_data"].get("answer_markdown", "")
                    if plan_markdown:
                        st.markdown(plan_markdown)
                else:
                    st.write(message["content"])


def clear_conversation():
    """Clear the conversation history and reset state"""
    st.session_state.conversation_history = []
    st.session_state.current_plan_id = None
    st.session_state.is_streaming = False


# Get destination info
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
    # Header section
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🗺️ AI Travel Planner")
        st.subheader(f"Planning your trip to {destination['name']}")

    with col2:
        with st.container(horizontal=True):
            if st.button("< Back", type="secondary"):
                st.switch_page("pages/home.py")
            if st.button("🔄 New Conversation", type="secondary"):
                clear_conversation()
                st.rerun()

    # Show helpful tips if no conversation started
    if not st.session_state.conversation_history:
        st.info(
            """
            💡 **Get started by describing your ideal trip!**

            Include details like:
            • Length of trip (e.g., "3 days", "a weekend")
            • Budget range (e.g., "$500 total", "mid-range")
            • Interests (e.g., "museums", "nightlife", "nature")
            • Travel style (e.g., "relaxed", "packed with activities")
            • Special requirements (e.g., "vegetarian food", "accessible venues")
            """
        )

    # Chat interface container
    chat_container = st.container(height=400)

    with chat_container:
        display_conversation_history()

    # Input section at bottom
    st.markdown("---")

    # Determine if this is an initial request or modification
    is_modification = st.session_state.current_plan_id is not None
    placeholder_text = (
        "Ask me to modify your plan..."
        if is_modification
        else f"Help me plan my trip to {destination['name']}..."
    )

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_area(
                "Message",
                placeholder=placeholder_text,
                height=80,
                label_visibility="collapsed",
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
            submit_button = st.form_submit_button(
                "✈️ Plan" if not is_modification else "🔄 Update",
                type="primary",
                use_container_width=True,
            )

    # Handle form submission
    if submit_button and user_input.strip():
        if not st.session_state.is_streaming:
            st.session_state.is_streaming = True

            # Add user message to history
            add_message_to_history("user", user_input.strip())

            # Show user message immediately
            with chat_container:
                display_conversation_history()

            # Stream the response
            with st.spinner("🤖 AI is thinking..."):
                result = stream_trip_request(
                    destination["id"],
                    user_input.strip(),
                    st.session_state.current_plan_id,
                )

            if result:
                # Add assistant response to history
                response_text = (
                    "Here's your updated travel plan!"
                    if result.get("is_edit")
                    else "Here's your travel plan!"
                )
                add_message_to_history("assistant", response_text, result["plan_data"])

            st.session_state.is_streaming = False
            st.rerun()

    elif submit_button and not user_input.strip():
        st.warning("Please enter a message before submitting!")

    # Show current status
    if st.session_state.is_streaming:
        st.info("🤖 AI is working on your request...")
    elif st.session_state.current_plan_id:
        st.success(
            f"✅ Plan ready! You can ask for modifications above. (Plan ID: {st.session_state.current_plan_id})"
        )
