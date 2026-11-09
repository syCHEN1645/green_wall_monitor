from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

SINGAPORE_TZ = ZoneInfo("Asia/Singapore")


def ensure_datetime(value: datetime | pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts


def to_singapore_time(value: datetime | pd.Timestamp) -> datetime:
    ts = ensure_datetime(value)
    return ts.tz_convert(SINGAPORE_TZ).to_pydatetime()


def to_utc_from_singapore(value: datetime | pd.Timestamp) -> datetime:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(SINGAPORE_TZ)
    return ts.tz_convert(timezone.utc).to_pydatetime()


def to_flux_time(value: datetime | pd.Timestamp) -> str:
    return to_utc_from_singapore(value).isoformat().replace("+00:00", "Z")


def format_singapore_timestamp(value) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert(SINGAPORE_TZ).strftime("%Y-%m-%d %H:%M")


def normalize_series_name(record) -> str:
    values = record.values or {}
    sensor = values.get("sensor")
    field = values.get("_field")
    measurement = values.get("_measurement")

    if sensor and field and field != "value":
        return f"{sensor}/{field}"
    if sensor and measurement and measurement != "value":
        return f"{sensor}/{measurement}"
    if measurement and field and field != "value":
        return f"{measurement}/{field}"
    if measurement:
        return str(measurement)
    if field and field != "value":
        return str(field)
    if sensor:
        return str(sensor)
    return "unknown"


def build_minute_labels(start_dt: datetime, end_dt: datetime) -> pd.DatetimeIndex:
    start_ts = pd.Timestamp(to_utc_from_singapore(start_dt)).floor("min")
    end_ts = pd.Timestamp(to_utc_from_singapore(end_dt)).floor("min")
    return pd.date_range(start=start_ts, end=end_ts, freq="1min")


def build_wide_frame(history_df: pd.DataFrame, selected_entries: list[str], start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    minute_labels = build_minute_labels(start_dt, end_dt)
    wide_df = pd.DataFrame({"timestamp": minute_labels})
    wide_df["timestamp"] = pd.to_datetime(wide_df["timestamp"], utc=True).dt.tz_convert(SINGAPORE_TZ)

    if history_df.empty:
        for entry_name in selected_entries:
            wide_df[entry_name] = pd.NA
        return wide_df

    history_df = history_df.copy()
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True).dt.tz_convert(SINGAPORE_TZ)

    for entry_name in selected_entries:
        entry_series = history_df[history_df["entry"] == entry_name].copy()
        if entry_series.empty:
            wide_df[entry_name] = pd.NA
            continue
        entry_series = entry_series[["timestamp", "value"]].drop_duplicates(subset=["timestamp"]).set_index("timestamp")["value"]
        wide_df[entry_name] = wide_df["timestamp"].map(entry_series)

    return wide_df.where(pd.notna(wide_df), pd.NA)


def export_csv_bytes(frame: pd.DataFrame) -> bytes:
    csv_df = frame.copy()
    if "timestamp" in csv_df.columns:
        csv_df["timestamp"] = csv_df["timestamp"].map(format_singapore_timestamp)
    return csv_df.to_csv(index=False, encoding="utf-8").encode("utf-8")


def resolve_query_window(start_dt: datetime, end_dt: datetime, real_time_mode: bool, now_dt: datetime | None = None):
    query_now = pd.Timestamp(now_dt or datetime.now(SINGAPORE_TZ))
    if query_now.tzinfo is None:
        query_now = query_now.tz_localize(SINGAPORE_TZ)
    else:
        query_now = query_now.tz_convert(SINGAPORE_TZ)

    if real_time_mode:
        return pd.Timestamp(start_dt).tz_convert(SINGAPORE_TZ).to_pydatetime(), query_now.to_pydatetime()
    return pd.Timestamp(start_dt).tz_convert(SINGAPORE_TZ).to_pydatetime(), pd.Timestamp(end_dt).tz_convert(SINGAPORE_TZ).to_pydatetime()


def build_refresh_script(interval_seconds: int | None) -> str:
    if interval_seconds is None:
        return """
        <script>
            if (window.__greenwall_data_viewer_timer) {
                clearInterval(window.__greenwall_data_viewer_timer);
                window.__greenwall_data_viewer_timer = null;
            }
            window.addEventListener('beforeunload', () => {
                if (window.__greenwall_data_viewer_timer) {
                    clearInterval(window.__greenwall_data_viewer_timer);
                    window.__greenwall_data_viewer_timer = null;
                }
            });
        </script>
        """

    return f"""
    <script>
        if (window.__greenwall_data_viewer_timer) {{
            clearInterval(window.__greenwall_data_viewer_timer);
        }}
        window.__greenwall_data_viewer_timer = setInterval(() => {{
            if (document.visibilityState !== 'hidden') {{
                window.location.reload();
            }}
        }}, {interval_seconds * 1000});
        window.addEventListener('beforeunload', () => {{
            if (window.__greenwall_data_viewer_timer) {{
                clearInterval(window.__greenwall_data_viewer_timer);
                window.__greenwall_data_viewer_timer = null;
            }}
        }});
    </script>
    """
