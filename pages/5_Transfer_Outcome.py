import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a THP comparison chart for transfer gain/losses

#database = 'mySQL'
database = 'sqlite'
st.session_state.pre_transfer_date = '11/29/25'
st.session_state.post_transfer_date = '12/06/25'

# Callbacks for selection box updates
def on_servers_change():
    st.session_state.transfer_servers_choice = st.session_state.transferserver_multiselect_value
    st.session_state.all_check = False
def on_alliances_change():
    st.session_state.transfer_alliances_choice = st.session_state.transferalliance_multiselect_value
def on_metrictype_change():
    st.session_state.transfer_choice = st.session_state.transfer_selectbox_value
def all_checkbox():
    if st.session_state.all_warzones_check:
        st.session_state.transfer_servers_choice = st.session_state.server_region
        st.session_state.all_check = True
    else:
        st.session_state.all_check = False
        if "transfer_servers_choice" in st.session_state:
            del st.session_state["transfer_servers_choice"]

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'transfer_servers' not in st.session_state:
        server_query = "select distinct warzone from totalhero where date = '12/06/25' order by warzone"
        server_df = db.query_df(conn, server_query)
        st.session_state.server_region = server_df.iloc[:, 0].tolist()
        print("[INFO] Pulled servers from Database")
    if 'transfer_alliances' not in st.session_state:
        alliance_query = "select distinct alliance, sum(totalhero) as totalhero from totalhero where date = '12/06/25' group by alliance order by totalhero desc"
        alliance_df = db.query_df(conn, alliance_query)
        st.session_state.transfer_alliances = alliance_df.iloc[:, 0].tolist()
        print("[INFO] Pulled alliances from Database")

def render_selection_boxes(col):
    space1, sel1, sel2, check, space2 = col.columns([1, 6, 1, 1, 1])

    metrictype_options = ['Server','Alliance']
    if 'transfer_choice' not in st.session_state:
        st.session_state.transfer_choice = 'Alliance'
    if 'all_check' not in st.session_state:
        st.session_state.all_check = False

    if st.session_state.transfer_choice == 'Server':
        check.markdown("<div style='padding-top: 30px'> </div>", unsafe_allow_html=True)
        allcheck = check.checkbox(
            "All Warzones",
            value=st.session_state.all_check,
            key="all_warzones_check",
            on_change=all_checkbox
            )

    metrictype_dropdown = sel2.selectbox(
        "Metric Type",
        options=metrictype_options,
        key="transfer_selectbox_value",
        index=metrictype_options.index(st.session_state.transfer_choice), 
        on_change=on_metrictype_change
    )
    if st.session_state.transfer_choice == 'Server':
        if 'transfer_servers_choice' not in st.session_state:
            st.session_state.transfer_servers_choice = [1103,1104,1101,1098,1108]
        selected_servers = sel1.multiselect(
            "Select multiple servers",
            options=st.session_state.server_region,
            key="transferserver_multiselect_value",
            default=st.session_state.transfer_servers_choice,
            on_change=on_servers_change
        )
        return metrictype_dropdown, selected_servers
    elif st.session_state.transfer_choice == 'Alliance':
        if 'transfer_alliances_choice' not in st.session_state:
            st.session_state.transfer_alliances_choice = ['OLDs','KOUS','Ap3x','UsU','NXT','SRQ','SHUB','TAAF','Sif']
        selected_alliances = sel1.multiselect(
            "Select multiple alliances",
            options=st.session_state.transfer_alliances,
            key="transferalliance_multiselect_value",
            default=st.session_state.transfer_alliances_choice,
            on_change=on_alliances_change
        )
        return metrictype_dropdown, selected_alliances
    else:
        return None, None

