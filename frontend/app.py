import streamlit as st
import requests
from utils import API_URL, load_css
from prompt_scrubber import prompt_scrubber_tab
from file_scrubber import file_scrubber_tab


st.markdown(f'<style>{load_css("style.css")}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="SecurePrompt", page_icon="🤖")
st.title("SecurePrompt :robot:")

def login_form():
    """Handles the user login UI and logic."""
    st.html(f"<div class='welcome-message'>Please log in to access the app.</div>")
    with st.form("login"):
        username = st.text_input("Username", value="jdoe")
        password = st.text_input("Password", type="password", value="demo_password")
        submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            response = requests.post(
                f"{API_URL}/login", json={"username": username, "password": password}
            )
            if response.status_code == 200:
                json_result = response.json()
                st.session_state["token"] = json_result["token"]
                st.session_state["full_name"] = json_result["full_name"]
                st.session_state["role"] = json_result["role"]
                st.rerun()
            else:
                st.error("Login failed")


def main_app():
    """Handles the logged-in state of the application."""
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}

    # Header and Logout
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.html(f"<div class='welcome-message'>Welcome <strong>{st.session_state.get('full_name')}!</strong></div>")
    with col2:
        left, right = st.columns([1, 1])
        with right:
            if st.button("➡️ Logout", type="tertiary", key="logout_button"):
                r = requests.post(f"{API_URL}/logout", headers=headers)
                if r.status_code == 200:
                    del st.session_state["token"]
                    st.rerun()

    # Tabs
    tab_prompt_scrubber, tab_file_scrubber = st.tabs(
        ["✍🏻 Prompt Scrubber", "📄 File Scrubber"]
    )

    with tab_prompt_scrubber:
        prompt_scrubber_tab()

    with tab_file_scrubber:
        file_scrubber_tab()


# --- Main Application Logic ---
if "token" not in st.session_state:
    login_form()
else:
    main_app()