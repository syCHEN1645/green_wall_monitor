import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from influxdb_client.client.influxdb_client import InfluxDBClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_viewer_utils import (
    SINGAPORE_TZ,
    build_refresh_script,
    build_wide_frame,
    export_csv_bytes,
    format_singapore_timestamp,
    normalize_series_name,
    to_flux_time,
)

load_dotenv(dotenv_path=ROOT_DIR / ".env")

INFLUX_URL = os.environ.get("GREENWALL_INFLUX_URL", "http://localhost:8086")
ORG = os.environ.get("GREENWALL_INFLUX_ORG", "greenwall")
BUCKET = os.environ.get("GREENWALL_INFLUX_BUCKET", "test-data")
TOKEN = os.environ.get("GREENWALL_INFLUX_TOKEN")

FALLBACK_ENTRIES = [
    "2-air-temp-out/air-temp",
    "2-air-temp-in/air-temp",
    "2-water-temp/wall-temp",
    "2-wall-temp/wall-temp",
    "2-soil-moisture/soil-moisture",
]

REFRESH_INTERVALS = {
    "30 seconds": 30,
    "1 minute": 60,
    "5 minutes": 300,
    "30 minutes": 1800,
}

LIGHT_THEME_CSS = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    .stApp {
        font-size: 1.5rem !important;
    }
    div, p, label, .stTextInput, .stDateInput, .stTimeInput, .stSelectbox, .stMultiSelect, .stButton, .stDownloadButton, .stDataFrame, .stPlotlyChart, .stMetric {
        font-size: 1.5rem !important;
    }
    .stDataFrame table {
        font-size: 1.45rem !important;
    }
    .stSidebar {
        background-color: #f8fafc !important;
        border-right: 1px solid #d1d5db !important;
    }
    .stSidebar .stSelectbox, .stSidebar .stTextInput, .stSidebar .stDateInput, .stSidebar .stTimeInput, .stSidebar .stCheckbox, .stSidebar .stRadio {
        font-size: 1.5rem !important;
    }
    .stButton button, .stDownloadButton button {
        font-size: 1.45rem !important;
    }
    .stDataFrame, .stDataFrame .dataframe {
        width: 100% !important;
    }
    .stTable td, .stTable th {
        border: 1px solid #d1d5db !important;
        color: #111827 !important;
    }
    .stTabs [role="tablist"] button {
        font-size: 1.4rem !important;
    }
    .plotly .modebar, .plotly .svg-container {
        background-color: #ffffff !important;
    }
