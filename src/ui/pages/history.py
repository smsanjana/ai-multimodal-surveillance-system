"""Review & Audit View Module for Human Analyst Overrides and Audit Trail Persistence."""

import streamlit as st
from src.core.di_container import DIContainer
from src.infrastructure.database.repositories import AnalysisRepository, AnalystReviewRepository
from src.application.analyst_review_service import AnalystReviewService
from src.ui.components import render_section_header, render_threat_badge


def render_review_audit_page() -> None:
    """Renders the human analyst Review & Audit workspace."""
    render_section_header(
        "Review & Audit Workspace",
        "Searchable audit history, human review decision overrides, and audit log persistence"
    )

    container = DIContainer()
    analysis_repo = container.resolve(AnalysisRepository)
    review_repo = container.resolve(AnalystReviewRepository)
    review_service = container.resolve(AnalystReviewService)

    records = analysis_repo.get_all()

    if not records:
        st.info("No analysis records logged in the database yet. Run an analysis in the Workspace first.")
        return

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        media_filter = st.selectbox("Filter Media", ["ALL", "IMAGE", "VIDEO"], key="ra_media_filter")
    with c2:
        threat_filter = st.selectbox("Filter Threat", ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"], key="ra_threat_filter")
    with c3:
        search_q = st.text_input("Search ID / Scenario", placeholder="Enter keyword...", key="ra_search_q")

    if media_filter != "ALL":
        records = [r for r in records if r.media_type == media_filter]
    if threat_filter != "ALL":
        records = [r for r in records if r.threat_level == threat_filter]
    if search_q:
        records = [r for r in records if search_q.lower() in r.id.lower() or search_q.lower() in (r.scenario_name or "").lower()]

    st.write(f"Displaying **{len(records)}** recorded analyses")

    # Table of Records
    table_data = []
    for r in records:
        rev = review_repo.get_review_by_analysis_id(r.id)
        status = rev.review_status if rev else "PENDING_REVIEW"
        table_data.append({
            "Analysis ID": r.id[:8] + "...",
            "Timestamp": r.timestamp,
            "Platform": r.platform,
            "Media": r.media_type,
            "Scenario / Source": r.scenario_name or "Custom Media",
            "Threat Score": f"{r.threat_score:.1f}",
            "Threat Level": r.threat_level,
            "Review Status": status
        })

    st.dataframe(table_data, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Analyst Decision Inspector & State Override")

    record_labels = [f"{r.id[:8]} | {r.platform} | {r.scenario_name or 'Custom'} ({r.threat_level})" for r in records]
    selected_idx = st.selectbox("Select Record to Review", range(len(records)), format_func=lambda i: record_labels[i], key="ra_select_rec")
    selected_rec = records[selected_idx]

    rev_record = review_repo.get_review_by_analysis_id(selected_rec.id)
    current_status = rev_record.review_status if rev_record else "PENDING_REVIEW"
    assigned_analyst = rev_record.analyst_id if rev_record else "Unassigned"

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        st.metric("Threat Score", f"{selected_rec.threat_score:.1f}/100")
    with ic2:
        st.metric("AI Threat Level", selected_rec.threat_level)
    with ic3:
        st.metric("Current Review Status", current_status)
    with ic4:
        st.metric("Assigned Analyst", assigned_analyst)

    # Safe extraction of SOP recommendation (Fixes AttributeError)
    sop_text = getattr(selected_rec, "sop_recommendation", None) or getattr(selected_rec, "rationale", None)
    if not sop_text:
        sop_text = "Continue routine surveillance monitoring and maintain baseline sector security."

    st.markdown(f"**Operational SOP Guidance:** {sop_text}")

    # Decision Override Action Box
    st.markdown("##### Change Review Decision Status")
    with st.form(key=f"review_override_form_{selected_rec.id}"):
        new_status = st.selectbox(
            "Select New Status",
            options=["PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"],
            index=["PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"].index(current_status) if current_status in ["PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"] else 0
        )
        analyst_id_input = st.text_input("Analyst ID", value=assigned_analyst if assigned_analyst != "Unassigned" else "ANALYST-001")
        notes_input = st.text_area("Review Decision Notes / Justification", placeholder="Enter mandatory override notes...")

        submit_btn = st.form_submit_button("Update Review Decision", type="primary")

        if submit_btn:
            try:
                updated_rev = review_service.update_review_status(
                    analysis_id=selected_rec.id,
                    new_status=new_status,
                    analyst_id=analyst_id_input,
                    notes=notes_input
                )
                st.success(f"Successfully updated review status to **{new_status}**")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update review status: {e}")

    # Audit Transition History
    if rev_record:
        history_entries = review_repo.get_review_history(rev_record.id)
        if history_entries:
            st.markdown("---")
            st.markdown("##### Analyst Review Transition Audit History")
            hist_data = [
                {
                    "Timestamp": h.timestamp,
                    "From Status": h.from_status,
                    "To Status": h.to_status,
                    "Analyst ID": h.analyst_id,
                    "Notes": h.notes or "-"
                }
                for h in history_entries
            ]
            st.dataframe(hist_data, use_container_width=True)
