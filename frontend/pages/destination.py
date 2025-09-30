import os
import sys

import streamlit as st
from components.menu import menu_with_redirect
from utils import request_with_auth

TAG_OPTIONS = [
    "Beach",
    "Mountain",
    "Cultural",
    "Historical",
    "Food",
    "Shopping",
    "Nightlife",
]


def save_destination(id, name, description, lat, lon, tags=[]):
    response = request_with_auth(
        "PUT",
        f"/destinations/{id}",
        json={
            "name": name,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "tags": tags,
        },
    )
    if response.status_code == 200:
        st.success(f"Destination '{name}' saved successfully!")
    else:
        st.error(
            f"Error: Unable to save destination (status code {response.status_code})"
        )


def get_destination(destination_id):
    response = request_with_auth("GET", f"/destinations/{destination_id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


destination = st.session_state.edit_destination and get_destination(
    st.session_state.edit_destination
)
files = []
menu_with_redirect()

if destination is None:
    st.subheader("Unknown Destination!")

    st.markdown(
        """
    Oops! There was an error: no destination data found. Please navigate back to the [Home Page](./home) to choose a destination.
    """
    )
    if st.button("< Back", type="secondary"):
        st.switch_page("pages/home.py")

else:
    st.subheader(f"Destination Editor: {destination['name']}")

    cols = st.columns(2, gap="large")
    with cols[0]:
        st.write("EDITOR")
        name = st.text_input("Destination Name", value=destination["name"])
        description = st.text_area("Description", value=destination["description"])
        with st.container(horizontal=True):
            lat = st.number_input("Latitude", value=destination["latitude"])
            lon = st.number_input("Longitude", value=destination["longitude"])
        tags = st.multiselect("Tags", default=destination["tags"], options=TAG_OPTIONS)
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("< Back", type="secondary"):
                st.switch_page("pages/home.py")
            if st.button("Save", type="primary"):
                save_destination(
                    destination["id"],
                    name if name else destination["name"],
                    description if description else destination["description"],
                    lat if lat is not None else destination.get("latitude"),
                    lon if lon is not None else destination.get("longitude"),
                    tags if tags else destination.get("tags", []),
                )

    with cols[1]:
        with st.container(border=True):
            st.write("KNOWLEDGE BASE")
            if len(files) > 0:
                for file in files:
                    st.write(file.name)
            else:
                with st.container(horizontal_alignment="center"):
                    st.markdown("*No files uploaded*")
            st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])
