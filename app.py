"""Main Streamlit Application Entrypoint & Workstation Router.

AI-Based Multimodal Surveillance System for Threat Detection and Decision Support
"""

import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title="Surveillance Intelligence Workstation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.core.di_container import DIContainer
from src.ui.styles import inject_custom_css
from src.ui.pages.dashboard import render_workspace_page
from src.ui.pages.surveillance import (
    render_detection_view, render_tracking_view,
    render_threat_assessment_view, render_explainability_view
)
from src.ui.pages.history import render_review_audit_page
from src.ui.pages.analytics import render_analytics_page
from src.ui.pages.settings import render_model_system_page


def main() -> None:
    # 1. Initialize Core DI Container & Database Seeding
    container = DIContainer()

    # 2. Inject Dark Workstation Styling
    inject_custom_css()

    # 3. Sidebar Navigation Structure
    st.sidebar.markdown("### 🛡️ Surveillance Workstation")
    st.sidebar.caption("AI-Based Multimodal Threat Detection | v1.0.0")
    st.sidebar.markdown("---")

    # Final Navigation: Eight Functional Views
    nav_options = [
        "1. Workspace",
        "2. Detection",
        "3. Tracking",
        "4. Threat Assessment",
        "5. Explainability",
        "6. Review & Audit",
        "7. Analytics",
        "8. Model & System"
    ]

    # Handle contextual navigation overrides from buttons/session state
    default_nav = st.session_state.get("nav_selection", "1. Workspace")
    default_index = 0
    for idx, opt in enumerate(nav_options):
        if opt == default_nav or opt.endswith(default_nav) or default_nav in opt:
            default_index = idx
            break

    selected_page = st.sidebar.radio(
        "Workstation Navigation",
        options=nav_options,
        index=default_index,
        key="main_nav_radio"
    )
    st.session_state["nav_selection"] = selected_page

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Operating Mode:** 🔒 Offline Secure")
    st.sidebar.markdown("**Database:** 🟢 Connected (SQLite)")
    st.sidebar.markdown("**Model Checkpoint:** `yolov8n_kiit_mita.pt`")

    # 4. View Router
    if selected_page == "1. Workspace":
        render_workspace_page()
    elif selected_page == "2. Detection":
        render_detection_view()
    elif selected_page == "3. Tracking":
        render_tracking_view()
    elif selected_page == "4. Threat Assessment":
        render_threat_assessment_view()
    elif selected_page == "5. Explainability":
        render_explainability_view()
    elif selected_page == "6. Review & Audit":
        render_review_audit_page()
    elif selected_page == "7. Analytics":
        render_analytics_page()
    elif selected_page == "8. Model & System":
        render_model_system_page()


if __name__ == "__main__":
    main()