def print_server_chart(col):
    combined_df = pd.DataFrame(columns=["warzone", "totalhero"])
    for server in st.session_state.transfer_servers_choice:
        if database == 'mySQL':
            server_query = "select date, sum(totalhero) from totalhero where warzone = %s and (date = %s or date = %s) group by date order by date"    
        else:
            server_query = f"select date, sum(totalhero) from totalhero where warzone = ? and (date = ? or date = ?) group by date order by date" # sqlite
        
        server_df = db.query_df(conn, server_query, [server, st.session_state.pre_transfer_date, st.session_state.post_transfer_date])
        if len(server_df) == 2:
            server_diff = server_df.iloc[1, 1] - server_df.iloc[0, 1]
            combined_df.loc[len(combined_df)] = [server, server_diff]
    print("[INFO] Pulled totalhero data from Database")

    # Return true if we need to print a blank chart
    if combined_df.empty:
        return True

    # Create server bar chart
    combined_df["totalhero"] = pd.to_numeric(combined_df["totalhero"])
    combined_df = combined_df.sort_values(by="totalhero", ascending=True)
    server_order = combined_df["warzone"].tolist()
    server_bar = alt.Chart(combined_df).mark_bar().encode(
        x=alt.X("warzone:N", title="Alliance", sort=server_order),
        y=alt.X("totalhero:Q", title="Top 200 - Total Hero Power"),
        color = alt.Color("warzone:N", title="Warzone", scale=alt.Scale(domain=st.session_state.transfer_servers_choice)),
        tooltip=["warzone", "totalhero"]
    ).properties(
        title=alt.TitleParams(text=f"Comparing Pre/Post Transfer per Warzone: Top 200 THP", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    col.altair_chart(server_bar, use_container_width=True)
    return False

def print_alliance_chart(col):
    combined_df = pd.DataFrame(columns=["alliance", "totalhero", "warzone"])
    for alliance in st.session_state.transfer_alliances_choice:
        # Get total server hero power for each date
        if database == 'mySQL':
            alliance_query = "select date, sum(totalhero), warzone from totalhero where alliance = %s and (date = %s or date = %s) group by date, warzone order by date"    
        else:
            alliance_query = f"select date, sum(totalhero), warzone from totalhero where alliance = ? and (date = ? or date = ?) group by date, warzone order by date" # sqlite
        
        alliance_df = db.query_df(conn, alliance_query, [alliance, st.session_state.pre_transfer_date, st.session_state.post_transfer_date])
        if len(alliance_df) == 2:

            alliance_diff = alliance_df.iloc[1, 1] - alliance_df.iloc[0, 1]
            warzone = alliance_df.iloc[0, 2]
            combined_df.loc[len(combined_df)] = [alliance, alliance_diff, warzone]
    print("[INFO] Pulled totalhero data from Database")

    # Return true if we need to print a blank chart
    if combined_df.empty:
        return True

    # Create alliance bar chart
    combined_df["totalhero"] = pd.to_numeric(combined_df["totalhero"])
    combined_df = combined_df.sort_values(by="totalhero", ascending=True)
    alliance_order = combined_df["alliance"].tolist()
    server_bar = alt.Chart(combined_df).mark_bar().encode(
        x=alt.X("alliance:N", title="Alliance", sort=alliance_order),
        y=alt.X("totalhero:Q", title="Top 200 - Total Hero Power"),
        color = alt.Color("alliance:N", title="Alliance", scale=alt.Scale(domain=st.session_state.transfer_alliances_choice)),
        tooltip=["warzone", "alliance", "totalhero"]
    ).properties(
        title=alt.TitleParams(text=f"Comparing Pre/Post Transfer per Alliance: Top 200 THP", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    col.altair_chart(server_bar, use_container_width=True)
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
        # Metrictype = server/alliance, select multiple of that type 
        metrictype_dropdown, multiselect_dropdown = render_selection_boxes(st)
    with chart_container:
        if metrictype_dropdown == 'Server' and st.session_state.transfer_servers_choice:
            show_blank = print_server_chart(st)
        elif metrictype_dropdown == 'Alliance' and st.session_state.transfer_alliances_choice:
            show_blank = print_alliance_chart(st)
        else:
            show_blank = True

        if show_blank == True:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)