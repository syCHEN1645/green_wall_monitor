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
    build_wide_frame,
    export_csv_bytes,
    format_singapore_timestamp,
    normalize_series_name,
    resolve_query_window,
    should_auto_refresh,
    to_flux_time,
)
from theme_utils import apply_shared_theme, render_topbar_company_name

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

st.set_page_config(page_title="Data Viewer", layout="wide")
apply_shared_theme()
render_topbar_company_name()
st.title("Data Viewer")
st.caption("Historical readings and live monitoring for GreenWall sensor data")


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
                rows.append(
                    {
                        "timestamp": timestamp.floor("min"),
                        "entry": name,
                        "value": float(value),
                    }
                )

        if not rows:
            return pd.DataFrame(columns=["timestamp", "entry", "value"])

        history_df = pd.DataFrame(rows)
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)
        return history_df
    finally:
        client.close()


def initialize_query_state() -> None:
    now_dt = datetime.now(SINGAPORE_TZ)
    default_start = now_dt - timedelta(days=1)

    st.session_state.setdefault("dv_query_submitted", False)
    st.session_state.setdefault("dv_query_pending", False)
    st.session_state.setdefault("dv_realtime_active", False)
    st.session_state.setdefault("dv_submitted_params", None)
    st.session_state.setdefault("dv_last_refresh_at", None)
    st.session_state.setdefault("dv_last_query_start_dt", None)
    st.session_state.setdefault("dv_last_query_end_dt", None)
    st.session_state.setdefault("dv_last_history_df", None)
    st.session_state.setdefault("dv_last_query_error", None)
    st.session_state.setdefault("dv_last_query_no_data", False)
    st.session_state.setdefault("dv_last_input_signature", None)
    st.session_state.setdefault("dv_last_control_change_at", None)

    st.session_state.setdefault("dv_input_start_date", default_start.date())
    st.session_state.setdefault("dv_input_start_time", default_start.time().replace(microsecond=0))
    st.session_state.setdefault("dv_input_end_date", now_dt.date())
    st.session_state.setdefault("dv_input_end_time", now_dt.time().replace(microsecond=0))
    st.session_state.setdefault("real_time_monitor_checkbox", False)
    st.session_state.setdefault("real_time_refresh_interval", "1 minute")
    st.session_state.setdefault("data_viewer_csv_name", "data_viewer_export.csv")


def render_results_from_history(history_df: pd.DataFrame, selected_entries: list[str], query_start_dt: datetime, query_end_dt: datetime) -> None:
    wide_df = build_wide_frame(
        history_df,
        selected_entries,
        query_start_dt,
        query_end_dt,
    )
    wide_display_df = wide_df.copy()
    wide_display_df["timestamp"] = wide_display_df["timestamp"].map(
        format_singapore_timestamp
    )

    st.subheader("Table view")
    st.dataframe(wide_display_df, use_container_width=True, hide_index=True)

    csv_export_name = st.text_input(
        "CSV file name",
        value=st.session_state.get("data_viewer_csv_name", "data_viewer_export.csv"),
        key="data_viewer_csv_name",
    )
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

    st.subheader("Scatter plot")
    plot_df = wide_df.melt(
        id_vars="timestamp",
        var_name="entry",
        value_name="value",
    ).dropna(subset=["value"])
    plot_df["timestamp"] = pd.to_datetime(
        plot_df["timestamp"],
        utc=True,
    ).dt.tz_convert(SINGAPORE_TZ)

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
        paper_bgcolor="rgba(255,255,255,0.90)",
        plot_bgcolor="rgba(243,247,251,0.9)",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "size": 15, "color": "#1f2d3d"},
        legend={"font": {"size": 13}, "title_font": {"size": 14}},
        margin={"l": 50, "r": 25, "t": 60, "b": 60},
        hovermode="closest",
        xaxis={
            "gridcolor": "#dfeaf3",
            "zerolinecolor": "#dfeaf3",
            "showline": True,
            "linecolor": "#9db6c9",
            "tickfont": {"size": 12},
        },
        yaxis={
            "gridcolor": "#dfeaf3",
            "zerolinecolor": "#dfeaf3",
            "showline": True,
            "linecolor": "#9db6c9",
            "tickfont": {"size": 12},
        },
    )
    fig.update_xaxes(
        tickformat="%Y-%m-%d %H:%M",
        title_font={"size": 14},
        tickfont={"size": 12},
    )
    fig.update_yaxes(
        title_font={"size": 14},
        tickfont={"size": 12},
        gridcolor="#dfeaf3",
    )
    fig.update_traces(
        mode="lines+markers",
        marker={"size": 7},
        line={"width": 2.5},
    )

    st.plotly_chart(fig, use_container_width=True)


