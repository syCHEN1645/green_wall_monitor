from __future__ import annotations

import streamlit as st


COMPANY_NAME = "E&ST Environmental"


LIGHT_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f3f5f7 0%, #ffffff 100%) !important;
        color: #2a2f36 !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
    }

    .stApp {
        font-size: 1.05rem !important;
        line-height: 1.5 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.96) !important;
        border-right: 1px solid rgba(42, 47, 54, 0.12) !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.8rem !important;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 0.5rem !important;
    }

    /* Sidebar labels and text */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #2a2f36 !important;
    }

    /* Text inputs, date inputs, time inputs, number inputs, and text areas */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background-color: #f4f6f8 !important;
        color: #2a2f36 !important;
        -webkit-text-fill-color: #2a2f36 !important;
        caret-color: #2a2f36 !important;
        border: 1px solid #b8c2cc !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #6c757d !important;
        opacity: 1 !important;
    }

    /* Date/time input wrappers */
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        background-color: #f4f6f8 !important;
        border-color: #b8c2cc !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="base-input"] input {
        background-color: #f4f6f8 !important;
        color: #2a2f36 !important;
        -webkit-text-fill-color: #2a2f36 !important;
    }

    /* Selectbox and multiselect visible controls */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #f4f6f8 !important;
        color: #2a2f36 !important;
        border-color: #b8c2cc !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        color: #2a2f36 !important;
    }

    /* Multiselect tags */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: #e5ebf0 !important;
        border: 1px solid #c5d0d9 !important;
        border-radius: 6px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="tag"] svg {
        fill: #2a2f36 !important;
        color: #2a2f36 !important;
    }

    /* Dropdown menus and options.
       These may be rendered outside the sidebar by BaseWeb. */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: #ffffff !important;
        color: #2a2f36 !important;
        border: 1px solid #c5d0d9 !important;
    }

    [data-baseweb="popover"] *,
    [data-baseweb="menu"] *,
    [role="listbox"] *,
    [role="option"] {
        color: #2a2f36 !important;
    }

    [role="option"] {
        background-color: #ffffff !important;
    }

    [role="option"]:hover,
    [role="option"][aria-selected="true"] {
        background-color: #e9eef2 !important;
        color: #212529 !important;
    }

    /* Checkboxes and radio controls */
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #2a2f36 !important;
    }

    [data-testid="stSidebar"] [data-testid="stCheckbox"] p,
    [data-testid="stSidebar"] [data-testid="stRadio"] p {
        color: #2a2f36 !important;
    }

    /* Focus states */
    [data-testid="stSidebar"] input:focus,
    [data-testid="stSidebar"] textarea:focus,
    [data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within {
        background-color: #ffffff !important;
        color: #212529 !important;
        border-color: #6c9bcf !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(108, 155, 207, 0.25) !important;
    }

    /* Fallback for controls that remain dark because of browser styling */
    [data-testid="stSidebar"] input[type="date"],
    [data-testid="stSidebar"] input[type="time"] {
        color-scheme: light !important;
    }

    /* Top bar */
    .topbar-brand-wrap {
        position: sticky;
        top: 0;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(8px);
        padding: 0.45rem 0 0.7rem 0;
        margin: -0.5rem 0 0.75rem 0;
        border-bottom: 1px solid rgba(42, 47, 54, 0.12);
    }

    .topbar-brand {
        display: inline-block;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
        color: #2a2f36 !important;
        padding: 0.25rem 0.5rem 0.35rem 0.1rem !important;
        white-space: nowrap;
    }

    .sidebar-brand {
        display: none !important;
    }

    /* General text */
    h1,
    h2,
    h3,
    .stSubheader,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3 {
        color: #2a2f36 !important;
        letter-spacing: -0.02em !important;
    }

    p,
    li,
    label,
    .stMarkdown,
    .stCaption,
    .stMetric {
        color: #2a2f36 !important;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(180deg, #f5f7fa 0%, #edf1f5 100%) !important;
        color: #2a2f36 !important;
        border: 1px solid rgba(42, 47, 54, 0.16) !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) !important;
        font-weight: 600 !important;
        padding: 0.65rem 1rem !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(42, 47, 54, 0.24) !important;
        background: #edf1f5 !important;
    }

    .stButton > button:focus,
    .stDownloadButton > button:focus {
        outline: 2px solid rgba(98, 114, 135, 0.35) !important;
        outline-offset: 1px !important;
    }

    /* Table */
    [data-testid="stDataFrame"] {
        background: #ffffff !important;
        border: 1px solid rgba(42, 47, 54, 0.12) !important;
    }

    .stDataFrame table {
        border-collapse: collapse !important;
        background: #ffffff !important;
    }

    .stDataFrame th {
        background: #f2f5f8 !important;
        color: #2a2f36 !important;
        font-weight: 700 !important;
        border-bottom: 1px solid rgba(42, 47, 54, 0.16) !important;
    }

    .stDataFrame td {
        color: #2a2f36 !important;
        border-bottom: 1px solid rgba(42, 47, 54, 0.08) !important;
    }

    /* Alerts */
    .stAlert {
        border-radius: 10px !important;
        color: #2a2f36 !important;
    }

    /* Plot */
    .plotly .svg-container {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(42, 47, 54, 0.08) !important;
        border-radius: 12px !important;
    }

    .js-plotly-plot .plotly .modebar {
        background: rgba(255, 255, 255, 0.8) !important;
    }

    .plotly text,
    .plotly .legendtext,
    .plotly .xtick text,
    .plotly .ytick text,
    .plotly .axis-title,
    .plotly .annotation-text {
        fill: #2a2f36 !important;
        color: #2a2f36 !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
    }

    .plotly .legendtitletext {
        fill: #2a2f36 !important;
        color: #2a2f36 !important;
        font-weight: 600 !important;
    }

    .plotly .gridlayer .xgrid,
    .plotly .gridlayer .ygrid {
        stroke: rgba(42, 47, 54, 0.12) !important;
    }

    .plotly .axis-line,
    .plotly .xaxis-line,
    .plotly .yaxis-line {
        stroke: rgba(42, 47, 54, 0.28) !important;
    }

    ::placeholder {
        color: rgba(42, 47, 54, 0.6) !important;
        opacity: 1 !important;
    }

    [disabled] {
        opacity: 0.55 !important;
        cursor: not-allowed !important;
    }
</style>
"""


def apply_shared_theme() -> None:
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_topbar_company_name() -> None:
    st.markdown(
        (
            '<div class="topbar-brand-wrap">'
            f'<div class="topbar-brand">{COMPANY_NAME}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_sidebar_company_name() -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-brand">{COMPANY_NAME}</div>',
            unsafe_allow_html=True,
        )