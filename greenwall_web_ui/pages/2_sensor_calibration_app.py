import socket
import select
import json
import datetime
import threading
import streamlit as st

import config_utils
from theme_utils import apply_shared_theme, render_topbar_company_name

RECV_PORT = 5006

st.set_page_config(page_title="Sensor Calibration", layout="wide")
apply_shared_theme()
render_topbar_company_name()
st.title("Sensor Calibration")

# list of sensors that can be calibrated
sensors = [config_utils.DO_NAME]
# sensors = [config_utils.PH_NAME, config_utils.DO_NAME, config_utils.ORP_NAME]

with st.sidebar:
    st.header("Select sensor to calibrate")
    selected_sensor = st.selectbox(
        label="Sensor",
        options=sensors,
        index=0
    )
    st.divider()

# cache config data in session state to avoid reloading old config on every interaction
config_key = f"config_{selected_sensor}"
if config_key not in st.session_state:
    st.session_state[config_key] = config_utils.load_config(selected_sensor)

# JSON dict for the selected sensor
sensor_config = st.session_state[config_key]
assert isinstance(sensor_config, dict)

st.subheader(f"{selected_sensor} Real-time Raw Sensor Reading (V/mV)")

# show the last live sensor reading and the time it was received
# use a mutable object to store the last reading and time, so that the UDP socket worker can update it
if "last_live_sensor_reading" not in st.session_state:
    st.session_state["last_live_sensor_reading"] = {}
if "last_live_sensor_reading_time" not in st.session_state:
    st.session_state["last_live_sensor_reading_time"] = {}

if not hasattr(st, "_active_bg_socket"):
    setattr(st, "_active_bg_socket", None)

# there is a background thread running from before refreshing the browser, close it and start a new thread
if getattr(st, "_active_bg_socket") is not None:
    try:
        getattr(st, "_active_bg_socket").close()
    except Exception:
        pass
    setattr(st, "_active_bg_socket", None)

