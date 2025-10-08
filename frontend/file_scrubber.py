import streamlit as st
import requests
from utils import API_URL, risk_options, get_risk_label, create_scrubbed_entity_report


def file_scrubber_tab():
    """
    Defines the UI and logic for the File Scrubber tab.
    """
    st.html("<div class='field_header'>Choose a file:</div>")
    uploaded_file = st.file_uploader(
        "",
        type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    st.html("<div class='field_header'>Select target risk level:</div>")
    file_risk_level = st.selectbox(
        "File target risk level",
        options=risk_options,
        format_func=get_risk_label,
        index=3,
        label_visibility="collapsed",
    )
    st.markdown("")

    if st.button("Anonymize File", type="primary", key="scrub_file"):
        if not uploaded_file:
            st.warning("Please choose a file to anonymize.")
            st.stop()

        # Assuming the token is in the session state from app.py
        if "token" not in st.session_state:
            st.error("Authentication token not found. Please log in.")
            st.stop()

        headers = {"Authorization": f"Bearer {st.session_state['token']}"}

        try:
            files = {"file": uploaded_file}
            response = requests.post(
                f"{API_URL}/file/scrub",
                headers=headers,
                files=files,
                data={"target_risk": file_risk_level},
            )

            if response.status_code == 200:
                json_result = response.json()
                entities = json_result.get("entities", [])

                if entities:
                    st.markdown("")
                    redacted_filename = json_result.get("filename", "")
                    download_url = json_result.get("download_url", "")
                    full_download_url = f"{API_URL.rstrip('/')}{download_url}?token={st.session_state['token']}"

                    st.html("<div class='field_header'>Anonymized file:</div>")
                    download_link_html = f"<a href='{full_download_url}' download='{redacted_filename}' title='Click to download'>{redacted_filename}</a>"
                    st.markdown(download_link_html, unsafe_allow_html=True)
                    st.markdown("")

                    with st.expander("Anonymization details"):
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
