import socket
import select
import json
import streamlit as st

import config_utils

RECV_PORT = 5006

st.set_page_config(page_title="Sensor Calibration", layout="wide")
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

st.subheader(f"{selected_sensor} Real-time Raw Sensor Reading (V/mV)")

@st.fragment(run_every=1.0)
def render_live_sensor_reading():
    """
    Render the live sensor reading from the UDP server.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", RECV_PORT))
    except Exception as e:
        st.error(f"Error setting up UDP socket: {e}")
        return

    # check if a packet is waiting to be received
    # readable, writable, exceptional = select.select([s], [], [], 0.1)
    recv_states = select.select([s], [], [], 0.1)
    if recv_states[0]:
        try:
            data, addr = s.recvfrom(1024)
            payload = data.decode("utf-8")

            # TODO: parse payload
            reading = 1
            st.metric(label="Raw Sensor Reading", value=reading)
        except Exception as e:
            st.error(f"Error receiving data: {e}")
        finally:
            s.close()

render_live_sensor_reading()
st.divider()

st.subheader(f"{selected_sensor} Sensor Calibration")
st.markdown(f"**Warning:** Changes will not be saved until you click the 'Save Changes' button.")
st.divider()

# JSON dict for the selected sensor
sensor_config = st.session_state[config_key]
assert isinstance(sensor_config, dict)

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
