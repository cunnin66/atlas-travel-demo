import streamlit as st
from components.header import header
from utils import is_authenticated


def authenticated_menu():
    # Show a navigation menu for authenticated users
    #st.sidebar.page_link("app.py", label="Switch accounts")
    header()
    st.sidebar.page_link("pages/home.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/admin.py", label="Admin", icon="⚙️")
    st.sidebar.page_link("app.py", label="Log Out", icon="⬅️")
    st.set_page_config(
        page_title="Atlas Travel Advisor",
        page_icon="🌍",
        layout="wide"
    )


def unauthenticated_menu():
    header()
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("app.py", label="Log in")
    st.sidebar.page_link("pages/register.py", label="Register")
    st.set_page_config(
        page_title="Atlas Travel Advisor",
        page_icon="🌍",
        layout="centered"
    )


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if not is_authenticated():
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if not is_authenticated():
        st.switch_page("app.py")
    menu()