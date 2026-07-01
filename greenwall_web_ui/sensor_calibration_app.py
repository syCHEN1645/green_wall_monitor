import streamlit as st

import config_utils

st.set_page_config(page_title="Sensor Calibration", layout="wide")
st.title("Sensor Calibration")

config_data = config_utils.load_config(config_utils.PH_NAME)