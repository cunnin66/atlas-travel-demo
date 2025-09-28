import streamlit as st

st.set_page_config(
    page_title="Login - Atlas Travel Advisor",
    page_icon="🔐",
    layout="centered"
)

st.title("🔐 Login")

st.write("TODO: Build this page.")

# Placeholder login form
with st.form("login_form"):
    st.text_input("Username")
    st.text_input("Password", type="password")
    st.form_submit_button("Login")

st.info("Login functionality will be implemented to connect with the FastAPI backend.")
