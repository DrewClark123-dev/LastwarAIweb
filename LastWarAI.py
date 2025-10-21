import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create a dashboard for visual Lastwar data analyis
# Developed by Drew Clark 8/24/25

#database = 'mySQL'
database = 'sqlite'

# Callbacks for selection box updates
def on_week_change():
    st.session_state.week_choice = st.session_state.week_selectbox_value
def on_player_change():
    st.session_state.player_choice = st.session_state.player_selectbox_value
def on_metric_change():
    st.session_state.metric_choice = st.session_state.metric_selectbox_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'weeks' not in st.session_state:
        week_query = "select distinct date from alliance_data where date != 'NaN' order by date desc"
        week_df = db.query_df(conn, week_query)
        st.session_state.weeks = week_df.iloc[:, 0].tolist()
        print("[INFO] Pulled weeks from Database")
    if 'players' not in st.session_state:
        player_query = "select distinct player from alliance_data order by player"
        player_df = db.query_df(conn, player_query)
        st.session_state.players = player_df.iloc[:, 0].tolist()
        print("[INFO] Pulled players from Database")

def render_selection_boxes(col):
    metric_options = ['power','kills','vs_points','donations']
    if 'metric_choice' not in st.session_state:
        st.session_state.metric_choice = 'power'
    metric_dropdown = col.selectbox(
        "Metric",
        options=metric_options,
        key="metric_selectbox_value",
        index=metric_options.index(st.session_state.metric_choice), 
        on_change=on_metric_change
    )
    if 'week_choice' not in st.session_state:
        # Get most recent week by default
        st.session_state.week_choice = st.session_state.weeks[0]
    date_dropdown = col.selectbox(
        "Date",
        options=st.session_state.weeks,
        key="week_selectbox_value",
        index=st.session_state.weeks.index(st.session_state.week_choice),
        on_change=on_week_change
    )
    if 'player_choice' not in st.session_state:
        st.session_state.player_choice = 'DrewC125'
    player_dropdown = col.selectbox(
        "Player",
        options=st.session_state.players,
        key="player_selectbox_value",
        index=st.session_state.players.index(st.session_state.player_choice),
        on_change=on_player_change
    )
    return metric_dropdown, date_dropdown, player_dropdown

