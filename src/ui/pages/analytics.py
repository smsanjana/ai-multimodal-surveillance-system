"""Analytics View Module for Database-Driven Statistical Metrics."""

import streamlit as st
import plotly.express as px
import pandas as pd
from src.core.di_container import DIContainer
from src.infrastructure.database.repositories import AnalysisRepository, AnalystReviewRepository
from src.ui.components import (
    render_section_header, render_detection_trend_chart,
    render_threat_distribution_chart, MILITARY_CLASSES
)


def render_analytics_page() -> None:
    """Renders database-driven operational analytics dashboard."""
    render_section_header("Database Analytics & Operational Intelligence", "Statistical metrics computed directly from stored surveillance records")

    container = DIContainer()
    analysis_repo = container.resolve(AnalysisRepository)
    review_repo = container.resolve(AnalystReviewRepository)

    analyses = analysis_repo.get_all()

    if not analyses:
        st.info("ℹ️ No analysis records found in the database. Run an analysis in the Workspace first to generate operational analytics.")
        return

    # Fetch all detection records from DB
    all_detections = []
    for a in analyses:
        all_detections.extend(analysis_repo.get_detections_by_analysis_id(a.id))

    # Top Metrics
    total_count = len(analyses)
    crit_count = sum(1 for a in analyses if a.threat_level == 'CRITICAL')
    crit_rate = f"{(crit_count / total_count * 100):.1f}%"
    mean_lat = f"{sum(a.processing_time_ms for a in analyses) / total_count:.0f} ms"
    mean_conf = f"{sum(a.confidence_avg for a in analyses) / total_count:.1%}"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Stored Analyses", total_count)
    with c2:
        st.metric("Critical Incident Rate", crit_rate)
    with c3:
        st.metric("Mean Latency", mean_lat)
    with c4:
        st.metric("Mean Confidence", mean_conf)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Grid
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.plotly_chart(render_detection_trend_chart(all_detections), use_container_width=True)
    with row1_c2:
        st.plotly_chart(render_threat_distribution_chart(analyses), use_container_width=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        media_counts = {"IMAGE": 0, "VIDEO": 0}
        for a in analyses:
            media_counts[a.media_type] = media_counts.get(a.media_type, 0) + 1
        df_media = pd.DataFrame({
            "Media Type": list(media_counts.keys()),
            "Analyses": list(media_counts.values())
        })
        fig_media = px.bar(
            df_media,
            x="Media Type",
            y="Analyses",
            title="Media Type Breakdown (Image vs Video)",
            color="Media Type",
            color_discrete_sequence=["#38BDF8", "#818CF8"]
        )
        fig_media.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9D1D9"),
            height=280
        )
        st.plotly_chart(fig_media, use_container_width=True)

    with row2_c2:
        # Analyst Review Decisions
        review_status_counts = {"PENDING_REVIEW": 0, "ACKNOWLEDGED": 0, "FALSE_POSITIVE": 0, "ESCALATED": 0}
        for a in analyses:
            rev = review_repo.get_review_by_analysis_id(a.id)
            status = rev.review_status if rev else "PENDING_REVIEW"
            review_status_counts[status] = review_status_counts.get(status, 0) + 1

        df_reviews = pd.DataFrame({
            "Review Status": list(review_status_counts.keys()),
            "Count": list(review_status_counts.values())
        })
        fig_reviews = px.bar(
            df_reviews,
            x="Review Status",
            y="Count",
            title="Human Analyst Review Decisions",
            color="Review Status",
            color_discrete_map={
                "PENDING_REVIEW": "#94A3B8",
                "ACKNOWLEDGED": "#22C55E",
                "FALSE_POSITIVE": "#F59E0B",
                "ESCALATED": "#EF4444"
            }
        )
        fig_reviews.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9D1D9"),
            height=280
        )
        st.plotly_chart(fig_reviews, use_container_width=True)
