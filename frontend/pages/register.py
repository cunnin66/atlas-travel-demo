from time import sleep

import streamlit as st
from components.menu import menu
from utils import submit_register

menu()
st.subheader("Registration 📝")

# --- USER AUTHENTICATION ---
username = st.text_input("Email")
password = st.text_input("Password", type="password")
organization = st.text_input("Organization Name")

if st.button("Register"):
    if submit_register(username, password, organization):
        st.success("Registered successfully!")
        sleep(1)
        st.switch_page("pages/home.py")  # Rerun the script to reflect the login state