# Query DB for player statistics, print to a column
def print_playerstats(col):
    
    if database == 'mySQL':
        playerstats_query = "select olds_rank,power,kills,vs_points,donations from alliance_data where player = %s and date = %s"
    else:
        playerstats_query = "select olds_rank,power,kills,vs_points,donations from alliance_data where player = ? and date = ?"  # sqlite

    playerstats_df = db.query_df(conn, playerstats_query, [st.session_state.player_choice, st.session_state.week_choice])
    columns = ['olds_rank', 'power', 'kills', 'vs_points', 'donations']
    if playerstats_df.empty:
        # create an empty dataframe with the correct columns
        playerstats_df = pd.DataFrame([[None]*len(columns)], columns=columns)
    else:
        playerstats_df.columns = columns

    if database == 'mySQL':
        playeravg_query = "select avg(vs_points) as vs_avg, avg(donations) as donation_avg from alliance_data where player = %s and date != 'NaN'"
    else:
        playeravg_query = "select avg(vs_points) as vs_avg, avg(donations) as donation_avg from alliance_data where player = ? and date != 'NaN'"
    
    playeravg_df = db.query_df(conn, playeravg_query, [st.session_state.player_choice])
    columns = ['vs_avg', 'donation_avg']
    if playeravg_df.empty:
        # create an empty dataframe with the correct columns
        playeravg_df = pd.DataFrame([[None]*len(columns)], columns=columns)
    else:
        playeravg_df.columns = columns
    print("[INFO] Pulled player stats from Database")

    col.write("")
    col.header("Player Stats")

    #print(playerstats_df)
    if playerstats_df.at[0, 'power'] is None:
        col.markdown(f"##### Current Power:  :red[N/A]")
    elif playerstats_df.at[0, 'power']/1000000 < 100:
        col.markdown(f"##### Current Power:  :red[{playerstats_df.at[0, 'power']:,}]")
    elif playerstats_df.at[0, 'power']/1000000 < 120:
        col.markdown(f"##### Current Power:  :orange[{playerstats_df.at[0, 'power']:,}]")
    else:
        col.markdown(f"##### Current Power:  :green[{playerstats_df.at[0, 'power']:,}]")

    if playerstats_df.at[0, 'kills'] is None:
        col.markdown(f"##### Current Kills:  :red[N/A]")
    elif playerstats_df.at[0, 'kills']/1000000 < 1:
        col.markdown(f"##### Current Kills:  :red[{playerstats_df.at[0, 'kills']:,}]")
    elif playerstats_df.at[0, 'kills']/1000000 < 2:
        col.markdown(f"##### Current Kills:  :orange[{playerstats_df.at[0, 'kills']:,}]")
    else:
        col.markdown(f"##### Current Kills:  :green[{playerstats_df.at[0, 'kills']:,}]")

    if playerstats_df.at[0, 'vs_points'] is None:
        col.markdown(f"##### Weekly VS Points:  :red[N/A]")
    elif playerstats_df.at[0, 'vs_points']/1000000 < 42:
        col.markdown(f"##### Weekly VS Points:  :red[{playerstats_df.at[0, 'vs_points']:,}]")
    elif playerstats_df.at[0, 'vs_points']/1000000 < 50:
        col.markdown(f"##### Weekly VS Points:  :orange[{playerstats_df.at[0, 'vs_points']:,}]")
    else:
        col.markdown(f"##### Weekly VS Points:  :green[{playerstats_df.at[0, 'vs_points']:,}]")

    if playerstats_df.at[0, 'donations'] is None:
        col.markdown(f"##### Weekly Donations:  :red[N/A]")
    elif playerstats_df.at[0, 'donations']/1000 < 30:
        col.markdown(f"##### Weekly Donations:  :red[{playerstats_df.at[0, 'donations']:,}]")
    elif playerstats_df.at[0, 'donations']/1000 < 35:
        col.markdown(f"##### Weekly Donations:  :orange[{playerstats_df.at[0, 'donations']:,}]")
    else:
        col.markdown(f"##### Weekly Donations:  :green[{playerstats_df.at[0, 'donations']:,}]")

    if playeravg_df.at[0, 'vs_avg'] is None:
        col.markdown(f"##### Avg VS Points:  :red[N/A]")
    elif playeravg_df.at[0, 'vs_avg']/1000000 < 42:
        col.markdown(f"##### Avg VS Points:  :red[{int(playeravg_df.at[0, 'vs_avg']):,}]")
    elif playeravg_df.at[0, 'vs_avg']/1000000 < 50:
        col.markdown(f"##### Avg VS Points:  :orange[{int(playeravg_df.at[0, 'vs_avg']):,}]")
    else:
        col.markdown(f"##### Avg VS Points:  :green[{int(playeravg_df.at[0, 'vs_avg']):,}]")

    if playeravg_df.at[0, 'donation_avg'] is None:
        col.markdown(f"##### Avg Donations:  :red[N/A]")
    elif playeravg_df.at[0, 'donation_avg']/1000 < 30:
        col.markdown(f"##### Avg Donations:  :red[{int(playeravg_df.at[0, 'donation_avg']):,}]")
    elif playeravg_df.at[0, 'donation_avg']/1000 < 35:
        col.markdown(f"##### Avg Donations:  :orange[{int(playeravg_df.at[0, 'donation_avg']):,}]")
    else:
        col.markdown(f"##### Avg Donations:  :green[{int(playeravg_df.at[0, 'donation_avg']):,}]")

