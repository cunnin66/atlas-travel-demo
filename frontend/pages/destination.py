import os
import sys

import streamlit as st
from components.menu import menu_with_redirect


def save_destination(name, description, lat, lon, tags):
    st.error("Not implemented")


files = []
menu_with_redirect()

if "edit_destination" not in st.session_state:
    st.subheader("Unknown Destination!")

    st.markdown(
        """
    Oops! There was an error: no destination data found. Please navigate back to the [Home Page](./home) to choose a destination.
    """
    )
    if st.button("< Back", type="secondary"):
        st.switch_page("pages/home.py")

else:
    st.subheader(f"Destination Editor: {st.session_state.edit_destination}")

    cols = st.columns(2, gap="large")
    with cols[0]:
        st.write("EDITOR")
        name = st.text_input("Destination Name")
        description = st.text_area("Description")
        with st.container(horizontal=True):
            lat = st.number_input("Latitude")
            lon = st.number_input("Longitude")
        tags = st.text_input("Tags")
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("< Back", type="secondary"):
                st.switch_page("pages/home.py")
            if st.button("Save", type="primary"):
                save_destination(name, description, lat, lon, tags)

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
