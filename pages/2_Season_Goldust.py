import streamlit as st
import pandas as pd
import altair as alt
import src.db as db

# Goal:  Create Season 3 Goldust comparison charts

#database = 'mySQL'
database = 'sqlite'

# Callbacks for selection box updates
def on_alliances_change():
    st.session_state.goldust_alliances = st.session_state.timeline_multiselect_value
def on_metrictype_change():
    st.session_state.goldustmetric_choice = st.session_state.goldustmetric_selectbox_value
def on_dates_change():
    st.session_state.goldust_date = st.session_state.s3date_multiselect_value 
def update_checkbox():
    st.session_state.goldust_check = st.session_state.gold_faction

# Get unique players,dates from db, cache them, show them in dropdown
def get_selection_data():
    if 's3alliances' not in st.session_state:
        alliance_query = "select distinct alliance from s3goldust"
        alliance_df = db.query_df(conn, alliance_query)
        st.session_state.s3alliances = alliance_df.iloc[:, 0].tolist()
        print("[INFO] Pulled alliances from Database")
    if 's3dates' not in st.session_state:
        date_query = "select distinct date from s3goldust order by date desc"
        date_df = db.query_df(conn, date_query)
        st.session_state.s3dates = date_df.iloc[:, 0].tolist()
        print("[INFO] Pulled dates from Database")

def render_selection_boxes(col):
    space1, sel1, sel2, sel3, check, space2 = col.columns([1, 6, 1, 1, 1, 1])


    # Set default as Current
    metrictype_options = ['Current','Timeline']
    if 'goldustmetric_choice' not in st.session_state:
        st.session_state.goldustmetric_choice = 'Current'

    # Don't show Faction checkmark for timeline
    if st.session_state.goldustmetric_choice == 'Current':
        if 'goldust_check' not in st.session_state:
            st.session_state.goldust_check = True
        check.markdown("<div style='padding-top: 30px'> </div>", unsafe_allow_html=True)
        faction_check = check.checkbox(
            "Faction",
            value=st.session_state.goldust_check,
            key="gold_faction",
            on_change=update_checkbox
            )

    metrictype_dropdown = sel2.selectbox(
        "Metric Type",
        options=metrictype_options,
        key="goldustmetric_selectbox_value",
        index=metrictype_options.index(st.session_state.goldustmetric_choice), 
        on_change=on_metrictype_change
    )
    if st.session_state.goldustmetric_choice == 'Current':
        if 'goldust_alliances' not in st.session_state:
            # This wont work if OCR reads alliance names wrong...
            st.session_state.goldust_alliances = ['OLDs','KOUS','SiNS','ASHH','NatA','Bytl','SHT1','baek']
        goldust_alliances = sel1.multiselect(
            "Select multiple alliances",
            options=st.session_state.s3alliances,
            key="timeline_multiselect_value",
            default=st.session_state.goldust_alliances,
            on_change=on_alliances_change
        )
        if 'goldust_date' not in st.session_state:
            date_query = "select max(date) from s3goldust"
            date_df = db.query_df(conn, date_query)
            st.session_state.goldust_date =  date_df.iloc[0, 0]   # first row, first column
        goldust_date = sel3.selectbox(
            "Date",
            options=st.session_state.s3dates,
            key="s3date_multiselect_value",
            index=st.session_state.s3dates.index(st.session_state.goldust_date), 
            on_change=on_dates_change
        )
        return metrictype_dropdown, goldust_alliances

    elif st.session_state.goldustmetric_choice == 'Timeline':
        if 'goldust_alliances' not in st.session_state:
            st.session_state.goldust_alliances = ['OLDS','KOUS']
        goldust_alliances = sel1.multiselect(
            "Select multiple alliances",
            options=st.session_state.s3alliances,
            key="timeline_multiselect_value",
            default=st.session_state.goldust_alliances,
            on_change=on_alliances_change
        )
        return metrictype_dropdown, goldust_alliances
    else:
        return None, None

def assign_faction(row):
    golden_tribe = [1104,1095,1124,1103]
    scarlet_legion = [1097,1115,1093,1113]

    if row['alliance'] in st.session_state.goldust_alliances:
        return 'Selected'
    elif row['warzone'] in scarlet_legion:
        return 'Scarlet Legion'
    elif row['warzone'] in golden_tribe:
        return 'Golden Tribe'
    else:
        return 'Other'