def print_alliancestats(col):
    if database == 'mySQL':
        alliancestats_query = "select sum(power), sum(kills), sum(vs_points), sum(donations) from alliance_data where date = %s"
    else:
        alliancestats_query = "select sum(power), sum(kills), sum(vs_points), sum(donations) from alliance_data where date = ?" # sqlite
    
    alliancestats_df = db.query_df(conn, alliancestats_query, [st.session_state.week_choice])
    alliancestats_df.columns = ['power', 'kills', 'vs_points', 'donations']

    allianceavg_query = "select avg(weekly_vs), avg(weekly_donate) from ( select `date`, sum(`vs_points`) as weekly_vs, sum(`donations`) as weekly_donate from alliance_data group by `date` ) as weekly_sums; "
    allianceavg_df = db.query_df(conn, allianceavg_query)
    allianceavg_df.columns = ['vs_avg', 'donation_avg']
    print("[INFO] Pulled alliance stats from Database")

    col.write("")
    col.header("Alliance Stats")
    col.markdown(f"##### Current Power:  :green[{alliancestats_df.at[0, 'power']:,}]")

    if alliancestats_df.at[0, 'kills'] is None:
        col.markdown(f"##### Current Kills:  :red[N/A]")
    else:
        col.markdown(f"##### Current Kills:  :green[{alliancestats_df.at[0, 'kills']:,}]")
    # orange if alliance metric under avg
    if alliancestats_df.at[0, 'vs_points'] < allianceavg_df.at[0, 'vs_avg']:
        col.markdown(f"##### Weekly VS Points:  :orange[{alliancestats_df.at[0, 'vs_points']:,}]")
    else:
        col.markdown(f"##### Weekly VS Points:  :green[{alliancestats_df.at[0, 'vs_points']:,}]")
    if alliancestats_df.at[0, 'donations'] < allianceavg_df.at[0, 'donation_avg']:
        col.markdown(f"##### Weekly Donations:  :orange[{alliancestats_df.at[0, 'donations']:,}]")
    else:
        col.markdown(f"##### Weekly Donations:  :green[{alliancestats_df.at[0, 'donations']:,}]")
    col.markdown(f"##### Avg VS Points:  :blue[{int(allianceavg_df.at[0, 'vs_avg']):,}]")
    col.markdown(f"##### Avg Donations:  :blue[{int(allianceavg_df.at[0, 'donation_avg']):,}]")

def weekly_alliance_data(metric, date):
    if database == 'mySQL':
        query = f"select * from alliance_data where date = %s order by {metric} asc"  
    else:
        query = f"select * from alliance_data where date = ? order by {metric} asc" # sqlite
    
    df = db.query_df(conn, query, [date])
    df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']
    print("[INFO] Pulled alliance weekly data from Database")
    return df

def print_player_chart(col, player, metric):
    if database == 'mySQL':
        progress_query = "select * from alliance_data where player = %s and date != 'NaN' order by date asc"    
    else:
        progress_query = f"select * from alliance_data where player = ? and date != 'NaN' order by date asc" # sqlite
    
    player_df = db.query_df(conn, progress_query, [player])
    player_df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']

    member_df = player_df[['date',metric]]

    # Define points and line separately to make points larger
    player_line = alt.Chart(member_df).mark_line().encode(
        x=alt.X("date", sort=list(member_df['date'].tolist())),
        y=metric,
    )
    player_points = alt.Chart(member_df).mark_circle(size=150).encode(
        x=alt.X('date', sort=member_df['date'].tolist()),  # maintain order
        y=metric
    ).properties(
        title=alt.TitleParams(text=f"{player} {metric} per week", anchor='middle', fontSize=24)
    ).interactive()

    player_chart = player_line + player_points
    col.altair_chart(player_chart, use_container_width=True)

def print_alliance_data(col, df, metric):
    alliance_df = df[['player',metric]]
    alliance_df = alliance_df.copy()
    alliance_df['color'] = alliance_df['player'].apply(lambda x: '#00e676' if x == st.session_state.player_choice else '#3ea6ff')
    alliance_chart = alt.Chart(alliance_df).mark_bar().encode(
        x=alt.X('player', sort=alliance_df['player'].tolist()),  # maintain order
        y=metric,
        color=alt.Color('color:N', scale=None)
    ).properties(
        title=alt.TitleParams(text=f"Alliance {metric} on {df['date'].iloc[0]}", anchor='middle', fontSize=24)
    ).interactive()
    col.altair_chart(alliance_chart, use_container_width=True)
    col.dataframe(df)

if __name__ == "__main__":
    # Set page config
    print("==================================================")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    col1, col2 = st.columns([3, 1], gap="large", vertical_alignment="top")
    conn = db.create_connection(database)

    # Print data for the right column
    col2.write("###")
    col2.header("Query Selection")
    get_selection_data()
    select1, select2 = col2.columns([2, 1])
    metric_dropdown, date_dropdown, player_dropdown = render_selection_boxes(select1)
    print_playerstats(col2)
    print_alliancestats(col2)

    # Print data for the left column
    col1.markdown("<h1 style='text-align: center; color: #3ea6ff; '>OLDs Lastwar Dashboard</h1>", unsafe_allow_html=True)
    col1.write("")
    print_player_chart(col1, player_dropdown, metric_dropdown)
    alliance_df = weekly_alliance_data(metric_dropdown, date_dropdown)
    print_alliance_data(col1, alliance_df, metric_dropdown)

    db.disconnect(conn)