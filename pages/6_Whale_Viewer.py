import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a whale THP comparison chart between servers

#database = 'mySQL'
database = 'sqlite'

# Callbacks for selection box updates
def on_servers_change():
    st.session_state.whale_selected_servers = st.session_state.whale_server_multiselect_value
def on_dates_change():
    st.session_state.whale_date = st.session_state.whale_date_selectbox_value
def whale_checkbox():
    if st.session_state.whale_warzones_check:
        st.session_state.whale_selected_servers = st.session_state.whale_region
        st.session_state.whale_check = True
    else:
        st.session_state.whale_check = False
        if "whale_selected_servers" in st.session_state:
            del st.session_state["whale_selected_servers"]

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'whale_servers' not in st.session_state:
        server_query = "select distinct warzone from totalhero where date = '12/06/25' order by warzone"
        server_df = db.query_df(conn, server_query)
        st.session_state.whale_region = server_df.iloc[:, 0].tolist()
        print("[INFO] Pulled servers from Database")
    if 'whale_dates' not in st.session_state:
        date_query = "select distinct date from totalhero order by date desc"
        date_df = db.query_df(conn, date_query)
        st.session_state.whale_dates = date_df.iloc[:, 0].tolist()
        print("[INFO] Pulled dates from Database")

def render_selection_boxes(col):
    space1, sel1, sel3, check, space2 = col.columns([1, 6, 1, 1, 1])

    if 'whale_check' not in st.session_state:
        st.session_state.whale_check = False

    check.markdown("<div style='padding-top: 30px'> </div>", unsafe_allow_html=True)
    whale_check = check.checkbox(
        "All Warzones",
        value=st.session_state.whale_check,
        key="whale_warzones_check",
        on_change=whale_checkbox
        )

    if 'whale_selected_servers' not in st.session_state:
        st.session_state.whale_selected_servers = [1103,1104,1101,1098,1107]
    whale_selected_servers = sel1.multiselect(
        "Select multiple servers",
        options=st.session_state.whale_region,
        key="whale_server_multiselect_value",
        default=st.session_state.whale_selected_servers,
        on_change=on_servers_change
    )
    if 'whale_date' not in st.session_state:
        date_query = "select max(date) from totalhero"
        date_df = db.query_df(conn, date_query)
        st.session_state.whale_date =  date_df.iloc[0, 0]   # first row, first column
    whale_date = sel3.selectbox(
        "Date",
        options=st.session_state.whale_dates,
        key="whale_date_selectbox_value",
        index=st.session_state.whale_dates.index(st.session_state.whale_date), 
        on_change=on_dates_change
    )
    return whale_selected_servers

def print_server_chart(col, metric):
    combined_data = []
    for server in st.session_state.whale_selected_servers:
        if database == 'mySQL':
            server_query = "select * from totalhero where date = %s and warzone = %s order by totalhero desc limit 10"
        else:
            server_query = f"select * from totalhero where date = ? and warzone = ? order by totalhero desc limit 10" # sqlite
        
        server_df = db.query_df(conn, server_query, [st.session_state.whale_date, server])
        if not server_df.empty:
            server_df.columns = ['date', 'warzone', 'alliance', 'player', 'totalhero']
            combined_data.append(server_df[['warzone','alliance','player','totalhero']])
    print("[INFO] Pulled totalhero data from Database")

    # Return true if we need to print a blank chart
    if not combined_data:
        return True

    # Rank players for charting
    all_servers_df = pd.concat(combined_data, ignore_index=True)
    all_servers_df['rank'] = all_servers_df.groupby("warzone")["totalhero"].rank(method="first", ascending=False)
    all_servers_df['rank'] = all_servers_df['rank'].astype(int)

    # Define points and line separately to make points larger
    server_line = alt.Chart(all_servers_df).mark_line().encode(
        x=alt.X("rank:O", sort="descending"),
        y=alt.Y("totalhero:Q"),
        color = alt.Color("warzone:N", title="Server", scale=alt.Scale(domain=st.session_state.whale_selected_servers))
    )
    server_points = alt.Chart(all_servers_df).mark_circle(size=60).encode(
        x=alt.X("rank:O", title="Top 200 - Total Hero Power", sort="descending"),
        y=alt.Y("totalhero:Q", title="Total Hero Power"),
        color = alt.Color("warzone:N", title="Server", scale=alt.Scale(domain=st.session_state.whale_selected_servers)),
        tooltip=['warzone','alliance','player','totalhero']
    ).properties(
        title=alt.TitleParams(text=f"Comparing Total Hero Power per Warzone", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    server_chart = server_line + server_points
    col.altair_chart(server_chart, use_container_width=True)
    return False

if __name__ == "__main__":
    print("==================================================")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    st.markdown("<h1 style='text-align: center; color: #3ea6ff; '>OLDs Lastwar Dashboard</h1>", unsafe_allow_html=True)
    st.write("")
    conn = db.create_connection(database)

    # Get all alliances and servers
    get_selection_data()

    chart_container = st.container()
    selection_container = st.container()
    with selection_container:
        multiselect_dropdown = render_selection_boxes(st)
    with chart_container:
        if st.session_state.whale_selected_servers:
            show_blank = print_server_chart(st, multiselect_dropdown)
        else:
            show_blank = True

        if show_blank == True:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)