import streamlit as st

if __name__ == "__main__":
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Transfer 1103")

    st.markdown("<h1 style='text-align: center;'>Apply to Transfer 1103!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Please fill out the form below.</h3>", unsafe_allow_html=True)

    # Embed Google Form
    google_form_url = "https://docs.google.com/forms/d/1_wwa4JF6zvGEqHrW8aQI7duA-dUAP_Zf_UHjBDwBc7A/viewform?embedded=true"
    st.components.v1.iframe(google_form_url, height=2100, scrolling=False)
