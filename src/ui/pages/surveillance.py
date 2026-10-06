"""Detailed Surveillance Workstation Views Module: Detection, Tracking, Threat Assessment, Explainability."""

import io
import json
import streamlit as st
import pandas as pd
from PIL import Image
from src.core.di_container import DIContainer
from src.ui.components import (
    render_section_header, render_alert_banner,
    render_threat_badge, MILITARY_CLASSES
)


def _get_active_response():
    """Helper to retrieve the active analysis response from session state."""
    resp = st.session_state.get("active_analysis_response")
    if not resp:
        st.info("No active analysis result selected. Please run an analysis in the Workspace first.")
    return resp


def render_detection_view() -> None:
    """Renders the dedicated Computer Vision Detection View."""
    render_section_header(
        "Military Object Detection View",
        "Visual bounding box inspection, entity class breakdown, and confidence telemetry"
    )

    render_alert_banner(
        "Notice: Detections are model observations and are not proof of hostile activity.",
        banner_type="notice"
    )

    resp = _get_active_response()
    if not resp:
        return

    # Visual Side-by-Side Frame Comparison
    st.markdown("#### Side-by-Side Visual Inspection")
    col_orig, col_annot = st.columns(2)

    with col_orig:
        st.markdown("**Original Input Frame**")
        if hasattr(resp, "original_image_bytes") and resp.original_image_bytes:
            st.image(resp.original_image_bytes, use_container_width=True, caption="Unprocessed Media Input")
        elif hasattr(resp, "annotated_video_bytes") and resp.annotated_video_bytes:
            st.info("Video Media: Displaying analyzed video stream below.")
        else:
            st.warning("Original media bytes unavailable.")

    with col_annot:
        st.markdown("**YOLOv8 Bounding Box Annotations**")
        if hasattr(resp, "annotated_image_bytes") and resp.annotated_image_bytes:
            st.image(resp.annotated_image_bytes, use_container_width=True, caption="YOLOv8 Annotated Bounding Boxes")
        elif hasattr(resp, "annotated_video_bytes") and resp.annotated_video_bytes:
            st.video(resp.annotated_video_bytes)
            st.caption("Analyzed Sampled Video Output")

    st.markdown("---")
    st.markdown("#### Detected Military Entities")

    detections = getattr(resp, "detections", [])
    if not detections:
        st.info("Zero military objects detected in the current media sector.")
        return

    det_table = []
    for idx, d in enumerate(detections, 1):
        bbox_str = f"({d.bbox.x_min:.0f}, {d.bbox.y_min:.0f}, {d.bbox.x_max:.0f}, {d.bbox.y_max:.0f})" if hasattr(d, "bbox") and d.bbox else "N/A"
        det_table.append({
            "#": idx,
            "Class Name": d.class_name,
            "Confidence": f"{d.confidence:.1%}",
            "Bounding Box (x_min, y_min, x_max, y_max)": bbox_str,
            "Detection ID": getattr(d, "detection_id", "N/A")[:8] + "..."
        })

    st.dataframe(det_table, use_container_width=True)
    st.caption(f"Total Detections: **{len(detections)}** | Configured Classes: {', '.join(MILITARY_CLASSES)}")


def render_tracking_view() -> None:
    """Renders the dedicated Multi-Object Video Tracking View."""
    render_section_header(
        "Multi-Object Tracking View",
        "Target trajectory tracking, movement states, and image-space pixel displacement"
    )

    resp = _get_active_response()
    if not resp:
        return

    tracks = getattr(resp, "tracks", None)
    if tracks is None:
        st.info("ℹ️ Tracking is available for video analyses. Single image analyses do not generate time-series trajectories.")
        return

    render_alert_banner(
        "Technical Disclaimers: 1. Tracking is based on sampled video frames. 2. Movement measurements are image-space pixel displacement, not calibrated real-world speed. 3. Camera views are not automatically spatially aligned.",
        banner_type="notice"
    )

    st.markdown("#### Active Target Track Telemetry")
    if not tracks:
        st.info("Zero active target tracks recorded for this video feed.")
        return

    track_table = []
    for t in tracks:
        track_table.append({
            "Track ID": f"Track #{t.track_id}",
            "Class Name": t.class_name,
            "First Frame": t.first_frame,
            "Last Frame": t.last_frame,
            "Total Detections": t.detection_count,
            "Avg Confidence": f"{t.avg_confidence:.1%}",
            "Movement State": t.movement_state,
            "Displacement": f"{t.pixel_displacement:.1f} px",
            "Trajectory Direction": t.trajectory_direction
        })

    st.dataframe(track_table, use_container_width=True)