initialize_query_state()

with st.sidebar:
    st.header("Filters")

    if not TOKEN:
        st.error("The InfluxDB token is not configured. Set GREENWALL_INFLUX_TOKEN in the environment or in greenwall_web_ui/.env before running this page.")
        st.stop()

    available_entries = detect_available_entries()
    current_entries = st.session_state.get("dv_input_entries")
    if not current_entries:
        st.session_state["dv_input_entries"] = available_entries[: min(3, len(available_entries))]
    else:
        st.session_state["dv_input_entries"] = [entry for entry in current_entries if entry in available_entries]

    selected_entries = st.multiselect(
        "Select one or more database entries",
        options=available_entries,
        key="dv_input_entries",
        help="Select the series to query from InfluxDB.",
    )

    st.subheader("Time range")
    now_dt = datetime.now(SINGAPORE_TZ)

    real_time_mode = st.checkbox(
        "Real-time monitor",
        key="real_time_monitor_checkbox",
    )

    start_date = st.date_input("Start date", key="dv_input_start_date")
    start_time = st.time_input("Start time", key="dv_input_start_time")
    start_dt = datetime.combine(start_date, start_time).replace(tzinfo=SINGAPORE_TZ)

    if real_time_mode:
        end_dt = datetime.now(SINGAPORE_TZ)
        end_display = "Now"
    else:
        end_date = st.date_input("End date", key="dv_input_end_date")
        end_time = st.time_input("End time", key="dv_input_end_time")
        end_dt = datetime.combine(end_date, end_time).replace(tzinfo=SINGAPORE_TZ)
        end_display = end_dt.strftime("%Y-%m-%d %H:%M")

    st.caption(f"Current local time: {now_dt.strftime('%Y-%m-%d %H:%M:%S')} SGT")
    st.caption(f"Query end time: {end_display}")

    refresh_options = ["30 seconds", "1 minute", "5 minutes", "30 minutes"]
    refresh_interval_label = st.selectbox(
        "Refresh rate",
        options=refresh_options,
        disabled=not real_time_mode,
        key="real_time_refresh_interval",
        help="Refresh interval used while Real-time monitor is enabled.",
    )
    refresh_interval_seconds = REFRESH_INTERVALS[refresh_interval_label]

    run_query = st.button("Query selected entries", type="primary", use_container_width=True)

    if real_time_mode:
        st.caption(
            "Real-time mode keeps the selected start time fixed and advances the query end time to the current time on each refresh."
        )
    else:
        st.caption("Manual mode uses a fixed end time selected from the controls above.")

st.caption("The time range is displayed in Singapore time, and the database timestamps are kept unchanged in UTC.")

current_input_signature = (
    tuple(selected_entries),
    start_dt.isoformat(),
    end_dt.isoformat() if not real_time_mode else "now",
    real_time_mode,
    refresh_interval_seconds,
)
last_input_signature = st.session_state.get("dv_last_input_signature")
if current_input_signature != last_input_signature and not run_query:
    st.session_state["dv_last_control_change_at"] = datetime.now(SINGAPORE_TZ)
st.session_state["dv_last_input_signature"] = current_input_signature

if not real_time_mode and st.session_state.get("dv_realtime_active"):
    st.session_state["dv_realtime_active"] = False

if run_query:
    if not selected_entries:
        st.session_state["dv_query_submitted"] = False
        st.session_state["dv_query_pending"] = False
        st.session_state["dv_realtime_active"] = False
        st.session_state["dv_last_history_df"] = None
        st.session_state["dv_last_query_error"] = "Select one or more entries before running a query."
    else:
        st.session_state["dv_submitted_params"] = {
            "selected_entries": selected_entries.copy(),
            "start_dt": start_dt,
            "end_dt": end_dt,
            "real_time_mode": real_time_mode,
            "refresh_interval_seconds": refresh_interval_seconds,
        }
        st.session_state["dv_query_submitted"] = True
        st.session_state["dv_query_pending"] = True
        st.session_state["dv_realtime_active"] = False
        st.session_state["dv_last_refresh_at"] = None
        st.session_state["dv_last_query_error"] = None
        st.session_state["dv_last_query_no_data"] = False
        st.session_state["dv_last_control_change_at"] = None

