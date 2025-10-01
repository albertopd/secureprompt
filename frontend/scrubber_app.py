import requests
import os
import pandas as pd
import streamlit as st
from st_copy import copy_button


API_URL = os.environ.get("SECUREPROMPT_API", "http://localhost:8000/api/v1")


st.set_page_config(page_title="SecurePrompt", page_icon="🤖")


# --- Auth check ---
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
                "Scrubbed": e.get("replacement", ""),
                "Original": e.get("span", ""),
                "Type": e.get("type", ""),
                "Source": e.get("source", ""),
                "Score": score_display,
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["Scrubbed", "Original", "Type", "Source", "Score"],
    )

    return df


if "token" not in st.session_state:
    st.title(":orange[SecurePrompt] :robot:")
    st.markdown("**Please log in to access the app.**")
    with st.form("login"):
        username = st.text_input("Username", value="demo_user")
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
    st.title(":orange[SecurePrompt] :robot:")
    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.markdown(f"Welcome **{st.session_state.get('full_name')}!**")
    with col2:
        left, right = st.columns([1, 1])
        with right:
            if st.button("➡️ Logout", type="tertiary"):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                r = requests.post(f"{API_URL}/logout", headers=headers)
                if r.status_code == 200:
                    del st.session_state["token"]
                    st.rerun()

    # Custom CSS to style the tab labels
    st.markdown(
        """
        <style>
        /* Target the <p> tag inside the tabs (where your text 'Prompt Scrubber' is) */
        [data-baseweb="tab"] p {
            font-size: 1.3rem;
            font-weight: 500 !important;
        }
        """,
        unsafe_allow_html=True,
    )

    tab_prompt_scrubber, tab_file_scrubber = st.tabs(
        ["✍🏻 Prompt Scrubber", "📄 File Scrubber"]
    )

    with tab_prompt_scrubber:
        prompt = st.text_area("Please enter a prompt that you need to scrub:")
        if st.button("Scrub Prompt", type="primary", key="scrub_prompt"):
            if not prompt:
                st.warning("Please enter a prompt.")
                st.stop()

            try:
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(
                    f"{API_URL}/scrub",
                    json={"user_id": "demo", "prompt": prompt},
                    headers=headers,
                )
                if response.status_code == 200:
                    json_result = response.json()
                    entities = json_result.get("entities", [])

                    if entities:
                        st.markdown("")
                        redacted_text = json_result["redacted_text"]

                        title_col, button_col = st.columns([1, 4], gap="small")

                        with title_col:
                            st.markdown("**Redacted Prompt**")

                        with button_col:
                            with button_col:
                                copy_button(
                                    redacted_text,
                                    tooltip="Copy redacted prompt to clipboard",
                                    copied_label="Copied!",
                                    icon="st",
                                )

                        st.info(redacted_text)

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
        uploaded_file = st.file_uploader(
            "Please choose a file that you need to scrub:",
            type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        if st.button("Scrub File", type="primary", key="scrub_file"):
            if not uploaded_file:
                st.warning("Please choose a file to scrub.")
                st.stop()

            try:
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                files = {"file": uploaded_file}
                response = requests.post(
                    f"{API_URL}/file/scrub", headers=headers, files=files
                )
                if response.status_code == 200:
                    json_result = response.json()
                    entities = json_result.get("entities", [])

                    if entities:
                        st.markdown("")
                        redacted_filename = json_result.get("filename", "")
                        download_url = json_result.get("download_url", "")
                        full_download_url = f"{API_URL.rstrip('/')}{download_url}"

                        st.markdown("**Redacted File**")
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
