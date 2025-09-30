from time import sleep

import streamlit as st
from components.menu import menu
from utils import initialize_session_state, submit_login

st.logo("assets/Atlas-logo.png", size="large")


initialize_session_state()


menu()
st.subheader("Login Page 🔐")

# --- USER AUTHENTICATION ---
username = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if submit_login(username, password):
        st.success("Logged in successfully!")
        sleep(1)
        st.switch_page("pages/home.py")  # Rerun the script to reflect the login state
