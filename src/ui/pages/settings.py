"""Model & System View Module for Runtime Configuration and Technical Status."""

import os
import streamlit as st
from src.core.di_container import DIContainer
from src.infrastructure.database.repositories import SettingsRepository
from src.ui.components import render_section_header, MILITARY_CLASSES


def render_model_system_page() -> None:
    """Renders the Model & System technical overview."""
    render_section_header(
        "Model & System Architecture Overview",
        "Technical status of computer vision models, dataset specifications, and database connectivity"
    )

    container = DIContainer()
    settings_repo = container.resolve(SettingsRepository)

    # 1. Model Status Section
    st.markdown("#### 1. Computer Vision Detection Model Status")
    model_path = settings_repo.get("ai.model_path", "data/models/yolov8n_kiit_mita.pt")
    file_exists = os.path.exists(model_path)
    file_size_mb = f"{os.path.getsize(model_path) / (1024 * 1024):.1f} MB" if file_exists else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Model Architecture", "YOLOv8n (Nano)")
    with c2:
        st.metric("Parameters", "3.0 Million")
    with c3:
        st.metric("Checkpoint File", "EXISTS" if file_exists else "MISSING")
    with c4:
        st.metric("Checkpoint Size", file_size_mb)

    st.write(f"- **Configured Model Path:** `{model_path}`")
    st.write(f"- **Model Status:** `{'🟢 ACTIVE & LOADED' if file_exists else '🔴 CHECKPOINT FILE NOT FOUND'}`")
    st.write(f"- **Supported Object Classes (7 Classes):** `{', '.join(MILITARY_CLASSES)}`")

    st.markdown("---")

    # 2. Dataset Information Section
    st.markdown("#### 2. KIIT-MiTA Military Dataset Information")
    st.caption("Documented dataset split counts for the fine-tuned military detection model:")

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("Total Cleaned Dataset", "1,681 Images")
    with d2:
        st.metric("Train Split", "1,341 Images")
    with d3:
        st.metric("Validation Split", "170 Images")
    with d4:
        st.metric("Held-out Test Split", "170 Images")

    st.write("- **Dataset Location:** `data/datasets/military/KIIT-MiTA/` (Cleaned: `KIIT-MiTA_cleaned/`)")

    st.markdown("---")

    # 3. System Environment & Database Status Section
    st.markdown("#### 3. System Environment & Infrastructure Status")

    db_path = "data/surveillance.db"
    db_exists = os.path.exists(db_path)
    db_size_mb = f"{os.path.getsize(db_path) / (1024 * 1024):.2f} MB" if db_exists else "0 MB"

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Operating Mode", "🔒 Offline Secure")
    with s2:
        st.metric("Database System", "SQLite 3")
    with s3:
        st.metric("Database File Size", db_size_mb)

    st.write(f"- **Database Storage Path:** `{db_path}`")
    st.write(f"- **Database Connection Status:** `{'🟢 CONNECTED' if db_exists else '🔴 DB NOT FOUND'}`")
