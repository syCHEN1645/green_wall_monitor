import streamlit as st

import config_utils

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

config_data = config_utils.load_config(selected_sensor)
st.subheader(f"{selected_sensor} Sensor Calibration")
st.markdown(f"**Warning:** Changes will not be saved until you click the 'Save Changes' button.")
st.divider()

# JSON dict for the selected sensor
sensor_config = config_utils.load_config(selected_sensor)
assert isinstance(sensor_config, dict)

def update_new_value(param: dict, key: str):
    """
    Update new value in the cached config (not saved to file yet) after type check. 
    Deal with parameters that have "options" differently.

    Args:
        param (dict): The parameter dictionary to update.
        key (str): The key for the parameter in the session state.
    """
    if "type" not in param:
        raise ValueError("Parameter dictionary must contain a 'type' key.")
    if "val" not in param:
        raise ValueError("Parameter dictionary must contain a 'val' key.")
    
    if "options" not in param:
        new_val = st.session_state.get(key, None)
    else:
        k = st.session_state.get(key, None)
        assert isinstance(param["options"], dict)
        new_val = param["options"].get(k, None)

    if new_val is None:
        raise ValueError("New value is not found or is None.")
    
    tp = param["type"]
    if tp == "int" and not isinstance(new_val, int):
        raise ValueError(f"Expected int for parameter, got {type(new_val).__name__}")
    elif tp == "float" and not isinstance(new_val, float):
        raise ValueError(f"Expected float for parameter, got {type(new_val).__name__}")
    elif tp == "str" and not isinstance(new_val, str):
        raise ValueError(f"Expected string for parameter, got {type(new_val).__name__}")
    param.update({"val": new_val})

# Display each parameter and its value in the JSON config file
for key, val in sensor_config.items():
    assert isinstance(val, dict)
    original_value = val.get("val", None)
    tp = val.get("type", None)
    writable = val.get("write", False)
    options = val.get("options", None)

    # col1 displays param name, col2 displays param value
    col1, col2 = st.columns([1, 2])

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
                on_change=update_new_value,
                args=(val, widget_key)
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
                    on_change=update_new_value,
                    args=(val, widget_key)
                )
            elif tp == "float":
                new_value = st.number_input(
                    label=f"Enter {tp}",
                    value=original_value,
                    step=0.001,
                    format="%.3f",
                    label_visibility="collapsed",
                    key=widget_key,
                    on_change=update_new_value,
                    args=(val, widget_key)
                )
            elif tp == "str":
                new_value = st.text_input(
                    label=f"Enter {tp}",
                    value=original_value,
                    label_visibility="collapsed",
                    key=widget_key,
                    on_change=update_new_value,
                    args=(val, widget_key)
                )
            else:
                raise ValueError(f"Other error occurred")

st.divider()
st.button("Save Changes", on_click=config_utils.save_config, args=(selected_sensor, sensor_config))