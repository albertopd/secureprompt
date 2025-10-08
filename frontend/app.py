import streamlit as st
import requests
from utils import API_URL, load_css
from text_scrubber import prompt_scrubber_tab
from file_scrubber import file_scrubber_tab


st.markdown(f'<style>{load_css("style.css")}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="SecurePrompt", page_icon="🤖")
st.title("SecurePrompt :robot:")

def login_form():
    """Handles the user login UI and logic."""
    st.html(f"<div class='welcome-message'>Please log in to access the app.</div>")
    with st.form("login"):
        email = st.text_input("Email", value="edward.richardson@ing.com")
        password = st.text_input("Password", type="password", value="OE27VJ")
        submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            response = requests.post(
                f"{API_URL}/auth/login", json={"email": email, "password": password}
            )
            if response.status_code == 200:
                json_result = response.json()
                st.session_state["token"] = json_result["token"]
                st.rerun()
            else:
                st.error("Login failed")


def main_app():
    """Handles the logged-in state of the application."""
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}

    # Header and Logout
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.html(f"<div class='welcome-message'>Welcome!</strong></div>")
    with col2:
        _, right = st.columns([1, 1])
        with right:
            if st.button("➡️ Logout", type="tertiary", key="logout_button"):
                requests.post(f"{API_URL}/auth/logout", headers=headers)
                del st.session_state["token"]
                st.rerun()

    # Tabs
    tab_prompt_scrubber, tab_file_scrubber = st.tabs(
        ["✍🏻 Prompt Anonymizer", "📄 File Anonymizer"]
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