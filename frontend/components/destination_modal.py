import streamlit as st
from utils import request_with_auth


def save_destination(name, description):
    """Save destination"""
    response = request_with_auth(
        "POST", "/destinations", json={"name": name, "description": description}
    )
    if response.status_code == 200:
        st.success(f"Destination '{name}' saved successfully!")
    else:
        st.error(
            f"Error: Unable to save destination (status code {response.status_code})"
        )


@st.dialog("Add New Destination")
def add_destination():
    """Add destination modal"""
    st.write("Please fill in the details for the new destination.")

    name = st.text_input("Destination Name *")
    description = st.text_area("Description (Optional)")

    with st.container(horizontal_alignment="right", horizontal=True):
        if st.button("Cancel", type="secondary"):
            st.session_state.show_modal = False  # Close modal on cancel
            st.rerun()
        if st.button("Submit", type="primary"):
            if not name:
                st.warning("Destination Name is a required field.")
            else:
                with st.spinner("Saving..."):
                    save_destination(name, description)
                st.success(f"Destination '{name}' saved successfully!")
                st.session_state.show_modal = False  # Close modal on success
                st.rerun()  # Rerun to reflect changes and close dialog