def render_threat_assessment_view() -> None:
    """Renders the Evidence-Based Threat Assessment View."""
    render_section_header(
        "Contextual Threat Assessment View",
        "Evidence-based threat scoring, factor contributions, and spatial context isolation"
    )

    resp = _get_active_response()
    if not resp:
        return

    assessment = getattr(resp, "threat_assessment", None)
    if not assessment:
        st.info("Threat assessment unavailable for selected analysis.")
        return

    # Severity Card
    st.markdown("#### Overall Threat Severity")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Threat Score", f"{assessment.threat_score:.1f} / 100")
    with col2:
        st.metric("Threat Level", assessment.threat_level)
    with col3:
        st.markdown(f"**Severity Status:** {render_threat_badge(assessment.threat_level)}", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Threat Score Formula Breakdown")
    st.caption("Scoring Rules: Object presence (+5 baseline) | Verified Zone Signal (+65) | Verified Access Signal (+20)")

    factors = getattr(assessment, "factors", [])
    if factors:
        factor_table = [
            {
                "Factor Name": f.factor_name,
                "Score Delta": f"+{f.score_delta:.1f}" if f.score_delta > 0 else f"{f.score_delta:.1f}",
                "Description": f.description
            }
            for f in factors
        ]
        st.dataframe(factor_table, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Separate Spatial/Contextual Assessment")
    sep_spatial = getattr(resp, "separate_contextual_assessment", None)
    if sep_spatial:
        st.write(f"- **Spatial Threat Score:** {sep_spatial.spatial_threat_score:.1f} / 100 ({sep_spatial.spatial_threat_level})")
        st.write(f"- **Computed Spatial Breach:** `{'YES' if sep_spatial.computed_spatial_breach else 'NO'}`")
        st.caption(f"Spatial XAI Reason: {sep_spatial.xai_reason}")
    else:
        st.info("Separate spatial assessment evaluated outside configured restricted zones.")


def render_explainability_view() -> None:
    """Renders the Explainable AI (XAI) & SOP Decision Support View."""
    render_section_header(
        "Explainability & Decision Support View",
        "Transparent multi-factor rationale, evidence breakdown, and analyst SOP verification steps"
    )

    resp = _get_active_response()
    if not resp:
        return

    assessment = getattr(resp, "threat_assessment", None)
    detections = getattr(resp, "detections", [])

    # Section A
    st.markdown("#### A. What the Model Observed")
    if detections:
        class_counts = {}
        for d in detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1
        st.write(f"- **Total Entities Identified:** {len(detections)}")
        st.write("- **Class Counts:** " + ", ".join([f"**{count}** {cls}" for cls, count in class_counts.items()]))
    else:
        st.write("- Zero object detections observed in surveillance sector.")

    # Section B
    st.markdown("#### B. What Evidence Was Considered")
    scenario_name = getattr(resp, "scenario_name", "N/A")
    st.write(f"- **Scenario Context:** {scenario_name or 'Custom Upload'}")

    # Section C
    st.markdown("#### C. How Assessment Was Produced")
    if assessment:
        st.write(f"- **Final Threat Score:** {assessment.threat_score:.1f} / 100 ({assessment.threat_level})")
        st.write(f"- **XAI Rationale:** {assessment.xai_reason}")

    # Section D
    st.markdown("#### D. What the Analyst Should Verify")
    if assessment and hasattr(assessment, "recommended_sop") and assessment.recommended_sop:
        st.success(f"**Recommended SOP:** {assessment.recommended_sop}")
    else:
        st.info("Continue routine surveillance monitoring.")