</style>
"""

st.set_page_config(page_title="Data Viewer", layout="wide")
st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
st.title("Data Viewer")


@st.cache_data(show_spinner=False)
def detect_available_entries() -> list[str]:
    if not TOKEN:
        return FALLBACK_ENTRIES

    try:
        client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
        query = f'''
        from(bucket: "{BUCKET}")
            |> range(start: -30d)
            |> keep(columns: ["_time", "_field", "_measurement", "sensor", "_value"])
            |> limit(n: 2000)
        '''
        tables = client.query_api().query(query)
        client.close()
        entries = set()
        for table in tables:
            for record in table.records:
                name = normalize_series_name(record)
                if name and name != "unknown":
                    entries.add(name)
        if entries:
            return sorted(entries)
    except Exception as exc:  # pragma: no cover - runtime-only failure path
        st.caption(f"Auto-detected entries could not be loaded. Falling back to the ESP32 sensor list. Error: {exc}")
    return FALLBACK_ENTRIES


@st.cache_data(show_spinner=False)
def fetch_selected_history(start_dt: datetime, end_dt: datetime, selected_entries: list[str]):
    if not selected_entries:
        return pd.DataFrame(columns=["timestamp", "entry", "value"])

    if not TOKEN:
        raise ValueError("The InfluxDB token is not configured.")

    start_iso = to_flux_time(start_dt)
    end_iso = to_flux_time(end_dt)
    flux_query = f'''
    from(bucket: "{BUCKET}")
        |> range(start: {start_iso}, stop: {end_iso})
        |> aggregateWindow(every: 1m, fn: last, createEmpty: true)
        |> keep(columns: ["_time", "_field", "_measurement", "sensor", "_value"])
    '''

    client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
    try:
        tables = client.query_api().query(flux_query)
        rows = []
        for table in tables:
            for record in table.records:
                try:
                    value = record.get_value()
                except Exception:
                    continue
                if value is None:
                    continue

                name = normalize_series_name(record)
                if name not in selected_entries:
                    continue

                timestamp = pd.to_datetime(record.get_time(), utc=True)
                rows.append({
                    "timestamp": timestamp.floor("min"),
                    "entry": name,
                    "value": float(value),
                })

        if not rows:
            return pd.DataFrame(columns=["timestamp", "entry", "value"])

        history_df = pd.DataFrame(rows)
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)
        return history_df
    finally:
        client.close()


with st.sidebar:
    st.header("Filters")

    if not TOKEN:
        st.error("The InfluxDB token is not configured. Set GREENWALL_INFLUX_TOKEN in the environment or in greenwall_web_ui/.env before running this page.")
        st.stop()

    available_entries = detect_available_entries()

    if "selected_entries" not in st.session_state:
        st.session_state["selected_entries"] = available_entries[: min(3, len(available_entries))]

    selected_entries = st.multiselect(
        "Select one or more database entries",
        options=available_entries,
        default=st.session_state["selected_entries"],
        help="Select the series to query from InfluxDB.",
    )
    st.session_state["selected_entries"] = selected_entries

    st.subheader("Time range")
    now_dt = datetime.now(SINGAPORE_TZ)
    end_now = st.checkbox("Use Now for end time", value=False)

    default_start = now_dt - timedelta(days=1)
    start_date = st.date_input("Start date", value=default_start.date())
    start_time = st.time_input("Start time", value=default_start.time())
    start_dt = datetime.combine(start_date, start_time).replace(tzinfo=SINGAPORE_TZ)

    if end_now:
        end_dt = now_dt
        end_display = "Now"
    else:
        default_end = now_dt
        end_date = st.date_input("End date", value=default_end.date())
        end_time = st.time_input("End time", value=default_end.time())
        end_dt = datetime.combine(end_date, end_time).replace(tzinfo=SINGAPORE_TZ)
        end_display = end_dt.strftime("%Y-%m-%d %H:%M")

    st.caption(f"Current local time: {now_dt.strftime('%Y-%m-%d %H:%M:%S')} SGT")
    st.caption(f"Query end time: {end_display}")

    real_time_mode = st.checkbox("Enable real-time refresh", value=False)
    refresh_options = ["30 seconds", "1 minute", "5 minutes", "30 minutes"]
    refresh_interval_label = st.selectbox(
        "Refresh rate",
        options=refresh_options,
        index=1,
        disabled=not real_time_mode,
    )
    refresh_interval_seconds = REFRESH_INTERVALS[refresh_interval_label]

    run_query = st.button("Query selected entries", type="primary", use_container_width=True)

    if real_time_mode:
        if "realtime_start_dt" not in st.session_state:
            st.session_state["realtime_start_dt"] = start_dt
        start_dt = st.session_state["realtime_start_dt"]
        end_dt = datetime.now(SINGAPORE_TZ)
        end_display = "Now"
    else:
        st.session_state.pop("realtime_start_dt", None)

st.caption("The time range is displayed in Singapore time, and the database timestamps are kept unchanged in UTC.")

if not selected_entries:
    st.info("Select one or more entries from the sidebar to view historical data.")
    st.stop()

if start_dt >= end_dt:
    st.error("The end time must be later than the start time.")
    st.stop()

try:
    with st.spinner("Querying InfluxDB..."):
        history_df = fetch_selected_history(start_dt, end_dt, selected_entries)
except Exception as exc:
    st.error(f"Failed to query InfluxDB: {exc}")
    st.stop()

if history_df.empty:
    st.warning("No data found for the selected entries within the chosen time range.")
    st.stop()

wide_df = build_wide_frame(history_df, selected_entries, start_dt, end_dt)
wide_display_df = wide_df.copy()
wide_display_df["timestamp"] = wide_display_df["timestamp"].map(format_singapore_timestamp)

st.subheader("Table view")
st.dataframe(wide_display_df, use_container_width=True, hide_index=True)

plot_df = wide_df.melt(id_vars="timestamp", var_name="entry", value_name="value").dropna(subset=["value"])
plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"], utc=True).dt.tz_convert(SINGAPORE_TZ)

fig = px.line(
    plot_df,
    x="timestamp",
    y="value",
    color="entry",
    markers=True,
    title="Historical readings by selected entry",
    category_orders={"entry": selected_entries},
)
fig.update_layout(
    xaxis_title="Timestamp (Singapore time)",
    yaxis_title="Value",
    legend_title_text="Entry",
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    font={"size": 16, "color": "#111827"},
    legend={"font": {"size": 15}, "title_font": {"size": 16}},
    margin={"l": 40, "r": 20, "t": 60, "b": 60},
)
fig.update_xaxes(tickformat="%Y-%m-%d %H:%M", title_font={"size": 16}, tickfont={"size": 15})
fig.update_yaxes(title_font={"size": 16}, tickfont={"size": 15}, gridcolor="#e5e7eb")
fig.update_traces(mode="lines+markers", marker={"size": 8}, line={"width": 2})

st.subheader("Scatter plot")
st.plotly_chart(fig, use_container_width=True)

csv_export_name = st.text_input("CSV file name", value="data_viewer_export.csv")
export_filename = csv_export_name.strip() or "data_viewer_export.csv"
export_data = export_csv_bytes(wide_display_df)

st.download_button(
    label="Export current table as CSV",
    data=export_data,
    file_name=export_filename,
    mime="text/csv",
    use_container_width=True,
    disabled=wide_display_df.empty,
)

if real_time_mode:
    st.components.v1.html(build_refresh_script(refresh_interval_seconds), height=0)
else:
    st.components.v1.html(build_refresh_script(None), height=0)
