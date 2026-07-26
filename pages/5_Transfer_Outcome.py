import streamlit as st
import pandas as pd
import altair as alt
import src.db as db
from datetime import datetime

# Goal:  Create a THP comparison chart for transfer gain/losses

#database = 'mySQL'
database = 'sqlite'
PRE_TRANSFER_DATE = '07/18/26'
POST_TRANSFER_DATE = '07/25/26'
SERVER_DEFAULT = [1103,1123,1098,1097,1157,1114,1084,1172,1074,1094,1072,1063,1130,1149,1160,1104,1078,1147,1100,1107,1109,1180,1075,1068,1090,1111]
ALLIANCE_DEFAULT = ['OLDs','SVGZ','LgND','FaF0','blod','SHUB','MaZ','UsU','TAAF','BDLM','Ap3x']

# Callbacks for selection box updates
def on_servers_change():
    st.session_state.transfer_servers_choice = st.session_state.transferserver_multiselect_value
    st.session_state.all_check = False
def on_alliances_change():
    st.session_state.transfer_alliances_choice = st.session_state.transferalliance_multiselect_value
def on_metrictype_change():
    st.session_state.transfer_choice = st.session_state.transfer_selectbox_value
def on_predate_change():
    st.session_state.pre_date = st.session_state.transfer_predate_value
def on_postdate_change():
    st.session_state.post_date = st.session_state.transfer_postdate_value
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
        server_query = "select distinct warzone from totalhero where date = '07/25/26' order by warzone"
        server_df = db.query_df(conn, server_query)
        st.session_state.server_region = server_df.iloc[:, 0].tolist()
        print("[INFO] Pulled servers from Database")
    if 'transfer_alliances' not in st.session_state:
        alliance_query = "select distinct alliance, sum(totalhero) as totalhero from totalhero where date = '07/25/26' group by alliance order by totalhero desc"
        alliance_df = db.query_df(conn, alliance_query)
        st.session_state.transfer_alliances = alliance_df.iloc[:, 0].tolist()
        print("[INFO] Pulled alliances from Database")
    if 'transfer_dates' not in st.session_state:
        date_query = "select distinct date from totalhero"
        date_df = db.query_df(conn, date_query)
        dates = date_df.iloc[:, 0].tolist()
        dates.sort(key=lambda d: datetime.strptime(d, '%m/%d/%y'))
        st.session_state.transfer_dates = dates
        print("[INFO] Pulled dates from Database")

