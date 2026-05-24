import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a player comparison chart
#           - User can select players to add from multiselect
#           - User can select a metric/date from selectbox

#database = 'mySQL'
database = 'sqlite'
pd.set_option('display.max_rows', None)

# Callbacks for selection box updates
def on_players_change():
    st.session_state.selected_players = st.session_state.player_multiselect_value
def on_metric_change():
    st.session_state.metric_choice = st.session_state.metric_selectbox_value
def on_metrictype_change():
    st.session_state.metrictype_choice = st.session_state.metrictype_selectbox_value
def on_delta_change():
    st.session_state.delta_choice = st.session_state.delta_toggle_value
def on_weeks_slider_change():
    st.session_state.aa_weeks_slider_choice = st.session_state.aa_weeks_slider_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'players' not in st.session_state:
        player_query = "select distinct player from alliance_data order by player"
        player_df = db.query_df(conn, player_query)
        st.session_state.players = player_df.iloc[:, 0].tolist()
        print("[INFO] Pulled players from Database")
    if 'weeks' not in st.session_state:
        week_query = "select distinct date from alliance_data where date != 'NaN' order by substr(date, 7, 2) || '-' || substr(date, 1, 2) || '-' || substr(date, 4, 2) desc"
        week_df = db.query_df(conn, week_query)
        st.session_state.weeks = week_df.iloc[:, 0].tolist()
        print("[INFO] Pulled weeks from Database")

def render_selection_boxes(col):
    space1, sel1, metrics_col, delta_col = col.columns([1, 6, 2, 2])
    sel2, sel3 = metrics_col.columns(2)

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
        st.session_state.selected_players = ['Drewski','Megan']
    selected_players = sel1.multiselect(
        "Select multiple players",
        options=st.session_state.players,
        key="player_multiselect_value",
        default=st.session_state.selected_players,
        on_change=on_players_change
    )
    n_weeks = max(1, len(st.session_state.weeks))
    if 'aa_weeks_slider_choice' not in st.session_state:
        st.session_state.aa_weeks_slider_choice = n_weeks
    weeks_slider = metrics_col.slider(
        "Last N Weeks (Chart)",
        min_value=1,
        max_value=n_weeks,
        value=st.session_state.aa_weeks_slider_choice,
        key="aa_weeks_slider_value",
        on_change=on_weeks_slider_change
    )
    if 'delta_choice' not in st.session_state:
        st.session_state.delta_choice = False
    delta_col.markdown("<div style='padding-top: 36px'></div>", unsafe_allow_html=True)
    delta_toggle = delta_col.toggle(
        "Delta",
        key="delta_toggle_value",
        value=st.session_state.delta_choice,
        on_change=on_delta_change
    )
    return metrictype_dropdown, metric_dropdown, selected_players, delta_toggle, weeks_slider

