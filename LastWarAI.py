import streamlit as st
import pandas as pd
import altair as alt
import sqlite3

# Goal:  Create a dashboard for visual Lastwar data analyis
# SQlite does not like %s, but wants ?
# connection = sqlite3.connect("lastwar.sqlite")
# Developed by Drew Clark 8/24/25

def create_connection():
    try:
        connection = sqlite3.connect("lastwar.sqlite")
        return connection
    except sqlite3.Error as e:
        print(f"[ERROR] {e}")
        return None

def disconnect(connection):
        connection.close()
        print("[INFO] Connection closed")

def query_df(conn, query, parms=()):
    cursor = conn.cursor()
    cursor.execute(query, parms)
    results = cursor.fetchall()
    df = pd.DataFrame(results)
    cursor.close()
    return df

# Callbacks for selection box updates
def on_week_change():
    st.session_state.week_choice = st.session_state.week_selectbox_value
def on_player_change():
    st.session_state.player_choice = st.session_state.player_selectbox_value

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 'weeks' not in st.session_state:
        week_query = "select distinct date from alliance_data where date != 'NaN' order by date"
        week_df = query_df(conn, week_query)
        st.session_state.weeks = week_df.iloc[:, 0].tolist()
        print("[INFO] Pulled weeks from Database")
    if 'players' not in st.session_state:
        player_query = "select distinct player from alliance_data order by player"
        player_df = query_df(conn, player_query)
        st.session_state.players = player_df.iloc[:, 0].tolist()
        print("[INFO] Pulled players from Database")

def render_selection_boxes(col):
    metric_dropdown = col.selectbox(
        "Metric",
        options=['power','kills','vs_points','donations'],
        index=2
    )
    if 'week_choice' not in st.session_state:
        # Get most recent week by default
        st.session_state.week_choice = st.session_state.weeks[-1]
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
    playerstats_query = "select olds_rank,power,kills,vs_points,donations from alliance_data where player =? and date = ?"
    playerstats_df = query_df(conn, playerstats_query, [st.session_state.player_choice, st.session_state.week_choice])
    columns = ['olds_rank', 'power', 'kills', 'vs_points', 'donations']
    if playerstats_df.empty:
        # create an empty dataframe with the correct columns
        playerstats_df = pd.DataFrame([[None]*len(columns)], columns=columns)
    else:
        playerstats_df.columns = columns

    playeravg_query = "select avg(vs_points) as vs_avg, avg(donations) as donation_avg from alliance_data where player = ? and date != 'NaN'"
    playeravg_df = query_df(conn, playeravg_query, [st.session_state.player_choice])
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
    alliancestats_query = "select sum(power), sum(kills), sum(vs_points), sum(donations) from alliance_data where date = ?"
    alliancestats_df = query_df(conn, alliancestats_query, [st.session_state.week_choice])
    alliancestats_df.columns = ['power', 'kills', 'vs_points', 'donations']

    allianceavg_query = "select avg(weekly_vs), avg(weekly_donate) from ( select `date`, sum(`vs_points`) as weekly_vs, sum(`donations`) as weekly_donate from alliance_data group by `date` ) as weekly_sums; "
    allianceavg_df = query_df(conn, allianceavg_query)
    allianceavg_df.columns = ['vs_avg', 'donation_avg']
    print("[INFO] Pulled alliance stats from Database")

    col.write("")
    col.header("Alliance Stats")
    col.markdown(f"##### Current Power:  :green[{alliancestats_df.at[0, 'power']:,}]")

    if alliancestats_df.at[0, 'kills'] is None:
        col.markdown(f"##### Current Kills:  :red[N/A]")
    else:
        col.markdown(f"##### Current Kills:  :green[{alliancestats_df.at[0, 'kills']:,}]")
    # orange if alliance vs points under avg
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
    query = f"select * from alliance_data where date = ? order by {metric} asc"
    df = query_df(conn, query, [date])
    df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']
    print("[INFO] Pulled alliance weekly data from Database")
    return df

def print_player_chart(col, player, metric):
    progress_query = f"select * from alliance_data where player = ? and date != 'NaN' order by date asc"
    player_df = query_df(conn, progress_query, [player])
    player_df.columns = ['olds_rank', 'player', 'date', 'power', 'kills', 'vs_points', 'donations']

    member_df = player_df[['date',metric]]
    
    player_chart = alt.Chart(member_df).mark_line(point=True).encode(
        x=alt.X('date', sort=member_df['date'].tolist()),  # maintain order
        y=metric
    ).properties(
        title=alt.TitleParams(text=f"Player {metric} per week", anchor='middle', fontSize=24)
    ).interactive()
    col.altair_chart(player_chart, use_container_width=True)

def print_alliance_data(col, df, metric):
    alliance_df = df[['player',metric]]
    alliance_df = alliance_df.copy()
    alliance_df['color'] = alliance_df['player'].apply(lambda x: 'green' if x == st.session_state.player_choice else '#1f77b4')
    alliance_chart = alt.Chart(alliance_df).mark_bar().encode(
        x=alt.X('player', sort=alliance_df['player'].tolist()),  # maintain order
        y=metric,
        color=alt.Color('color:N', scale=None)
    ).properties(
        title=alt.TitleParams(text=f"Alliance {metric} this week", anchor='middle', fontSize=24)
    ).interactive()
    col.altair_chart(alliance_chart, use_container_width=True)
    col.dataframe(df)

if __name__ == "__main__":
    # Set page config
    print("==================================================")
    #st.sidebar.title("Navigation")
    #st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    col1, col2 = st.columns([3, 1], gap="large", vertical_alignment="top")  # Wider left column for visuals
    conn = create_connection()

    # Print data for the right column
    col2.write("###")
    col2.header("Query Selection")
    get_selection_data()
    select1, select2 = col2.columns([2, 1])
    metric_dropdown, date_dropdown, player_dropdown = render_selection_boxes(select1)   ########## need to return those variables?
    print_playerstats(col2)
    print_alliancestats(col2)

    # Print data for the left column
    #col1.markdown("<h1 style='padding-left: 420px;'>Lastwar Dashboard</h1>", unsafe_allow_html=True)
    #col1.markdown("<h1 style='text-align: center; color: green; '>Lastwar Dashboard</h1>", unsafe_allow_html=True)
    dash1, dash2, dash3 = col1.columns([4, 4, 2])
    dash2.header(":blue[Lastwar Dashboard]")
    col1.write("")
    print_player_chart(col1, player_dropdown, metric_dropdown)
    alliance_df = weekly_alliance_data(metric_dropdown, date_dropdown)
    print_alliance_data(col1, alliance_df, metric_dropdown)

    disconnect(conn)