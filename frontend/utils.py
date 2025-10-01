import json
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
        json={"refresh_token": st.session_state["refresh_token"]},
    )
    if response.status_code == 200:
        st.session_state["access_token"] = response.json()["access_token"]
        return True
    else:
        return False


def send_request(
    method, url, json=None, headers=None, files=None, data=None, params=None
):
    if method == "POST":
        return requests.post(
            url, json=json, headers=headers, files=files, data=data, params=params
        )
    elif method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "PUT":
        return requests.put(
            url, json=json, headers=headers, files=files, data=data, params=params
        )
    elif method == "DELETE":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Invalid method: {method}")


def request_with_auth(method, endpoint, json=None, files=None, data=None, params=None):
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    url = f"{BACKEND_API_URL}/api/v1{endpoint}"
    response = send_request(method, url, json, headers, files, data, params)

    if response.status_code == 401:
        if st.session_state["refresh_token"]:
            if refresh_token():
                # Update headers with new access token after refresh
                headers = {
                    "Authorization": f"Bearer {st.session_state['access_token']}"
                }
                response = send_request(method, url, json, headers, files, data, params)

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


def stream_request_with_auth(endpoint, json_data=None):
    """Stream request with authentication for Server-Sent Events"""
    headers = {
        "Authorization": f"Bearer {st.session_state['access_token']}",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
    }
    url = f"{BACKEND_API_URL}/api/v1{endpoint}"

    try:
        response = requests.post(url, json=json_data, headers=headers, stream=True)

        if response.status_code == 401:
            if st.session_state["refresh_token"]:
                if refresh_token():
                    # Update headers with new access token after refresh
                    headers = {
                        "Authorization": f"Bearer {st.session_state['access_token']}",
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    }
                    response = requests.post(
                        url, json=json_data, headers=headers, stream=True
                    )

        if response.status_code == 401:
            st.error("Error: Session has expired")
            logout()
            return None

        return response

    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None


def parse_sse_stream(response):
    """Parse Server-Sent Events stream and yield parsed data"""
    if not response:
        return

    try:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data_str = line[6:]  # Remove 'data: ' prefix
                try:
                    data = json.loads(data_str)
                    yield data
                except json.JSONDecodeError:
                    # Skip malformed JSON
                    continue
    except Exception as e:
        st.error(f"Error parsing stream: {str(e)}")


def logout():
    # Only attempt logout if we have tokens
    if st.session_state.get("access_token"):
        headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
        response = send_request(
            "POST",
            f"{BACKEND_API_URL}/api/v1/auth/logout",
            json={},  # Backend doesn't expect any JSON data
            headers=headers,
        )

    # Clear tokens regardless of logout success
    st.session_state["access_token"] = False
    st.session_state["refresh_token"] = False
    st.switch_page("app.py")