def render_selection_boxes(col):
    space1, sel1, sel2, check, metric_col = col.columns([1, 5, 1, 1, 2])

    # Date dropdowns (only shows dates with actual data)
    _, date1, date2, _ = col.columns([1, 2, 2, 5])
    pre_index = st.session_state.transfer_dates.index(st.session_state.pre_date) if st.session_state.pre_date in st.session_state.transfer_dates else 0
    post_index = st.session_state.transfer_dates.index(st.session_state.post_date) if st.session_state.post_date in st.session_state.transfer_dates else len(st.session_state.transfer_dates) - 1
    date1.selectbox("Pre-transfer date", options=st.session_state.transfer_dates, index=pre_index, key="transfer_predate_value", on_change=on_predate_change)
    date2.selectbox("Post-transfer date", options=st.session_state.transfer_dates, index=post_index, key="transfer_postdate_value", on_change=on_postdate_change)

    if 'gain_loss_data' in st.session_state:
        d = st.session_state.gain_loss_data
        m1, m2 = metric_col.columns(2)
        m1.metric("Top Gainer", d['gainer_name'], delta=f"{d['gainer_delta']:+.2f}%")
        m2.metric("Top Loser", d['loser_name'], delta=f"{d['loser_delta']:+.2f}%")

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
            st.session_state.transfer_servers_choice = SERVER_DEFAULT
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
            st.session_state.transfer_alliances_choice = ALLIANCE_DEFAULT
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
    pre = st.session_state.pre_date
    post = st.session_state.post_date

    combined_df = pd.DataFrame(columns=["warzone", "totalhero"])
    for server in st.session_state.transfer_servers_choice:
        if database == 'mySQL':
            server_query = "select date, sum(totalhero) from totalhero where warzone = %s and (date = %s or date = %s) group by date order by date"
        else:
            server_query = f"select date, sum(totalhero) from totalhero where warzone = ? and (date = ? or date = ?) group by date order by date" # sqlite

        server_df = db.query_df(conn, server_query, [server, pre, post])
        if len(server_df) == 2:
            pre_total = server_df.iloc[0, 1]
            post_total = server_df.iloc[1, 1]

            # Avoid divide-by-zero
            if pre_total != 0:
                percent_change = ((post_total - pre_total) / pre_total) * 100
            else:
                percent_change = 0

            combined_df.loc[len(combined_df)] = [server, percent_change]

    print("[INFO] Pulled totalhero data from Database")
    if combined_df.empty:
        return True

    combined_df["totalhero"] = pd.to_numeric(combined_df["totalhero"])
    combined_df = combined_df.sort_values(by="totalhero", ascending=True)
    combined_df["color"] = combined_df["totalhero"].apply(lambda x: "#00e676" if x >= 0 else "#e60000")
    combined_df["percent_label"] = combined_df["totalhero"].apply(
        lambda x: f"{x:+.2f}%"
    )

    top_gainer = combined_df.loc[combined_df["totalhero"].idxmax()]
    top_loser = combined_df.loc[combined_df["totalhero"].idxmin()]
    st.session_state.gain_loss_data = {
        'gainer_name': f"{int(top_gainer['warzone'])}",
        'gainer_delta': float(top_gainer['totalhero']),
        'loser_name': f"{int(top_loser['warzone'])}",
        'loser_delta': float(top_loser['totalhero'])
    }

    server_order = combined_df["warzone"].tolist()
    server_bar = alt.Chart(combined_df).mark_bar().encode(
        x=alt.X("warzone:N", title="Warzone", sort=server_order),
        y=alt.Y("totalhero:Q", title="THP Change (%)", axis=alt.Axis(labelExpr="format(datum.value, '+.1f') + '%'")),
        color=alt.Color("color:N", scale=None),
        tooltip=["warzone", alt.Tooltip("percent_label:N", title="THP Change")]
    ).properties(
        title=alt.TitleParams(text=f"Season 5 Transfer: Warzone Growth (%)", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    col.altair_chart(server_bar, width='stretch')
    return False

def print_alliance_chart(col):
    pre = st.session_state.pre_date
    post = st.session_state.post_date

    combined_df = pd.DataFrame(columns=["alliance", "totalhero", "warzone"])
    for alliance in st.session_state.transfer_alliances_choice:
        if database == 'mySQL':
            alliance_query = "select date, sum(totalhero), warzone from totalhero where alliance = %s and (date = %s or date = %s) group by date, warzone order by date"
        else:
            alliance_query = f"select date, sum(totalhero), warzone from totalhero where alliance = ? and (date = ? or date = ?) group by date, warzone order by date" # sqlite

        alliance_df = db.query_df(conn, alliance_query, [alliance, pre, post])
        if len(alliance_df) == 2:
            pre_total = float(alliance_df.iloc[0, 1])
            post_total = float(alliance_df.iloc[1, 1])

            # Use the post-transfer warzone
            warzone = alliance_df.iloc[1, 2]
            # Avoid divide-by-zero
            if pre_total != 0:
                percent_change = ((post_total - pre_total) / pre_total) * 100
            else:
                percent_change = 0.0

            combined_df.loc[len(combined_df)] = {
                "alliance": alliance,
                "totalhero": percent_change,
                "warzone": warzone
            }

    print("[INFO] Pulled totalhero data from Database")
    if combined_df.empty:
        return True

    combined_df["totalhero"] = pd.to_numeric(combined_df["totalhero"])
    combined_df = combined_df.sort_values(by="totalhero", ascending=True)
    combined_df["color"] = combined_df.apply(
        lambda row: (
            "#2196f3" if row["alliance"] == "OLDs"
            else "#00e676" if row["totalhero"] >= 0
            else "#e60000"
        ),
        axis=1,
    )
    combined_df["percent_label"] = combined_df["totalhero"].apply(
        lambda x: f"{x:+.2f}%"
    )
    print(combined_df)

    top_gainer = combined_df.loc[combined_df["totalhero"].idxmax()]
    top_loser = combined_df.loc[combined_df["totalhero"].idxmin()]
    st.session_state.gain_loss_data = {
        'gainer_name': top_gainer['alliance'],
        'gainer_delta': float(top_gainer['totalhero']),
        'loser_name': top_loser['alliance'],
        'loser_delta': float(top_loser['totalhero'])
    }

    # alliance_order = combined_df["alliance"].tolist()
    alliance_order = (
        combined_df.sort_values("totalhero", ascending=True)["alliance"]
        .tolist()
    )
    print(alliance_order)
    print(combined_df)
    alliance_bar = alt.Chart(combined_df).mark_bar().encode(
        x=alt.X("alliance:N", title="Alliance", sort=alliance_order),
        y=alt.Y("totalhero:Q", title="THP Change (%)", axis=alt.Axis(labelExpr="format(datum.value, '+.1f') + '%'")),
        color=alt.Color("color:N", scale=None),
        tooltip=["warzone", "alliance", alt.Tooltip("percent_label:N", title="THP Change")]
    ).properties(
        title=alt.TitleParams(text=f"Season 5 Transfer: Alliance Growth (%)", anchor='middle', fontSize=24),
        height=800
    ).interactive()

    col.altair_chart(alliance_bar, width='stretch')
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

    # Pre-initialize defaults so chart can compute on first render
    if 'transfer_choice' not in st.session_state:
        st.session_state.transfer_choice = 'Alliance'
    if 'pre_date' not in st.session_state:
        st.session_state.pre_date = PRE_TRANSFER_DATE if PRE_TRANSFER_DATE in st.session_state.transfer_dates else st.session_state.transfer_dates[0]
    if 'post_date' not in st.session_state:
        st.session_state.post_date = POST_TRANSFER_DATE if POST_TRANSFER_DATE in st.session_state.transfer_dates else st.session_state.transfer_dates[-1]
    if 'transfer_alliances_choice' not in st.session_state:
        desired = ALLIANCE_DEFAULT
        st.session_state.transfer_alliances_choice = [a for a in desired if a in st.session_state.transfer_alliances]
    if 'transfer_servers_choice' not in st.session_state:
        desired = SERVER_DEFAULT
        st.session_state.transfer_servers_choice = [s for s in desired if s in st.session_state.server_region]

    chart_container = st.container()
    selection_container = st.container()

    # Chart fills first so gain_loss_data is in session state before selection row renders
    with chart_container:
        if st.session_state.transfer_choice == 'Server' and st.session_state.transfer_servers_choice:
            show_blank = print_server_chart(st)
        elif st.session_state.transfer_choice == 'Alliance' and st.session_state.transfer_alliances_choice:
            show_blank = print_alliance_chart(st)
        else:
            show_blank = True

        if show_blank == True:
            dummy_chart = alt.Chart().mark_point().encode().properties(height=800)
            st.altair_chart(dummy_chart)

    with selection_container:
        render_selection_boxes(st)

    db.disconnect(conn)