"""About Documentation View Module."""

import streamlit as st
from src.ui.components import render_section_header


def render_about_page() -> None:
    """Renders comprehensive project documentation and system overview."""
    render_section_header("About AI Surveillance Command Center", "System vision, Clean Architecture, and technical specifications")

    st.markdown("""
    ### Project Vision
    The **AI-Based Multimodal Surveillance System for Threat Detection and Decision Support** is an enterprise-grade AI Surveillance Command Center designed to assist security personnel in monitoring surveillance feeds, detecting suspicious activity, tracking movement, scoring threats, and making informed operational decisions.

    The system serves mission-critical control environments including **defense installations, border security, industrial facilities, airports, smart cities, and critical infrastructure**.

    ---

    ### Clean Architecture & Layering Model

    ```
    +-----------------------------------------------------------------------------------+
    | PRESENTATION LAYER (Streamlit Pages, Reusable Components, Custom CSS)             |
    +-----------------------------------------------------------------------------------+
                                            │
                                            ▼
    +-----------------------------------------------------------------------------------+
    | APPLICATION LAYER (Workflows, Orchestrators, Use Cases, DTOs)                      |
    +-----------------------------------------------------------------------------------+
                                            │
                                            ▼
    +-----------------------------------------------------------------------------------+
    | DOMAIN LAYER (Pure Python Business Logic, Threat Rules, Entities, Interfaces)     |
    +-----------------------------------------------------------------------------------+
                                            ▲
                                            │
    +-----------------------------------------------------------------------------------+
    | INFRASTRUCTURE LAYER (SQLite Repositories, DI Container, Logging, Config)         |
    +-----------------------------------------------------------------------------------+
    ```

    ---

    ### Approved Technology Stack
    - **Language:** Python 3.11+
    - **UI Framework:** Streamlit 1.56+
    - **Data Visualization:** Plotly 6.0+
    - **Persistence:** SQLite 3 (Native Driver & Repository Abstraction)
    - **Configuration & Logging:** PyYAML / Pydantic / Standard Logging
    - **Computer Vision Framework:** Ultralytics YOLOv8 & OpenCV (Specification 2+)
    - **Testing Framework:** Pytest

    ---

    ### SpecKit Governance Lifecycle
    This project is developed incrementally following the SpecKit Governance Lifecycle:
    $$\\text{/specify} \\longrightarrow \\text{/clarify} \\longrightarrow \\text{/plan} \\longrightarrow \\text{/tasks} \\longrightarrow \\text{/implement}$$

    > **Governing Documents:** Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`.
    """)
