import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a player comparison chart
#           - User can select players to add from multiselect
#           - User can select a metric/date from selectbox

database = 'mySQL'
#database = 'sqlite'

# Callbacks for selection box updates
def on_players_change():
    st.session_state.selected_players = st.session_state.player_multiselect_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'players' not in st.session_state:
        player_query = "select distinct player from alliance_data order by player"
        player_df = db.query_df(conn, player_query)
        st.session_state.players = player_df.iloc[:, 0].tolist()
        print("[INFO] Pulled players from Database")

def render_selection_boxes(col):
    sel1, sel2, space1 = col.columns([6, 1, 3])
    metric_dropdown = sel2.selectbox(
        "Metric",
        options=['power','kills','vs_points','donations'],
        index=2
    )
    if 'selected_players' not in st.session_state:
        st.session_state.selected_players = ['DrewC125','Megan']
    selected_players = sel1.multiselect(
        "Select multiple players",
        options=st.session_state.players,
        key="player_multiselect_value",
        default=st.session_state.selected_players,
        on_change=on_players_change
    )
    return metric_dropdown, selected_players

def print_comparison_chart(col, metric):
    combined_data = []
    for player in st.session_state.selected_players:
        if database == 'mySQL':
            progress_query = "select * from alliance_data where player = %s and date != 'NaN' order by date asc"    
        else:
            progress_query = f"select * from alliance_data where player = ? and date != 'NaN' order by date asc" # sqlite
        
        player_df = db.query_df(conn, progress_query, [player])
        player_df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']

        combined_data.append(player_df[['date','player',metric]])
    
    all_players_df = pd.concat(combined_data, ignore_index=True)
    player_chart = alt.Chart(all_players_df).mark_line(point=True).encode(
        x=alt.X('date'),
        y=metric,
        color=alt.Color('player', title='Player'),
        tooltip=['player', 'date', metric]
    ).properties(
        title=alt.TitleParams(text=f"Comparing {metric} per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()
    col.altair_chart(player_chart, use_container_width=True)

if __name__ == "__main__":
    print("==================================================")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    conn = db.create_connection(database)

    st.markdown("<h1 style='text-align: center; color: #3ea6ff; '>Lastwar Dashboard</h1>", unsafe_allow_html=True)
    st.write("")
    get_selection_data()
    chart_container = st.container()
    selection_container = st.container()

    with selection_container:
        metric_dropdown, player_dropdown = render_selection_boxes(st)
    with chart_container:
        if st.session_state.selected_players:
            print_comparison_chart(st, metric_dropdown)
        else:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)