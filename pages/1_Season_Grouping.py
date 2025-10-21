import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a server/alliance comparison chart

#database = 'mySQL'
database = 'sqlite'

# Callbacks for selection box updates
def on_servers_change():
    st.session_state.selected_servers = st.session_state.server_multiselect_value
def on_alliances_change():
    st.session_state.selected_alliances = st.session_state.alliance_multiselect_value
def on_metrictype_change():
    st.session_state.herometric_choice = st.session_state.herometric_selectbox_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'servers' not in st.session_state:
        server_query = "select distinct warzone from totalhero order by warzone"
        server_df = db.query_df(conn, server_query)
        st.session_state.servers = server_df.iloc[:, 0].tolist()
        print("[INFO] Pulled servers from Database")
    if 'alliances' not in st.session_state:
        alliance_query = "select distinct alliance from totalhero order by alliance"
        alliance_df = db.query_df(conn, alliance_query)
        st.session_state.alliances = alliance_df.iloc[:, 0].tolist()
        print("[INFO] Pulled alliances from Database")

def render_selection_boxes(col):
    space1, sel1, sel2, space2 = col.columns([1, 6, 1, 2])

    metrictype_options = ['Server','Alliance']
    if 'herometric_choice' not in st.session_state:
        st.session_state.herometric_choice = 'Server'
    metrictype_dropdown = sel2.selectbox(
        "Metric Type",
        options=metrictype_options,
        key="herometric_selectbox_value",
        index=metrictype_options.index(st.session_state.herometric_choice), 
        on_change=on_metrictype_change
    )
    if st.session_state.herometric_choice == 'Server':
        if 'selected_servers' not in st.session_state:
            st.session_state.selected_servers = [1103,1104]
        selected_servers = sel1.multiselect(
            "Select multiple servers",
            options=st.session_state.servers,
            key="server_multiselect_value",
            default=st.session_state.selected_servers,
            on_change=on_servers_change
        )
        return metrictype_dropdown, selected_servers
    elif st.session_state.herometric_choice == 'Alliance':
        if 'selected_alliances' not in st.session_state:
            st.session_state.selected_alliances = ['OLDS','KOUS']
        selected_alliances = sel1.multiselect(
            "Select multiple alliances",
            options=st.session_state.alliances,
            key="alliance_multiselect_value",
            default=st.session_state.selected_alliances,
            on_change=on_alliances_change
        )
        return metrictype_dropdown, selected_alliances
    else:
        return None, None

def print_server_chart(col, metric):
    combined_data = []
    for server in st.session_state.selected_servers:
        if database == 'mySQL':
            server_query = "select * from totalhero where warzone = %s order by warzone asc"    
        else:
            server_query = f"select * from totalhero where warzone = ? order by warzone asc" # sqlite
        
        server_df = db.query_df(conn, server_query, [server])
        server_df.columns = ['date', 'warzone', 'alliance', 'player', 'totalhero']

        combined_data.append(server_df[['warzone','alliance','player','totalhero']])
    print("[INFO] Pulled totalhero data from Database")

    # Rank players for charting
    all_servers_df = pd.concat(combined_data, ignore_index=True)
    all_servers_df['rank'] = all_servers_df.groupby("warzone")["totalhero"].rank(method="first", ascending=False)
    all_servers_df['rank'] = all_servers_df['rank'].astype(int)

    # Define points and line separately to make points larger
    server_line = alt.Chart(all_servers_df).mark_line().encode(
        x=alt.X("rank:O", sort="descending"),
        y=alt.X("totalhero:Q"),
        color = alt.Color("warzone:N", title="Server", scale=alt.Scale(domain=st.session_state.selected_servers))
    )
    server_points = alt.Chart(all_servers_df).mark_circle(size=60).encode(
        x=alt.X("rank:O", title="Top 200 - Total Hero Power", sort="descending"),
        y=alt.X("totalhero:Q", title="Total Hero Power"),
        color = alt.Color("warzone:N", title="Server", scale=alt.Scale(domain=st.session_state.selected_servers)),
        tooltip=['warzone','alliance','player','totalhero']
    ).properties(
        title=alt.TitleParams(text=f"Comparing Total Hero Power per Warzone", anchor='middle', fontSize=24),
        height=800
    ).interactive()
    
    server_chart = server_line + server_points
    col.altair_chart(server_chart, use_container_width=True)

def print_alliance_chart(col, metric):
    combined_data = []
    for alliance in st.session_state.selected_alliances:
        if database == 'mySQL':
            alliance_query = "select * from totalhero where alliance = %s order by alliance asc"    
        else:
            alliance_query = f"select * from totalhero where alliance = ? order by alliance asc" # sqlite
        
        alliance_df = db.query_df(conn, alliance_query, [alliance])
        alliance_df.columns = ['date', 'warzone', 'alliance', 'player', 'totalhero']

        combined_data.append(alliance_df[['warzone','alliance','player','totalhero']])
    print("[INFO] Pulled totalhero data from Database")

    # Rank players for charting
    all_alliances_df = pd.concat(combined_data, ignore_index=True)
    all_alliances_df['rank'] = all_alliances_df.groupby("alliance")["totalhero"].rank(method="first", ascending=False)
    all_alliances_df['rank'] = all_alliances_df['rank'].astype(int)

    # Define points and line separately to make points larger
    server_line = alt.Chart(all_alliances_df).mark_line().encode(
        x=alt.X("rank:O", sort="descending"),
        y=alt.X("totalhero:Q"),
        color = alt.Color("alliance:N", title="Alliance", scale=alt.Scale(domain=st.session_state.selected_alliances))
    )
    server_points = alt.Chart(all_alliances_df).mark_circle(size=100).encode(
        x=alt.X("rank:O", title="Top 200 - Total Hero Power", sort="descending"),
        y=alt.X("totalhero:Q", title="Total Hero Power"),
        color = alt.Color("alliance:N", title="Alliance", scale=alt.Scale(domain=st.session_state.selected_alliances)),
        tooltip=['warzone','alliance','player','totalhero']
    ).properties(
        title=alt.TitleParams(text=f"Comparing Total Hero Power per Alliance", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    server_chart = server_line + server_points
    col.altair_chart(server_chart, use_container_width=True)

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
        if metrictype_dropdown == 'Server' and st.session_state.selected_servers:
            print_server_chart(st, multiselect_dropdown)
        elif metrictype_dropdown == 'Alliance' and st.session_state.selected_alliances:
            print_alliance_chart(st, multiselect_dropdown)
        else:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)