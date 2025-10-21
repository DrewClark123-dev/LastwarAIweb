import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a player comparison chart
#           - User can select players to add from multiselect
#           - User can select a metric/date from selectbox

#database = 'mySQL'
database = 'sqlite'

# Callbacks for selection box updates
def on_players_change():
    st.session_state.selected_players = st.session_state.player_multiselect_value
def on_metric_change():
    st.session_state.metric_choice = st.session_state.metric_selectbox_value
def on_metrictype_change():
    st.session_state.metrictype_choice = st.session_state.metrictype_selectbox_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'players' not in st.session_state:
        player_query = "select distinct player from alliance_data order by player"
        player_df = db.query_df(conn, player_query)
        st.session_state.players = player_df.iloc[:, 0].tolist()
        print("[INFO] Pulled players from Database")

def render_selection_boxes(col):
    space1, sel1, sel2, sel3, space2 = col.columns([1, 6, 1, 1, 2])
    metric_options = ['power','kills','vs_points','donations']
    if 'metric_choice' not in st.session_state:
        st.session_state.metric_choice = 'power'
    metric_dropdown = sel2.selectbox(
        "Metric",
        options=metric_options,
        key="metric_selectbox_value",
        index=metric_options.index(st.session_state.metric_choice), 
        on_change=on_metric_change
    )
    metrictype_options = ['Player','Alliance']
    if 'metrictype_choice' not in st.session_state:
        st.session_state.metrictype_choice = 'Player'
    metrictype_dropdown = sel3.selectbox(
        "Metric Type",
        options=metrictype_options,
        key="metrictype_selectbox_value",
        index=metrictype_options.index(st.session_state.metrictype_choice), 
        on_change=on_metrictype_change
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
    return metrictype_dropdown, metric_dropdown, selected_players

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
    
    print("[INFO] Pulled player data from Database")
    all_players_df = pd.concat(combined_data, ignore_index=True)


    # Define points and line separately to make points larger
    player_line = alt.Chart(all_players_df).mark_line().encode(
        x=alt.X("date"),
        y=metric,
        color=alt.Color(
            'player',
            title='Player',
            scale=alt.Scale(domain=st.session_state.selected_players)
        )
    )
    player_points = alt.Chart(all_players_df).mark_circle(size=150).encode(
        x=alt.X('date'),
        y=metric,
        color=alt.Color(
            'player',
            title='Player',
            scale=alt.Scale(domain=st.session_state.selected_players)
        ),
        tooltip=['player', 'date', metric]
    ).properties(
        title=alt.TitleParams(text=f"Comparing {metric} per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    player_chart = player_line + player_points
    col.altair_chart(player_chart, use_container_width=True)

def print_alliance_chart(col, metric):
    alliance_query = f"select date, sum({metric}) from alliance_data where date != 'NaN' group by date;"    
    alliance_df = db.query_df(conn, alliance_query)
    alliance_df.columns = ['date', metric]
    alliance_df[metric] = alliance_df[metric].astype(float)
    print("[INFO] Pulled alliance data from Database")

    # Define points and line separately to make points larger
    alliance_line = alt.Chart(alliance_df).mark_line().encode(
        x=alt.X("date"),
        y=metric,
    )
    alliance_points = alt.Chart(alliance_df).mark_circle(size=150).encode(
        x=alt.X('date'),
        y=metric,
        tooltip=[metric, 'date']
    ).properties(
        title=alt.TitleParams(text=f"Alliance {metric} per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    alliance_chart = alliance_line + alliance_points
    col.altair_chart(alliance_chart, use_container_width=True)

if __name__ == "__main__":
    print("==================================================")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    conn = db.create_connection(database)

    st.markdown("<h1 style='text-align: center; color: #3ea6ff; '>OLDs Lastwar Dashboard</h1>", unsafe_allow_html=True)
    st.write("")
    get_selection_data()
    chart_container = st.container()
    selection_container = st.container()

    with selection_container:
        metrictype_dropdown, metric_dropdown, player_dropdown = render_selection_boxes(st)
    with chart_container:
        if metrictype_dropdown == 'Player' and st.session_state.selected_players:
            print_comparison_chart(st, metric_dropdown)
        elif metrictype_dropdown == 'Alliance':
            print_alliance_chart(st, metric_dropdown)
        else:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)