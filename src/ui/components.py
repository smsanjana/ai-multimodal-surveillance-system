"""Reusable UI Components for the Surveillance Intelligence Workstation."""

from typing import Optional, List, Dict, Any
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


MILITARY_CLASSES = [
    "Artilary",
    "Missile",
    "Radar",
    "M. Rocket Launcher",
    "Soldier",
    "Tank",
    "Vehicle"
]


def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Renders a styled workstation header with optional subtitle."""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="workstation-header">
        <h2>{title}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: Optional[str] = None) -> None:
    """Renders a workstation metric card."""
    delta_html = f'<div style="font-size: 0.8rem; color: #34D399; margin-top: 4px;">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-card-label">{label}</div>
        <div class="metric-card-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_threat_badge(threat_level: str) -> str:
    """Returns HTML string for a color-coded threat level badge."""
    level = (threat_level or "LOW").upper()
    css_class = f"threat-badge-{level.lower()}"
    return f'<span class="threat-badge {css_class}">{level}</span>'


def render_alert_banner(message: str, banner_type: str = "info") -> None:
    """Renders a styled alert banner."""
    css_class = f"alert-banner-{banner_type}"
    st.markdown(f"""
    <div class="alert-banner {css_class}">
        <span>ℹ️ {message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_workflow_stages(active_stage: str = "INPUT") -> None:
    """Renders 4-stage workflow progress indicator: INPUT -> ANALYSIS -> ASSESSMENT -> REVIEW."""
    stages = ["1. INPUT", "2. ANALYSIS", "3. ASSESSMENT", "4. REVIEW"]
    cols = st.columns(4)
    for idx, (col, stage_name) in enumerate(zip(cols, stages)):
        is_active = active_stage.upper() in stage_name.upper()
        style_color = "#38BDF8" if is_active else "#8B949E"
        font_weight = "700" if is_active else "500"
        with col:
            st.markdown(
                f'<div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 8px 12px; text-align: center; color: {style_color}; font-weight: {font_weight}; font-size: 0.85rem;">{stage_name}</div>',
                unsafe_allow_html=True
            )
    st.markdown("<br>", unsafe_allow_html=True)


def render_detection_trend_chart(detections_records: Optional[List[Any]] = None) -> go.Figure:
    """
    Generates a Plotly bar chart for military object class frequencies using database records.
    Strictly uses the 7 project military classes.
    """
    class_counts = {cls_name: 0 for cls_name in MILITARY_CLASSES}

    if detections_records:
        for d in detections_records:
            c_name = getattr(d, "class_name", "")
            if c_name in class_counts:
                class_counts[c_name] += 1

    df = pd.DataFrame({
        "Class": list(class_counts.keys()),
        "Detections": list(class_counts.values())
    })

    fig = px.bar(
        df,
        x="Class",
        y="Detections",
        title="Military Object Class Frequency (Database Records)",
        color="Class",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C9D1D9"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=280,
        showlegend=False
    )
    return fig


def render_threat_distribution_chart(records: Optional[List[Any]] = None) -> go.Figure:
    """Generates a Plotly threat severity distribution pie chart from database records."""
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    if records:
        for r in records:
            lvl = (getattr(r, "threat_level", "LOW") or "LOW").upper()
            if lvl in counts:
                counts[lvl] += 1

    labels = list(counts.keys())
    values = list(counts.values())

    fig = px.pie(
        names=labels,
        values=values,
        title="Threat Severity Level Distribution",
        hole=0.4,
        color=labels,
        color_discrete_map={
            "LOW": "#059669",
            "MEDIUM": "#D97706",
            "HIGH": "#EA580C",
            "CRITICAL": "#DC2626"
        }
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C9D1D9"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=280
    )
    return fig
