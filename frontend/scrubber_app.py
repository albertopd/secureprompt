import streamlit as st
import requests
import os


API_URL = os.environ.get("SECUREPROMPT_API", "http://localhost:8000/api/v1")


st.title("SecurePrompt")

if "token" not in st.session_state:
    with st.form("login"):
        username = st.text_input("Username", value="demo_user")
        password = st.text_input("Password", type="password", value="demo_password")
        submitted = st.form_submit_button("Login")
        if submitted:
            r = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if r.status_code == 200:
                st.session_state["token"] = r.json()["token"]
            else:
                st.error("Login failed")

if "token" in st.session_state:
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    prompt = st.text_area("Enter prompt:")
    if st.button("Scrub"):
        r = requests.post(f"{API_URL}/scrub", json={"user_id": "demo", "prompt": prompt}, headers=headers)
        st.json(r.json())
