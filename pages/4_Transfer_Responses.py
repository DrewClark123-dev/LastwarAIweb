import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Callbacks for updates
def on_submit_pass(check):
    pw = st.secrets["transfer_pw"]["password"]
    if check == pw:
        st.session_state.logged_in = True
        st.session_state.incorrect_pass = False
    else:
        st.session_state.logged_in = False
        st.session_state.incorrect_pass = True

def get_worksheet():
    # Convert secrets into dict
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Set up the credentials using your service account
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Authenticate and create a client to interact with Google Sheets
    client = gspread.authorize(creds)
    sheet_id = "1Tg0NrNN5GgH_KUbt_DwSepdsE21Gm1Q6RXtLdpd3x9Q"
    spreadsheet = client.open_by_key(sheet_id)
    # Select the first worksheet
    worksheet = spreadsheet.get_worksheet(0)
    return worksheet

def get_sheet_data():
    worksheet = get_worksheet()
    header_row = worksheet.row_values(1)  # Get the first row which is assumed to be the header
    rawdata = worksheet.get_all_records(expected_headers=header_row)
    data = pd.DataFrame(rawdata)
    data = data.fillna("").astype(str) # Fix serialization issue
    return data

if __name__ == "__main__":
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Transfer 1103")
    st.title("Response Viewer")
    st.write("")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "incorrect_pass" not in st.session_state:
        st.session_state.incorrect_pass = False

    # Login if needed
    if not st.session_state.logged_in:
        pass1, space1 = st.columns([1, 2])
        pw_check = pass1.text_input("Enter your password:")
        pass1.button("Submit", on_click=on_submit_pass, args=(pw_check,))

    if st.session_state.logged_in:
        if "response_df" not in st.session_state:
            st.session_state.response_df = get_sheet_data()
        st.subheader("Transfer Applications")
        st.write("")
        st.dataframe(st.session_state.response_df, height=700)
        
    if st.session_state.incorrect_pass == True:
        st.markdown('<p style="color:red;">Password Incorrect</p>', unsafe_allow_html=True)