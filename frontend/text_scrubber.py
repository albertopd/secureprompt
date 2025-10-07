import streamlit as st
import requests
from utils import API_URL, risk_options, get_risk_label, create_scrubbed_entity_report


def prompt_scrubber_tab():
    """
    Defines the UI and logic for the Prompt Scrubber tab.
    """
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

    if st.button("Anonymize Prompt", type="primary", key="scrub_prompt"):
        if not prompt:
            st.warning("Please enter a prompt.")
            st.stop()

        # Assuming the token is in the session state from app.py
        if "token" not in st.session_state:
            st.error("Authentication token not found. Please log in.")
            st.stop()

        headers = {"Authorization": f"Bearer {st.session_state['token']}"}

        try:
            response = requests.post(
                f"{API_URL}/text/scrub",
                json={"user_id": "demo", "prompt": prompt, "target_risk": prompt_risk_level},
                headers=headers,
            )
            
            if response.status_code == 200:
                json_result = response.json()
                entities = json_result.get("entities", [])

                if entities:
                    st.markdown("")
                    scrubbed_text = json_result["scrubbed_text"]

                    st.html("<div class='field_header'>Anonymized prompt:</div>")
                    st.code(scrubbed_text, language="html", wrap_lines=True)

                    with st.expander("Anonymization details"):
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