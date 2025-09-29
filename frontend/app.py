import streamlit as st
from time import sleep
from components.menu import menu


st.logo("assets/Atlas-logo.png", size="large")


# Initialize session state for login status if it doesn't exist
st.session_state['logged_in'] = False



def check_login(username, password):
    """Returns True if the username and password are correct."""
    return username == "user" and password == "pass123"


menu()
st.subheader("Login Page 🔐")

# --- USER AUTHENTICATION ---
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if check_login(username, password):
        st.session_state['logged_in'] = True
        st.success("Logged in successfully!")
        sleep(1)
        st.switch_page("pages/home.py")  # Rerun the script to reflect the login state
else:
    st.error("Incorrect username or password.")


