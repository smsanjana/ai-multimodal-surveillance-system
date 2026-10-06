"""Dark Command Center & Surveillance Workstation CSS Styling Module."""

import streamlit as st


def inject_custom_css() -> None:
    """Injects professional dark-theme CSS for Streamlit controls, sidebar, badges, and cards."""
    custom_css = """
    <style>
    /* Global dark theme overrides */
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: #C9D1D9 !important;
        font-weight: 500;
        font-size: 0.9rem;
        padding: 6px 12px;
        border-radius: 6px;
        transition: background-color 0.15s ease;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #21262D;
    }

    /* Main Container Cards & Panels */
    .workstation-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    .metric-card-label {
        font-size: 0.75rem;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .metric-card-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F0F6FC;
    }

    /* Threat Severity Badges */
    .threat-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .threat-badge-low {
        background-color: #064E3B;
        color: #34D399;
        border: 1px solid #059669;
    }

    .threat-badge-medium {
        background-color: #78350F;
        color: #FBBF24;
        border: 1px solid #D97706;
    }

    .threat-badge-high {
        background-color: #7C2D12;
        color: #FB923C;
        border: 1px solid #EA580C;
    }

    .threat-badge-critical {
        background-color: #7F1D1D;
        color: #FCA5A5;
        border: 1px solid #DC2626;
    }

    /* Workflow Stage Indicator */
    .stage-indicator {
        display: flex;
        justify-content: space-between;
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 20px;
    }

    .stage-item {
        font-size: 0.85rem;
        font-weight: 600;
        color: #8B949E;
    }

    .stage-item.active {
        color: #38BDF8;
    }

    .stage-item.complete {
        color: #34D399;
    }

    /* Section Header */
    .workstation-header {
        border-bottom: 1px solid #30363D;
        padding-bottom: 10px;
        margin-bottom: 18px;
    }

    .workstation-header h2 {
        color: #F0F6FC;
        font-size: 1.35rem;
        font-weight: 600;
        margin: 0;
    }

    .workstation-header p {
        color: #8B949E;
        font-size: 0.85rem;
        margin: 4px 0 0 0;
    }

    /* Alert Banner */
    .alert-banner {
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 14px;
        font-size: 0.875rem;
        font-weight: 500;
    }

    .alert-banner-warning {
        background-color: #451A03;
        color: #FCD34D;
        border: 1px solid #B45309;
    }

    .alert-banner-info {
        background-color: #0C2D48;
        color: #38BDF8;
        border: 1px solid #0284C7;
    }

    .alert-banner-notice {
        background-color: #161B22;
        color: #C9D1D9;
        border: 1px solid #30363D;
    }

    /* Tables */
    .stDataFrame {
        border: 1px solid #30363D !important;
        border-radius: 6px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