submitted_params = st.session_state.get("dv_submitted_params")
fragment_interval_seconds = None
if (
    st.session_state.get("dv_realtime_active")
    and submitted_params
    and submitted_params.get("real_time_mode")
):
    fragment_interval_seconds = submitted_params["refresh_interval_seconds"]


@st.fragment(run_every=fragment_interval_seconds)
def render_data_results() -> None:
    if not st.session_state.get("dv_query_submitted"):
        st.info("Set filters and click 'Query selected entries' to load data.")
        return

    params = st.session_state.get("dv_submitted_params")
    if not params:
        st.info("Set filters and click 'Query selected entries' to load data.")
        return

    now_dt = datetime.now(SINGAPORE_TZ)
    should_query = False

    if st.session_state.get("dv_query_pending"):
        should_query = True
    elif st.session_state.get("dv_realtime_active") and params.get("real_time_mode"):
        last_control_change = st.session_state.get("dv_last_control_change_at")
        if last_control_change:
            elapsed_since_change = (now_dt - pd.Timestamp(last_control_change).to_pydatetime()).total_seconds()
            if elapsed_since_change < params["refresh_interval_seconds"]:
                should_query = False
            else:
                should_query = should_auto_refresh(
                    st.session_state.get("dv_last_refresh_at"),
                    params["refresh_interval_seconds"],
                    now_dt,
                )
        else:
            should_query = should_auto_refresh(
                st.session_state.get("dv_last_refresh_at"),
                params["refresh_interval_seconds"],
                now_dt,
            )

    if should_query:
        query_end_input = now_dt if params["real_time_mode"] else params["end_dt"]
        query_start_dt, query_end_dt = resolve_query_window(
            params["start_dt"],
            query_end_input,
            params["real_time_mode"],
            now_dt,
        )

        if query_start_dt >= query_end_dt:
            st.session_state["dv_query_pending"] = False
            st.session_state["dv_last_query_error"] = "The end time must be later than the start time."
            st.session_state["dv_last_query_no_data"] = False
        else:
            try:
                with st.spinner("Querying InfluxDB..."):
                    history_df = fetch_selected_history(
                        query_start_dt,
                        query_end_dt,
                        params["selected_entries"],
                    )
                st.session_state["dv_last_history_df"] = history_df
                st.session_state["dv_last_query_start_dt"] = query_start_dt
                st.session_state["dv_last_query_end_dt"] = query_end_dt
                st.session_state["dv_last_query_error"] = None
                st.session_state["dv_last_query_no_data"] = history_df.empty
                st.session_state["dv_last_refresh_at"] = now_dt
                st.session_state["dv_query_pending"] = False

                if params["real_time_mode"] and not st.session_state.get("dv_realtime_active"):
                    st.session_state["dv_realtime_active"] = True
                    st.rerun()
            except Exception as exc:
                st.session_state["dv_last_query_error"] = f"Failed to query InfluxDB: {exc}"
                st.session_state["dv_query_pending"] = False
                st.session_state["dv_last_query_no_data"] = False

    last_error = st.session_state.get("dv_last_query_error")
    if last_error:
        st.error(last_error)
        return

    history_df = st.session_state.get("dv_last_history_df")
    query_start_dt = st.session_state.get("dv_last_query_start_dt")
    query_end_dt = st.session_state.get("dv_last_query_end_dt")
    if query_end_dt is not None:
        st.caption(f"Query end time: {format_singapore_timestamp(query_end_dt)}")

    if st.session_state.get("dv_last_query_no_data"):
        st.warning("No data found for the selected entries within the chosen time range.")
        return

    if history_df is None or query_start_dt is None or query_end_dt is None:
        st.info("No query results yet. Click 'Query selected entries' to fetch data.")
        return

    render_results_from_history(
        history_df=history_df,
        selected_entries=params["selected_entries"],
        query_start_dt=query_start_dt,
        query_end_dt=query_end_dt,
    )


render_data_results()