def print_current_chart(col):
    if database == 'mySQL':
        current_query = "select * from s3goldust where date = %s order by goldust desc"    
    else:
        current_query = f"select * from s3goldust where date = ? order by goldust desc" # sqlite

    current_df = db.query_df(conn, current_query, [st.session_state.goldust_date])
    current_df.columns = ['date', 'warzone', 'alliance', 'goldust']
    print("[INFO] Pulled current goldust data from Database")

    # Rank players for charting
    current_df['rank'] = current_df['goldust'].rank(method='dense', ascending=True).astype(int)
    current_df = current_df.sort_values('rank')

    # Add faction to DF
    current_df['faction'] = current_df.apply(assign_faction, axis=1)

    # Make factions red
    if st.session_state.goldust_check:
        # Define points and line separately to make points larger
        current_line = alt.Chart(current_df).mark_line().encode(
            x=alt.X("alliance:O", sort=list(current_df['alliance'])),
            y=alt.Y("goldust:Q"),
        )
        current_points = alt.Chart(current_df).mark_circle(size=150).encode(
            x=alt.X("alliance:O", title="Goldust Rank", sort=list(current_df['alliance'])),
            y=alt.Y("goldust:Q", title="Season 3 Goldust"),
            color=alt.Color(
                'faction:N', 
                scale=alt.Scale(
                    domain=['Golden Tribe', 'Scarlet Legion', 'Selected'],
                    range=['#3ea6ff', '#e60000', '#e6e200']  # colors you used
                ),
                legend=alt.Legend(title="Faction")
            ),
            tooltip=['warzone','alliance','goldust']
        ).properties(
            title=alt.TitleParams(text=f"Season 3 Goldust Rankings", anchor='middle', fontSize=24),
            height=800
        ).interactive()

    else:
        current_df['color'] = current_df['alliance'].apply(lambda x: "#e6e200" if x in st.session_state.goldust_alliances else '#3ea6ff')

        # Define points and line separately to make points larger
        current_line = alt.Chart(current_df).mark_line().encode(
            x=alt.X("alliance:O", sort=list(current_df['alliance'])),
            y=alt.Y("goldust:Q"),
        )
        current_points = alt.Chart(current_df).mark_circle(size=150).encode(
            x=alt.X("alliance:O", title="Goldust Rank", sort=list(current_df['alliance'])),
            y=alt.Y("goldust:Q", title="Season 3 Goldust"),
            color=alt.Color('color:N', scale=None),
            tooltip=['warzone','alliance','goldust']
        ).properties(
            title=alt.TitleParams(text=f"Season 3 Goldust Rankings", anchor='middle', fontSize=24),
            height=800
        ).interactive()

    current_chart = current_line + current_points
    col.altair_chart(current_chart, use_container_width=True)

def print_timeline_chart(col):
    combined_data = []
    for alliance in st.session_state.goldust_alliances:
        if database == 'mySQL':
            alliance_query = "select * from s3goldust where alliance = %s order by date asc"    
        else:
            alliance_query = f"select * from s3goldust where alliance = ? order by date asc" # sqlite
        
        alliance_df = db.query_df(conn, alliance_query, [alliance])
        alliance_df.columns = ['date', 'warzone', 'alliance', 'goldust']
        combined_data.append(alliance_df[['date', 'warzone', 'alliance', 'goldust']])
    print("[INFO] Pulled s3goldust data from Database")

    # Rank players for charting
    timeline_df = pd.concat(combined_data, ignore_index=True)
    timeline_df['rank'] = timeline_df.groupby("alliance")["goldust"].rank(method="first", ascending=False)

    # Define points and line separately to make points larger
    timeline_line = alt.Chart(timeline_df).mark_line().encode(
        x=alt.X("date:O", sort="ascending"),
        y=alt.X("goldust:Q"),
        color = alt.Color("alliance:N", title="Alliance", scale=alt.Scale(domain=st.session_state.goldust_alliances))
    )
    timeline_points = alt.Chart(timeline_df).mark_circle(size=150).encode(
        x=alt.X("date:O", title="Season 3 Week", sort="ascending"),
        y=alt.X("goldust:Q", title="Season 3 Goldust"),
        color = alt.Color("alliance:N", title="Alliance", scale=alt.Scale(domain=st.session_state.goldust_alliances)),
        tooltip=['warzone','alliance','goldust']
    ).properties(
        title=alt.TitleParams(text=f"Comparing Season 3 Goldust per week", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    timeline_chart = timeline_line + timeline_points
    col.altair_chart(timeline_chart, use_container_width=True)

if __name__ == "__main__":
    print("==================================================")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select a page from the sidebar to navigate.")
    st.set_page_config(layout="wide", page_title="Lastwar AI")
    st.markdown("<h1 style='text-align: center; color: #3ea6ff; '>OLDs Lastwar Dashboard</h1>", unsafe_allow_html=True)
    st.write("")
    conn = db.create_connection(database)

    # Get all alliances
    get_selection_data()

    chart_container = st.container()
    selection_container = st.container()
    with selection_container:
        # Metrictype = current/timeline, select multiple alliances
        metrictype_dropdown, multiselect_dropdown = render_selection_boxes(st)
    with chart_container:
        if metrictype_dropdown == 'Current':
            print_current_chart(st)
        elif metrictype_dropdown == 'Timeline' and st.session_state.goldust_alliances:
            print_timeline_chart(st)
        else:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    db.disconnect(conn)