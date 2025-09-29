import streamlit as st

def enforce_authentication():
    if not is_authenticated():
        st.warning("Please log in to view this page.")
        logout()

def is_authenticated():
    """Returns True if the username and password are correct."""
    return st.session_state.get('logged_in', False)


def logout():
    st.session_state['logged_in'] = False
    st.switch_page("app.py")
    