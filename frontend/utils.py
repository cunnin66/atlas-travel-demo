import os

import requests
import streamlit as st

if "BACKEND_API_URL" not in os.environ:
    raise RuntimeError("Environment variable BACKEND_API_URL is not set.")
BACKEND_API_URL = os.environ["BACKEND_API_URL"]


def initialize_session_state():
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = False
    if "refresh_token" not in st.session_state:
        st.session_state["refresh_token"] = False
    if st.session_state["access_token"] or st.session_state["refresh_token"]:
        logout()


def refresh_token():
    response = requests.post(
        f"{BACKEND_API_URL}/api/v1/auth/refresh",
        data={"refresh_token": st.session_state["refresh_token"]},
    )
    if response.status_code == 200:
        st.session_state["access_token"] = response.json()["access_token"]
        return True
    else:
        return False


def send_request(method, url, json=None, headers=None):
    if method == "POST":
        return requests.post(url, json=json, headers=headers)
    elif method == "GET":
        return requests.get(url, headers=headers)
    elif method == "PUT":
        return requests.put(url, json=json, headers=headers)
    elif method == "DELETE":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Invalid method: {method}")


def request_with_auth(method, endpoint, json=None):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    url = f"{BACKEND_API_URL}/api/v1{endpoint}"
    response = send_request(method, url, json, headers)

    if response.status_code == 401:
        if st.session_state["refresh_token"]:
            if refresh_token():
                response = send_request(method, url, json, headers)

    if response.status_code == 401:
        st.error("Error: Session has expired")
        logout()
        return

    return response


def submit_login(username, password):
    response = requests.post(
        f"{BACKEND_API_URL}/api/v1/auth/login",
        data={"username": username, "password": password},
    )

    if response.status_code == 200:
        # Successful login
        payload = response.json()
        st.session_state["access_token"] = payload["access_token"]
        st.session_state["refresh_token"] = payload["refresh_token"]
        return True
    elif response.status_code == 401:
        st.error("Invalid username or password.")
        return False
    else:
        st.error(
            f"Error: Unable to process login request (status code {response.status_code})"
        )
        return False


def submit_register(username, password, organization):
    response = requests.post(
        f"{BACKEND_API_URL}/api/v1/auth/register",
        json={"email": username, "password": password, "org_name": organization},
    )

    if response.status_code == 200:
        # Successful register
        payload = response.json()
        st.session_state["access_token"] = payload["access_token"]
        st.session_state["refresh_token"] = payload["refresh_token"]
        return True
    elif response.status_code == 401:
        st.error("Invalid username, password, or organization.")
        return False
    else:
        st.error(
            f"Error: Unable to process register request (status code {response.status_code})"
        )
        return False


def is_authenticated():
    """Returns True if the username and password are correct."""
    return st.session_state.get("access_token", False) and st.session_state.get(
        "refresh_token", False
    )


def logout():
    response = send_request(
        "POST",
        f"{BACKEND_API_URL}/api/v1/auth/logout",
        json={"token": st.session_state["refresh_token"]},
    )
    st.session_state["access_token"] = False
    st.session_state["refresh_token"] = False
    st.switch_page("app.py")
