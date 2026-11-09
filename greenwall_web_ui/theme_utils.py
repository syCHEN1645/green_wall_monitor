from __future__ import annotations

import streamlit as st

SIDEBAR_COMPANY_NAME = "E&ST Environmental"

LIGHT_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
        background: linear-gradient(180deg, #f3f5f7 0%, #ffffff 100%) !important;
        color: #2a2f36 !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
    }

    .stApp {
        font-size: 1.05rem !important;
        line-height: 1.5 !important;
    }

    .stSidebar {
        background: rgba(255,255,255,0.9) !important;
        border-right: 1px solid rgba(42,47,54,0.12) !important;
        color: #2a2f36 !important;
    }

    .stSidebar > div {
        padding-top: 0.8rem !important;
    }

    .stSidebar .stSelectbox, .stSidebar .stTextInput, .stSidebar .stDateInput, .stSidebar .stTimeInput,
    .stSidebar .stMultiselect, .stSidebar .stCheckbox, .stSidebar .stRadio, .stSidebar label,
    .stSidebar .stMarkdown, .stSidebar .stButton button {
        color: #2a2f36 !important;
    }

    .stSidebar .block-container {
        padding-top: 0.5rem !important;
    }

    .sidebar-brand {
        display: block;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
        color: #2a2f36 !important;
        padding: 0.3rem 0.6rem 0.7rem 0.6rem !important;
        border-bottom: 1px solid rgba(42,47,54,0.12);
        margin-bottom: 0.5rem;
        white-space: nowrap;
    }

    h1, h2, h3, .stSubheader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #2a2f36 !important;
        letter-spacing: -0.02em !important;
    }

    p, li, span, div, label, .stTextInput input, .stTextArea textarea, .stSelectbox div,
    .stDateInput input, .stTimeInput input, .stNumberInput input, .stCheckbox label,
    .stMarkdown, .stCaption, .stRadio label, .stMetric {
        color: #2a2f36 !important;
    }

    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(180deg, #f5f7fa 0%, #edf1f5 100%) !important;
        color: #2a2f36 !important;
        border: 1px solid rgba(42,47,54,0.16) !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(15,23,42,0.06) !important;
        font-weight: 600 !important;
        padding: 0.65rem 1rem !important;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: rgba(42,47,54,0.24) !important;
        background: #edf1f5 !important;
    }

    .stButton > button:focus, .stDownloadButton > button:focus,
    .stSelectbox [role="combobox"]:focus, .stTextInput input:focus,
    .stDateInput input:focus, .stTimeInput input:focus {
        outline: 2px solid rgba(98, 114, 135, 0.35) !important;
        outline-offset: 1px;
    }

    .stSelectbox [role="combobox"], .stTextInput input, .stDateInput input, .stTimeInput input,
    .stMultiSelect [role="combobox"], .stNumberInput input, .stTextArea textarea {
        background: rgba(255,255,255,0.95) !important;
        color: #2a2f36 !important;
        border: 1px solid rgba(42,47,54,0.18) !important;
        border-radius: 8px !important;
    }

    .stSelectbox [role="combobox"], .stMultiSelect [role="combobox"] {
        box-shadow: inset 0 1px 2px rgba(15,23,42,0.02);
    }

    .stDataFrame table {
        border-collapse: collapse !important;
        border: 1px solid rgba(42,47,54,0.12) !important;
        background: white !important;
    }

    .stDataFrame th {
        background: #f2f5f8 !important;
        color: #2a2f36 !important;
        font-weight: 700 !important;
        border-bottom: 1px solid rgba(42,47,54,0.16) !important;
    }

    .stDataFrame td {
        color: #2a2f36 !important;
        border-bottom: 1px solid rgba(42,47,54,0.08) !important;
    }

    .stDataFrame tbody tr:nth-child(even) {
        background: rgba(247, 249, 251, 0.80) !important;
    }

    .stDataFrame tbody tr:hover {
        background: rgba(232, 238, 244, 0.8) !important;
    }

    .stAlert {
        border-radius: 10px !important;
        color: #2a2f36 !important;
    }

    .plotly .svg-container {
        background: rgba(255,255,255,0.9) !important;
        border: 1px solid rgba(42,47,54,0.08) !important;
        border-radius: 12px !important;
    }

    .js-plotly-plot .plotly .modebar {
        background: rgba(255,255,255,0.8) !important;
    }

    .plotly text, .plotly .legendtext, .plotly .xtick text, .plotly .ytick text,
    .plotly .axis-title, .plotly .annotation-text {
        fill: #2a2f36 !important;
        color: #2a2f36 !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
    }

    .plotly .legendtitletext {
        fill: #2a2f36 !important;
        color: #2a2f36 !important;
        font-weight: 600 !important;
    }

    .plotly .gridlayer .xgrid, .plotly .gridlayer .ygrid {
        stroke: rgba(42,47,54,0.12) !important;
    }

    .plotly .axis-line, .plotly .xaxis-line, .plotly .yaxis-line {
        stroke: rgba(42,47,54,0.28) !important;
    }

    ::placeholder {
        color: rgba(42,47,54,0.6) !important;
    }

    [disabled] {
        opacity: 0.55 !important;
        cursor: not-allowed !important;
    }
</style>
"""


def apply_shared_theme() -> None:
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_sidebar_company_name() -> None:
    with st.sidebar:
        st.markdown(f'<div class="sidebar-brand">{SIDEBAR_COMPANY_NAME}</div>', unsafe_allow_html=True)