def print_comparison_chart(col, metric, delta=False, last_n=None):
    combined_data = []
    for player in st.session_state.selected_players:
        if database == 'mySQL':
            progress_query = "select * from alliance_data where player = %s and date != 'NaN'"    
        else:
            progress_query = "select * from alliance_data where player = ? and date != 'NaN'"
        
        player_df = db.query_df(conn, progress_query, [player])
        player_df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']

        # Convert to datetime, sort, then convert back to string mm/dd/yy
        player_df['date'] = pd.to_datetime(player_df['date'], format='%m/%d/%y', errors='coerce')
        player_df = player_df.sort_values('date')
        player_df['date'] = player_df['date'].dt.strftime('%m/%d/%y')

        if delta:
            player_df[metric] = player_df[metric].diff()
            player_df = player_df.dropna(subset=[metric])

        combined_data.append(player_df[['date','player',metric]])
    
    print("[INFO] Pulled player data from Database")
    all_players_df = pd.concat(combined_data, ignore_index=True)

    # Convert unique dates to datetime, sort, then convert back to string mm/dd/yy
    x_dates = all_players_df['date'].drop_duplicates()
    x_dates = pd.to_datetime(x_dates, format='%m/%d/%y', errors='coerce')
    x_dates = x_dates.sort_values()
    x_dates = x_dates.dt.strftime('%m/%d/%y')
    if last_n is not None:
        x_dates = x_dates.iloc[-last_n:]
        all_players_df = all_players_df[all_players_df['date'].isin(x_dates)]

    # Define points and line separately to make points larger
    player_line = alt.Chart(all_players_df).mark_line().encode(
        x=alt.X("date:O", axis=alt.Axis(labelAngle=-90), sort=x_dates),
        y=metric,
        color=alt.Color(
            'player',
            title='Player',
            scale=alt.Scale(domain=st.session_state.selected_players)
        )
    )
    player_points = alt.Chart(all_players_df).mark_circle(size=150).encode(
        x=alt.X('date:O', axis=alt.Axis(labelAngle=-90), sort=x_dates),
        y=metric,
        color=alt.Color(
            'player',
            title='Player',
            scale=alt.Scale(domain=st.session_state.selected_players)
        ),
        tooltip=['player', alt.Tooltip('date:O'), metric]
    ).properties(
        title=alt.TitleParams(text=f"Weekly Change in {metric}" if delta else f"Comparing {metric} per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    player_chart = player_line + player_points
    col.altair_chart(player_chart, width='stretch')

    _, btn_col, _ = col.columns([1, 8, 2])
    btn_col.download_button(
        "Download CSV",
        data=all_players_df.to_csv(index=False),
        file_name=f"player_{metric}_data.csv",
        mime="text/csv"
    )

    if len(x_dates) >= 2:
        latest = x_dates.iloc[-1]
        prev = x_dates.iloc[-2]
        curr_df = all_players_df[all_players_df['date'] == latest][['player', metric]].rename(columns={metric: 'current'})
        prev_df = all_players_df[all_players_df['date'] == prev][['player', metric]].rename(columns={metric: 'previous'})
        delta_df = curr_df.merge(prev_df, on='player', how='left')
        delta_df['delta'] = delta_df['current'] - delta_df['previous']
        delta_df = delta_df.sort_values('delta', ascending=False).set_index('player')
        _, expander_col, _ = col.columns([1, 8, 2])
        with expander_col.expander(f"Week-over-Week Changes  ({prev} → {latest})"):
            st.dataframe(delta_df.style.format("{:,.0f}"))

def print_alliance_chart(col, metric, delta=False, last_n=None):
    if database == 'mySQL':
        alliance_query = f"select date, sum({metric}) from alliance_data where date != 'NaN' group by date order by STR_TO_DATE(date, '%m/%d/%y') asc;"
    else:
        alliance_query = f"select date, sum({metric}) from alliance_data where date != 'NaN' group by date order by substr(date, 7, 2) || '-' || substr(date, 1, 2) || '-' || substr(date, 4, 2) asc;"
    alliance_df = db.query_df(conn, alliance_query)
    alliance_df.columns = ['date', metric]
    alliance_df[metric] = alliance_df[metric].astype(float)
    if delta:
        alliance_df[metric] = alliance_df[metric].diff()
        alliance_df = alliance_df.dropna(subset=[metric])
    if last_n is not None:
        alliance_df = alliance_df.iloc[-last_n:]
    x_dates = alliance_df['date'].drop_duplicates().tolist()
    print("[INFO] Pulled alliance data from Database")

    # Define points and line separately to make points larger
    alliance_line = alt.Chart(alliance_df).mark_line().encode(
        x=alt.X("date:O", axis=alt.Axis(labelAngle=-90), sort=x_dates),
        y=metric,
    )
    alliance_points = alt.Chart(alliance_df).mark_circle(size=150).encode(
        x=alt.X("date:O", axis=alt.Axis(labelAngle=-90), sort=x_dates),
        y=metric,
        tooltip=[metric, 'date']
    ).properties(
        title=alt.TitleParams(text=f"Alliance Weekly Change in {metric}" if delta else f"Alliance {metric} per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    alliance_chart = alliance_line + alliance_points
    col.altair_chart(alliance_chart, width='stretch')

    col.download_button(
        "Download CSV",
        data=alliance_df.to_csv(index=False),
        file_name=f"alliance_{metric}_data.csv",
        mime="text/csv"
    )

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
        metrictype_dropdown, metric_dropdown, player_dropdown, delta_toggle, weeks_slider = render_selection_boxes(st)
    with chart_container:
        if metrictype_dropdown == 'Player' and st.session_state.selected_players:
            print_comparison_chart(st, metric_dropdown, delta_toggle, last_n=weeks_slider)
        elif metrictype_dropdown == 'Alliance':
            print_alliance_chart(st, metric_dropdown, delta_toggle, last_n=weeks_slider)
        else:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)