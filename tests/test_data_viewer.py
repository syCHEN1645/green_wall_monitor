from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "greenwall_web_ui"))

from data_viewer_utils import (
    SINGAPORE_TZ,
    build_refresh_script,
    build_wide_frame,
    export_csv_bytes,
    to_singapore_time,
)


def test_to_singapore_time_converts_utc_to_sgt():
    dt = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
    assert to_singapore_time(dt) == datetime(2026, 11, 8, 20, 0, tzinfo=SINGAPORE_TZ)


def test_build_wide_frame_keeps_minute_grid_and_missing_values():
    start_dt = datetime(2026, 11, 8, 20, 0, tzinfo=SINGAPORE_TZ)
    end_dt = datetime(2026, 11, 8, 20, 5, tzinfo=SINGAPORE_TZ)
    history_df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-11-08T12:02:00Z"), "entry": "sensor-a/temp", "value": 5.0},
            {"timestamp": pd.Timestamp("2026-11-08T12:04:00Z"), "entry": "sensor-a/temp", "value": 7.0},
            {"timestamp": pd.Timestamp("2026-11-08T12:03:00Z"), "entry": "sensor-b/humidity", "value": 10.0},
        ]
    )

    wide_df = build_wide_frame(history_df, ["sensor-a/temp", "sensor-b/humidity"], start_dt, end_dt)

    assert list(wide_df.columns) == ["timestamp", "sensor-a/temp", "sensor-b/humidity"]
    assert wide_df["sensor-a/temp"].isna().sum() >= 1
    assert wide_df["sensor-b/humidity"].notna().sum() >= 1


def test_export_csv_bytes_uses_singapore_display_format():
    frame = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-11-08T12:00:00Z"), "sensor-a/temp": 42.0, "sensor-b/humidity": 10.5}]
    )
    payload = export_csv_bytes(frame)
    assert b"2026-11-08 20:00" in payload
    assert b"sensor-a/temp" in payload


def test_build_refresh_script_uses_single_timer_and_reload():
    script = build_refresh_script(30)
    assert "clearInterval(window.__greenwall_data_viewer_timer)" in script
    assert "setInterval" in script
    assert "window.location.reload()" in script


def test_main_app_routes_to_data_viewer_page():
    main_app_path = REPO_ROOT / "greenwall_web_ui" / "main_app.py"
    text = main_app_path.read_text(encoding="utf-8")
    assert 'st.switch_page("pages/1_data_viewer_app.py")' in text
