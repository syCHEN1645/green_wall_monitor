import streamlit as st

from theme_utils import apply_shared_theme, render_sidebar_company_name

# Configure page parameters (Must be the first Streamlit command executed)
st.set_page_config(page_title="Main Menu", layout="wide")
apply_shared_theme()
render_sidebar_company_name()

st.title("Main Menu")
st.markdown("---")

# Create grid columns for navigation shortcuts right on the main hub canvas
col1, col2 = st.columns(2)

with col1:
    st.subheader("Data Viewer", text_alignment="center")
    if st.button("Data Viewer", type="secondary", icon="📊", use_container_width=True):
        st.switch_page("pages/1_data_viewer_app.py")

with col2:
    st.subheader("Sensor Calibration", text_alignment="center")
    if st.button("Sensor Calibration Page", type="secondary", icon="⚙️", use_container_width=True):
        st.switch_page("pages/2_sensor_calibration_app.py")

st.divider()
st.info("Use the sidebar navigation menu to jump between operations spaces at any time.")