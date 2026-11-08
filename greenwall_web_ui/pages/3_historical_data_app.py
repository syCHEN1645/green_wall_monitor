import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from influxdb_client.client.influxdb_client import InfluxDBClient

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


st.set_page_config(page_title="Historical Data Review", layout="wide")
st.title("Historical Data Review")


def to_flux_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def normalize_series_name(record) -> str:
    values = record.values or {}
    sensor = values.get("sensor")
    if sensor:
        return str(sensor)

    measurement = values.get("_measurement")
    field = values.get("_field")
    if measurement and field and field != "value":
        return f"{measurement}/{field}"
    if measurement:
        return str(measurement)
    if field and field != "value":
        return str(field)
    return "unknown"


@st.cache_data(show_spinner=False)
def detect_available_entries() -> list[str]:
    try:
        client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
        query = f'''
        from(bucket: "{BUCKET}")
            |> range(start: -30d)
            |> keep(columns: ["_time", "_field", "_measurement", "sensor", "_value"])
            |> limit(n: 1000)
        '''
        tables = client.query_api().query(query)
        entries = set()
        for table in tables:
            for record in table.records:
                name = normalize_series_name(record)
                if name and name != "unknown":
                    entries.add(name)
        client.close()
        if entries:
            return sorted(entries)
    except Exception as exc:  # pragma: no cover - runtime-only failure path
        st.caption(f"Auto-detection fell back to known ESP32 entries: {exc}")

    return FALLBACK_ENTRIES


@st.cache_data(show_spinner=False)
def fetch_selected_history(start_dt: datetime, end_dt: datetime, selected_entries: list[str]):
    if not selected_entries:
        return pd.DataFrame(columns=["timestamp", "entry", "value"])

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

                timestamp = pd.to_datetime(record.get_time())
                rows.append({
                    "timestamp": timestamp.floor("min"),
                    "entry": name,
                    "value": float(value),
                })

        if not rows:
            return pd.DataFrame(columns=["timestamp", "entry", "value"])

        return pd.DataFrame(rows)
    finally:
        client.close()


if not TOKEN:
    st.error("InfluxDB credentials are missing. Set the GREENWALL_INFLUX_TOKEN environment variable before running this page.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    available_entries = detect_available_entries()
    selected_entries = st.multiselect(
        "Select one or more database entries",
        options=available_entries,
        default=available_entries[: min(3, len(available_entries))],
    )

    st.subheader("Time range")
    default_start = datetime.now() - timedelta(days=1)
    default_end = datetime.now()

    start_date = st.date_input("Start date", value=default_start.date())
    start_time = st.time_input("Start time", value=default_start.time())
    end_date = st.date_input("End date", value=default_end.date())
    end_time = st.time_input("End time", value=default_end.time())

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    run_query = st.button("Query selected entries", type="primary", use_container_width=True)

st.caption(
    "Entry names are automatically detected from the active InfluxDB bucket when possible; \
    if no metadata is available, the ESP32 sensor names are used as a fallback."
)

if not selected_entries:
    st.info("Select one or more entries from the sidebar to view historical data.")
    st.stop()

if start_dt >= end_dt:
    st.error("The end time must be later than the start time.")
    st.stop()

if run_query:
    with st.spinner("Querying InfluxDB..."):
        history_df = fetch_selected_history(start_dt, end_dt, selected_entries)
else:
    history_df = fetch_selected_history(start_dt, end_dt, selected_entries)

if history_df.empty:
    st.warning("No data found for the selected entries within the chosen time range.")
    st.stop()

minute_labels = pd.date_range(start=start_dt.replace(second=0, microsecond=0), end=end_dt.replace(second=0, microsecond=0), freq="1min")
wide_df = pd.DataFrame({"timestamp": minute_labels})

for entry_name in selected_entries:
    entry_series = history_df[history_df["entry"] == entry_name].copy()
    if entry_series.empty:
        wide_df[entry_name] = pd.NA
        continue

    entry_series = entry_series[["timestamp", "value"]].drop_duplicates()
    entry_series = entry_series.set_index("timestamp")["value"]
    wide_df[entry_name] = wide_df["timestamp"].map(entry_series)

wide_df = wide_df.where(pd.notna(wide_df), pd.NA)

st.subheader("Table view")
st.dataframe(wide_df, use_container_width=True, hide_index=True)

plot_df = wide_df.melt(id_vars="timestamp", var_name="entry", value_name="value").dropna(subset=["value"])
plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"])

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
    xaxis_title="Timestamp (minute bucket)",
    yaxis_title="Value",
    legend_title_text="Entry",
    template="plotly_white",
)
fig.update_xaxes(tickformat="%Y-%m-%d %H:%M")

st.subheader("Scatter plot")
st.plotly_chart(fig, use_container_width=True)