def udp_socket_rx_worker(reading_cache, time_cache):
    """
    Worker function to receive UDP packets from the UDP server.
    This function runs in a separate thread and updates the session state with the latest sensor reading.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", RECV_PORT))
        s.setblocking(True)
        setattr(st, "_active_bg_socket", s)
    except Exception as e:
        print(f"Error setting up UDP socket: {e}")
        return
    
    while True:
        try:
            data, _ = s.recvfrom(128)
            payload = json.loads(data.decode("utf-8"))

            assert isinstance(payload, dict)
            if "sensor" not in payload or "reading" not in payload or "error" not in payload:
                print("Invalid payload received from UDP server.")
                continue
            
            if payload["error"]:
                print(f"Error from UDP server: {payload['error']}")
                continue

            sensor_id = payload["sensor"]

            reading_cache[sensor_id] = payload["reading"]
            time_cache[sensor_id] = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
            print(f"Updated live reading for sensor '{sensor_id}': {payload['reading']}")

        except OSError as os_err:
            # Captures socket closures
            print(f"Socket channel disconnected or closed ({os_err.errno}). Terminating old loop thread safely.")
            break

        except Exception as e:
            print(f"Error receiving data from UDP server: {e}")

# run the UDP socket receiver in a separate thread to avoid blocking the Streamlit UI
if "udp_thread_started" not in st.session_state:
    worker = threading.Thread(
        target=udp_socket_rx_worker,
        args=(st.session_state["last_live_sensor_reading"], st.session_state["last_live_sensor_reading_time"]),
        # Setting daemon ensures thread dies cleanly when the app terminates
        daemon=True 
    )
    worker.start()
    st.session_state["udp_thread_started"] = True

@st.fragment(run_every=1.0)
def render_live_sensor_reading():
    """
    Render the live sensor reading from the UDP server.
    """
    this_sensor_type_id = sensor_config["sensor_id"]["val"]
    if this_sensor_type_id not in st.session_state["last_live_sensor_reading"] or this_sensor_type_id not in st.session_state["last_live_sensor_reading_time"]:
        st.session_state["last_live_sensor_reading"][this_sensor_type_id] = "N/A"
        st.session_state["last_live_sensor_reading_time"][this_sensor_type_id] = "N/A"
        print(f"No live reading available for sensor '{this_sensor_type_id}' yet.")
        return

    reading = st.session_state["last_live_sensor_reading"][this_sensor_type_id]
    timestamp = st.session_state["last_live_sensor_reading_time"][this_sensor_type_id]
    st.metric(label="Raw Sensor Reading", value=reading)
    st.caption(f"Last reading received at: **{timestamp}**")

render_live_sensor_reading()
st.divider()

st.subheader(f"{selected_sensor} Sensor Calibration")
st.markdown(f"**Warning:** Changes will not be saved until you click the 'Save Changes' button.")
st.divider()

# put buttons on top and on bottom to reduce scrolling
# revert_button_top = st.button(label="Revert Changes", key="revert_button_top", type="secondary")
# save_button_top = st.button(label="Save Changes", key="save_button_top", type="primary")

# Display each parameter and its value in the JSON config file
for key, val in sensor_config.items():
    assert isinstance(val, dict)
    original_value = val.get("val", None)
    tp = val.get("type", None)
    writable = val.get("write", False)
    options = val.get("options", None)

    # col1 displays param name, col2 displays param value
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown(f"***{key}***")

    with col2:
        assert isinstance(val, dict)
        # Display the value if it is not writable
        if not writable:
            st.markdown(f"**{original_value}** (read-only)")

        # Select from dropdown if options are provided
        elif options is not None and len(options) > 0:
            assert isinstance(options, dict)
            # val_li is the list of actual values
            val_li = list(options.values())
            # key_li is the list of descriptive names for the values to be displayed in the dropdown
            key_li = list(options.keys())
            if original_value not in val_li:
                raise ValueError(f"Original value '{original_value}' not in options for parameter '{key}'")

            # a unique identifier for the new value in the session state
            widget_key = f"{selected_sensor}_{key}"
            # set default option to be current value
            selected_option = st.selectbox(
                label=f"Select from dropdown",
                options=key_li,
                index=val_li.index(original_value),
                label_visibility="collapsed",
                key=widget_key,
            )

        # Free input with type check if no options are provided
        else:
            widget_key = f"{selected_sensor}_{key}"
            if tp == "int":
                new_value = st.number_input(
                    label=f"Enter {tp}",
                    value=original_value,
                    step=1,
                    format="%d",
                    label_visibility="collapsed",
                    key=widget_key,
                )
            elif tp == "float":
                new_value = st.number_input(
                    label=f"Enter {tp}",
                    value=original_value,
                    step=0.001,
                    format="%.3f",
                    label_visibility="collapsed",
                    key=widget_key,
                )
            elif tp == "str":
                new_value = st.text_input(
                    label=f"Enter {tp}",
                    value=original_value,
                    label_visibility="collapsed",
                    key=widget_key,
                )
            else:
                raise ValueError(f"Other error occurred")

    st.divider()

def save_config():
    """
    Save the updated config to cache and write to the JSON file.
    """
    for key, value in sensor_config.items():
        widget_key = f"{selected_sensor}_{key}"
        if widget_key in st.session_state:
            new_value = st.session_state[widget_key]

            if "options" in value and value["options"] is not None:
                # If the parameter has options, map the selected option back to its actual value
                options = value["options"]
                if new_value not in options:
                    raise ValueError(f"Selected option '{new_value}' is not valid for parameter '{key}'")
                new_value = options[new_value]
            else:
                # if no options provided, check the type of the new value
                if "type" not in value:
                    raise ValueError(f"Parameter '{key}' must have a 'type' key.")
                tp = value["type"]
                if tp == "int" and not isinstance(new_value, int):
                    raise ValueError(f"Expected int for parameter, got {type(new_value).__name__}")
                elif tp == "float" and not isinstance(new_value, float):
                    raise ValueError(f"Expected float for parameter, got {type(new_value).__name__}")
                elif tp == "str" and not isinstance(new_value, str):
                    raise ValueError(f"Expected string for parameter, got {type(new_value).__name__}")
            
            # write new value to the cached config
            value["val"] = new_value
    config_utils.save_config(selected_sensor, sensor_config)
    st.session_state[config_key] = config_utils.load_config(selected_sensor)
    print(f"Saved updated config for {selected_sensor} successfully.")

def revert_config():
    """
    Revert the config to the original values from the JSON file.
    """
    # Reload the original config from file
    st.session_state[config_key] = config_utils.load_config(selected_sensor)
    sensor_config = st.session_state[config_key]
    for key, value in sensor_config.items():
        assert isinstance(value, dict)
        widget_key = f"{selected_sensor}_{key}"
        if widget_key in st.session_state:
            # Skip read-only parameters
            if "write" in value and not value["write"]:
                continue
            # Reset the session state value to the original value
            st.session_state[widget_key] = value.get("val", None)

save_trigger = st.button(label="Save Changes", type="primary", on_click=save_config)
revert_trigger = st.button(label="Revert Changes", type="secondary", on_click=revert_config)
