import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from influxdb_client.client.influxdb_client import InfluxDBClient
import os
import json

# --- CONFIGURATION ---
INFLUX_URL = "http://localhost:8086"
ORG = "greenwall"
BUCKET = "test-data"
TOKEN = "396eLu78MVeq4xLCbKqnXNCUsdyK7ZKgkPUT6XeZhnl0UXmmx4r9Z978iGbtMjHHDU7yvt3l5C4Znjqc6c9RFg=="
LOG_FILE = "experiment_logs.json"

st.set_page_config(page_title="GreenWall Lab Log", layout="wide")
st.title("GreenWall Lab Experiment Log (Python)")

"""
Load experiment histories
"""
def load_logs():
    return []

"""
Save an experiment log to file
"""
def save_log():
    return []


with st.sidebar:
    st.header("1. Experiment info")
    exp_name = st.text_input("Experiemnt Name", placeholder="")
    
    start_date = st.date_input("Start Date", datetime.now() - timedelta(hours=1))
    start_time = st.time_input("Start Time", (datetime.now() - timedelta(hours=1)).time())

    end_date = st.date_input("End Date", datetime.now())
    end_time = st.time_input("End Time", datetime.now().time())

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    col1, col2 = st.columns(2)
    with col1:
        run_query = st.button("Run Query", use_container_width=True)
    with col2:
        save_info = st.button("Save Experiment Info", use_container_width=True)
    if save_info and exp_name:
        # TODO
        save_log()
        st.success("Saved")
    
    st.divider()
    st.header("Saved Experiment Timelines")
    saved_logs = load_logs()
    
    # Display historical logs as clickable triggers
    for log in saved_logs:
        if st.button(label="label"):
            st.rerun()


# data graph
st.subheader("2. Data Graph View")

if run_query:
    with st.spinner("Running query..."):
        # Format datetimes to strict RFC3339 strings for Influx Flux engine
        start_iso = start_dt.isoformat() + "Z"
        end_iso = end_dt.isoformat() + "Z"

        flux_query = f'''
        from(bucket: "{BUCKET}")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "Box-1")
            |> filter(fn: (r) => r["_field"] == "value")
        '''

        try:
            # Connect and execute query
            client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
            query_api = client.query_api()
            tables = query_api.query(flux_query)

            timestamps = []
            values = []
            sensor_labels = []

            for table in tables:
                for record in table.records:
                    timestamps.append(record.get_time())
                    values.append(record.get_value())
                    sensor_labels.append(record.values.get("sensor", "Unknown"))

            client.close()

            if not timestamps:
                st.warning("No metrics found inside this specific time range.")
            else:
                # Create the Matplotlib Plot
                fig, ax = plt.subplots(figsize=(10, 4.5))
                ax.plot(timestamps, values, marker='o', linestyle='-', color='#228be6', markersize=3, label=exp_name or "Sensor Data")
                
                ax.set_title(f"Experiment Run: {exp_name or 'Telemetry Stream'}", fontsize=12, fontweight='bold')
                ax.set_xlabel("Timeline Interval", fontsize=10)
                ax.set_ylabel("Sensor Output Scalar", fontsize=10)
                ax.grid(True, linestyle='--', alpha=0.6)
                plt.xticks(rotation=15)
                plt.tight_layout()

                # Show plot in browser window interface
                st.pyplot(fig)

                # Save locally to temp file to enable image download button
                temp_img_path = "temp_chart.png"
                fig.savefig(temp_img_path, dpi=300)

                with open(temp_img_path, "rb") as file:
                    st.download_button(
                        label="📷 Export Graph Image (PNG)",
                        data=file,
                        file_name=f"{exp_name.replace(' ', '_') if exp_name else 'experiment'}_graph.png",
                        mime="image/png",
                        use_container_width=False
                    )
        except Exception as e:
            st.error(f"Failed to communicate with InfluxDB: {e}")
else:
    st.info("Input a time scale configuration range on the left sidebar pane and execute 'Run Query'.")
