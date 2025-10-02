from enum import Enum
import requests
import os
import pandas as pd
import streamlit as st


API_URL = os.environ.get("SECUREPROMPT_API", "http://localhost:8000/api/v1")

# Helpers

def create_scrubbed_entity_report(entities):
    rows = []
    for e in entities:
        score_val = e.get("score", "")
        # try to coerce to float and format: as percent if 0..1, otherwise rounded number
        score_display = ""
        try:
            s = float(score_val)
            if 0.0 <= s <= 1.0:
                score_display = f"{s:.1%}"  # e.g. 0.87 -> "87.0%"
            else:
                score_display = f"{s:.3f}"  # e.g. 123 -> "123.000"
        except Exception:
            score_display = score_val  # keep original if not numeric

        rows.append(
            {
                "Original": e.get("span", ""),
                "Replacement": e.get("replacement", ""),
                "Reason": e.get("explanation", ""),
                "Score": score_display
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["Original", "Replacement", "Reason", "Score"]
    )

    return df

class RiskLevel(Enum):
    C1 = "C1 Public"
    C2 = "C2 Restricted"
    C3 = "C3 Confidential"
    C4 = "C4 Secret / C3 Sensitive"

risk_options = [m.name for m in RiskLevel]

def get_risk_label(option: str) -> str:
    try:
        return RiskLevel[option].value
    except KeyError:
        return option

# APP

st.set_page_config(page_title="SecurePrompt", page_icon="🤖")
st.title("SecurePrompt :robot:")

# Custom CSSs
st.markdown(
    """
    <style>
        /* Target the <p> tag inside the tabs (where your text 'Prompt Scrubber' is) */
        [data-baseweb="tab"] p {
            font-size: 1.15rem;
            font-weight: 500 !important;
        }

        /* Target any element whose class attribute contains 'st-key-logout_button' */
        [class*="st-key-logout_button"] p {
            font-size: 0.9rem;
        }

        .welcome-message {
            font-size: 1.4rem;
            font-weight: 500 !important;
        }

        .field_header {
            font-size: 1.1rem;
            font-weight: 500 !important;
            margin-bottom: -0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Auth check
if "token" not in st.session_state:
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
else:
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}

    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.html(f"<div class='welcome-message'>Welcome <strong>{st.session_state.get('full_name')}!</strong></div>")
    with col2:
        left, right = st.columns([1, 1])
        with right:
            if st.button("➡️ Logout", type="tertiary", key="logout_button"):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                r = requests.post(f"{API_URL}/logout", headers=headers)
                if r.status_code == 200:
                    del st.session_state["token"]
                    st.rerun()

    tab_prompt_scrubber, tab_file_scrubber = st.tabs(
        ["✍🏻 Prompt Scrubber", "📄 File Scrubber"]
    )

    with tab_prompt_scrubber:
        st.html("<div class='field_header'>Enter your prompt:</div>")
        prompt = st.text_area("", label_visibility="collapsed")
        st.html("<div class='field_header'>Select target risk level:</div>")
        prompt_risk_level = st.selectbox(
            "Propmpt target risk level",
            options=risk_options,
            format_func=get_risk_label,
            index=3,
            label_visibility="collapsed"
        )
        st.markdown("")

        if st.button("Scrub Prompt", type="primary", key="scrub_prompt"):
            if not prompt:
                st.warning("Please enter a prompt.")
                st.stop()

            try:
                response = requests.post(
                    f"{API_URL}/scrub",
                    json={"user_id": "demo", "prompt": prompt, "target_risk": prompt_risk_level},
                    headers=headers,
                )
                if response.status_code == 200:
                    json_result = response.json()
                    entities = json_result.get("entities", [])

                    if entities:
                        st.markdown("")
                        redacted_text = json_result["redacted_text"]

                        st.html("<div class='field_header'>Redacted prompt:</div>")
                        st.code(redacted_text, language="html")

                        with st.expander("Redaction details"):
                            df = create_scrubbed_entity_report(entities)
                            st.dataframe(df, hide_index=True)
                    else:
                        st.success("No sensitive information detected.")
                else:
                    st.error(
                        f"Error occurred while scrubbing prompt. Status Code: {response.status_code} Message: {response.text}"
                    )
            except Exception as e:
                st.error(f"Error occurred while scrubbing prompt: {e}")

    with tab_file_scrubber:
        st.html("<div class='field_header'>Choose a file:</div>")
        uploaded_file = st.file_uploader(
            "",
            type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
            label_visibility="collapsed"
        )
        st.html("<div class='field_header'>Select target risk level:</div>")
        file_risk_level = st.selectbox(
            "File target risk level",
            options=risk_options,
            format_func=get_risk_label,
            index=3,
            label_visibility="collapsed"
        )
        st.markdown("")

        if st.button("Scrub File", type="primary", key="scrub_file"):
            if not uploaded_file:
                st.warning("Please choose a file to scrub.")
                st.stop()

            try:
                files = {"file": uploaded_file}
                response = requests.post(
                    f"{API_URL}/file/scrub", headers=headers, files=files, data={"target_risk": file_risk_level}
                )
                if response.status_code == 200:
                    json_result = response.json()
                    entities = json_result.get("entities", [])

                    if entities:
                        st.markdown("")
                        redacted_filename = json_result.get("filename", "")
                        download_url = json_result.get("download_url", "")
                        full_download_url = f"{API_URL.rstrip('/')}{download_url}"

                        st.html("<div class='field_header'>Redacted file:</div>")
                        download_link_html = f"<a href='{full_download_url}' download='{redacted_filename}' title='Click to download'>{redacted_filename}</a>"
                        st.markdown(download_link_html, unsafe_allow_html=True)
                        st.markdown("")

                        with st.expander("Redaction details"):
                            df = create_scrubbed_entity_report(entities)
                            st.dataframe(df, hide_index=True)
                    else:
                        st.success("No sensitive information detected.")
                else:
                    st.error(
                        f"Error occurred while scrubbing file. Status Code: {response.status_code} Message: {response.text}"
                    )
            except Exception as e:
                st.error(f"Error occurred while scrubbing file: {e}")
