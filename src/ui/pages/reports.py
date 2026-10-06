"""Report Generator View Module."""

import streamlit as st
from typing import Optional, List, Dict, Any
from src.core.di_container import DIContainer
from src.domain.entities import AnalysisRecord, DetectionRecord
from src.infrastructure.database.repositories import AnalysisRepository, ReportRepository
from src.ui.components import render_section_header, render_alert_banner


def compile_incident_report(
    record: AnalysisRecord,
    detections: Optional[List[DetectionRecord]] = None,
    tracks: Optional[List[Any]] = None,
    report_type: str = "INCIDENT_SUMMARY",
    include_sop: bool = True
) -> str:
    """Compiles a structured Markdown surveillance report from actual inspection data."""
    if not record:
        return "# SURVEILLANCE REPORT\n\nNo analysis record selected."

    lines = [
        "# SURVEILLANCE INCIDENT & TELEMETRY REPORT",
        "",
        f"**Report Type:** {report_type}",
        f"**Generated:** {record.timestamp}",
        "",
        "---",
        "",
        "## 1. Inspection Metadata",
        f"- **Analysis ID:** `{record.id}`",
        f"- **Timestamp:** {record.timestamp}",
        f"- **Source Type:** {record.source_type}",
        f"- **Platform:** {record.platform}",
        f"- **Media Type:** {record.media_type}",
        f"- **Scenario / Source:** {record.scenario_name or 'Custom Upload / Feed'}",
        f"- **Status:** {record.status}",
        f"- **Processing Latency:** {record.processing_time_ms:.1f} ms",
        "",
        "---",
        "",
        "## 2. Threat & Risk Assessment",
        f"- **Threat Score:** {record.threat_score:.1f} / 100",
        f"- **Threat Level:** {record.threat_level}",
        f"- **Average Model Confidence:** {record.confidence_avg:.1%}",
    ]

    sop = getattr(record, "sop_recommendation", None) or getattr(record, "rationale", None)
    if include_sop:
        lines.extend([
            "",
            "### Recommended Standard Operating Procedure (SOP)",
            f"{sop if sop else 'Continue routine surveillance monitoring and maintain baseline sector security.'}"
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 3. Computer Vision Observations (Detections Summary)"
    ])

    if detections:
        class_counts: Dict[str, int] = {}
        for d in detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1
        lines.append(f"- **Total Observed Detections:** {len(detections)}")
        lines.append("- **Class Breakdown:** " + ", ".join([f"{count} {cls}" for cls, count in class_counts.items()]))
        lines.append("")
        lines.append("| # | Class Name | Confidence | Frame Index |")
        lines.append("|---|---|---|---|")
        for idx, d in enumerate(detections, 1):
            frame_str = str(d.frame_index) if d.frame_index is not None else "N/A"
            lines.append(f"| {idx} | {d.class_name} | {d.confidence:.1%} | {frame_str} |")
    else:
        lines.append("No individual detection records logged for this analysis.")

    if record.media_type == "VIDEO":
        lines.extend([
            "",
            "---",
            "",
            "## 4. Multi-Object Tracking & Trajectory Telemetry"
        ])
        if tracks:
            lines.append(f"- **Total Tracked Targets:** {len(tracks)}")
            lines.append("")
            lines.append("| Track ID | Class | First Frame | Last Frame | Detections | Avg Conf | Movement | Displacement | Direction |")
            lines.append("|---|---|---|---|---|---|---|---|---|")
            for t in tracks:
                if isinstance(t, dict):
                    lines.append(f"| Track #{t.get('track_id')} | {t.get('class_name')} | {t.get('first_frame')} | {t.get('last_frame')} | {t.get('detection_count')} | {t.get('avg_confidence', 0.0):.1%} | {t.get('movement_state')} | {t.get('pixel_displacement', 0.0):.1f} px | {t.get('trajectory_direction')} |")
                else:
                    lines.append(f"| Track #{t.track_id} | {t.class_name} | {t.first_frame} | {t.last_frame} | {t.detection_count} | {t.avg_confidence:.1%} | {t.movement_state} | {t.pixel_displacement:.1f} px | {t.trajectory_direction} |")
        else:
            lines.append("No active target tracks recorded for this video analysis.")

    return "\n".join(lines)


def render_reports_page() -> None:
    """Renders the report management and Markdown exporter UI shell."""
    render_section_header("Surveillance Incident Reports", "Generate, preview, and export official surveillance reports")

    container = DIContainer()
    analysis_repo = container.resolve(AnalysisRepository)
    report_repo = container.resolve(ReportRepository)

    analyses = analysis_repo.get_all()

    if not analyses:
        st.info("No analysis records available to generate reports.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Report Parameters")
        selected_analysis_id = st.selectbox(
            "Select Inspection Record",
            options=[a.id for a in analyses],
            format_func=lambda x: next((f"{a.timestamp[:10]} - {a.platform} - {a.scenario_name or 'Custom'} ({a.threat_level})" for a in analyses if a.id == x), x)
        )
        report_type = st.selectbox("Report Template Type", ["INCIDENT_SUMMARY", "DAILY_AUDIT", "FULL_EXECUTIVE_EXPORT"])
        include_images = st.checkbox("Include Annotated Bounding Box Image Snapshots", value=True)
        include_sop = st.checkbox("Include Recommended SOP Action Plan", value=True)

        if st.button("📄 Generate Report", type="primary", use_container_width=True):
            st.session_state["report_generated"] = True
            st.session_state["active_report_analysis_id"] = selected_analysis_id
            st.success("Report compiled successfully!")

    with c2:
        st.subheader("2. Report Preview Area")
        active_id = st.session_state.get("active_report_analysis_id", selected_analysis_id)
        if st.session_state.get("report_generated", False) and active_id:
            selected_rec = analysis_repo.get_by_id(active_id)
            if selected_rec:
                detections = analysis_repo.get_detections_by_analysis_id(selected_rec.id)
                tracks = []
                if selected_rec.media_type == "VIDEO" and selected_rec.artifact_path:
                    tracks = analysis_repo.get_tracks_by_artifact_path(selected_rec.artifact_path)

                report_md = compile_incident_report(
                    record=selected_rec,
                    detections=detections,
                    tracks=tracks,
                    report_type=report_type,
                    include_sop=include_sop
                )

                st.markdown(report_md)
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    "⬇️ Download Markdown Report",
                    data=report_md,
                    file_name=f"surveillance_report_{selected_rec.id[:8]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        else:
            st.info("Select parameters and click 'Generate Report' to view preview.")

    st.markdown("---")
    st.subheader("Generated Reports Archive")
    reports = report_repo.get_all()
    if reports:
        rep_table = [
            {"Report ID": r.id[:8] + "...", "Analysis ID": r.analysis_id[:8] + "...", "Type": r.report_type, "Generated At": r.generated_at, "File Path": r.file_path}
            for r in reports
        ]
        st.dataframe(rep_table, use_container_width=True)
