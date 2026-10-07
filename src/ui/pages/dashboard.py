"""Workspace — Main Demonstration Page Module.

Implements the central 4-stage demonstration workflow:
INPUT -> ANALYSIS -> ASSESSMENT -> REVIEW
"""

import logging
import streamlit as st
from typing import Optional
from src.core.di_container import DIContainer
from src.infrastructure.services.demo_manager import DemoManager
from src.application.image_surveillance_service import ImageSurveillanceService
from src.application.video_surveillance_service import VideoSurveillanceService
from src.domain.entities import ImageAnalysisRequest, VideoAnalysisRequest
from src.ui.components import (
    render_section_header, render_workflow_stages,
    render_threat_badge, render_alert_banner
)

logger = logging.getLogger("SurveillanceSystem")


def render_workspace_page() -> None:
    """Renders the central 4-stage Surveillance Workspace demonstration workflow."""
    render_section_header(
        "Surveillance Intelligence Workstation",
        "Multimodal Image & Video Threat Detection, Object Tracking, and Decision Support"
    )

    container = DIContainer()
    demo_manager: DemoManager = container.resolve(DemoManager)
    image_service: ImageSurveillanceService = container.resolve(ImageSurveillanceService)
    video_service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)

    # STAGE 1: INPUT SELECTION
    st.markdown("#### Stage 1: Select Input Media & Scenario")
    col_input1, col_input2 = st.columns([1, 1])

    with col_input1:
        source_mode = st.radio(
            "Select Input Mode",
            options=["Built-in Demo Scenario", "Upload Custom Image", "Upload Custom Video"],
            horizontal=True,
            key="ws_source_mode"
        )

        platform_choice = st.radio(
            "Select Platform",
            options=["Drone", "CCTV"],
            horizontal=True,
            key="ws_platform"
        )

    selected_scenario_name: Optional[str] = None
    uploaded_file = None
    media_type = "IMAGE"
    upload_zone_flag = False
    upload_unauth_signal = False

    with col_input2:
        if source_mode == "Built-in Demo Scenario":
            demo_type = st.radio("Select Demo Type", ["Image Scenario", "Video Scenario"], horizontal=True, key="ws_demo_type")
            media_type = "IMAGE" if demo_type == "Image Scenario" else "VIDEO"

            if media_type == "IMAGE":
                scenarios = demo_manager.list_scenarios(platform=platform_choice)
            else:
                scenarios = demo_manager.list_video_scenarios(platform=platform_choice)

            scen_titles = [s["title"] for s in scenarios] if scenarios else ["Drone Military Reconnaissance Feed"]
            selected_scenario_name = st.selectbox("Select Built-in Scenario", options=scen_titles, key="ws_scenario_select")

            scen_info = demo_manager.get_scenario(selected_scenario_name) if selected_scenario_name else None
            if scen_info:
                zone_str = "YES (+65)" if scen_info.get("zone_violation_flag", False) else "NO"
                unauth_str = "YES (+20)" if scen_info.get("unauthorized_access_signal", False) else "NO"
                exp_lvl = scen_info.get("expected_level", "LOW")
                st.markdown(
                    f"**Asset Label:** `[SYNTHETIC DEMO ASSET]` | Platform: **{scen_info.get('platform')}** | Expected: **{exp_lvl}**\n\n"
                    f"*{scen_info.get('description')}*\n\n"
                    f"ℹ️ **Configured Security Evidence**: Zone Breach: `{zone_str}` | Access Breach: `{unauth_str}`"
                )

        elif source_mode == "Upload Custom Image":
            media_type = "IMAGE"
            uploaded_file = st.file_uploader("Upload Image File", type=["jpg", "jpeg", "png"], key="ws_img_uploader")
            st.markdown("**Contextual Security Evidence Signals (Optional):**")
            c_flag1, c_flag2 = st.columns(2)
            with c_flag1:
                upload_zone_flag = st.checkbox("Explicit Restricted Zone Signal (+65 pts)", key="ws_img_zone_flag")
            with c_flag2:
                upload_unauth_signal = st.checkbox("Explicit Unauthorized Access Signal (+20 pts)", key="ws_img_unauth_flag")
            if uploaded_file:
                st.caption(f"Loaded File: **{uploaded_file.name}** ({uploaded_file.size} bytes)")

        else:  # Upload Custom Video
            media_type = "VIDEO"
            uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov"], key="ws_vid_uploader")
            st.markdown("**Contextual Security Evidence Signals (Optional):**")
            c_flag1, c_flag2 = st.columns(2)
            with c_flag1:
                upload_zone_flag = st.checkbox("Explicit Restricted Zone Signal (+65 pts)", key="ws_vid_zone_flag")
            with c_flag2:
                upload_unauth_signal = st.checkbox("Explicit Unauthorized Access Signal (+20 pts)", key="ws_vid_unauth_flag")
            if uploaded_file:
                st.caption(f"Loaded File: **{uploaded_file.name}** ({uploaded_file.size} bytes)")

    # --- Phase 2: Interactive Restricted Zone Polygon Drawer ---
    st.markdown("---")
    with st.expander("✏️ Interactive Restricted Zone Polygon Drawer (Optional Custom Bounds)", expanded=False):
        st.caption("Draw 3 or more vertices on the surveillance backdrop below to define a custom spatial restricted zone.")
        
        # Extract background preview frame for canvas
        bg_pil = None
        orig_w, orig_h = 1280, 720

        try:
            import cv2
            from PIL import Image
            import io

            if media_type == "IMAGE":
                if source_mode == "Built-in Demo Scenario" and selected_scenario_name:
                    img_bytes = demo_manager.load_demo_image_bytes(selected_scenario_name)
                    bg_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                elif uploaded_file:
                    bg_pil = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
            else:  # VIDEO
                vpath = None
                if source_mode == "Built-in Demo Scenario" and selected_scenario_name:
                    scen = demo_manager.get_video_scenario(selected_scenario_name) or demo_manager.get_scenario(selected_scenario_name)
                    if scen and "file_path" in scen:
                        vpath = scen["file_path"]
                elif uploaded_file:
                    import tempfile
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tf.write(uploaded_file.getvalue())
                    tf.close()
                    vpath = tf.name

                if vpath and os.path.exists(vpath):
                    cap = cv2.VideoCapture(vpath)
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        bg_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except Exception as ex:
            logger.warning("Could not extract canvas backdrop preview frame: %s", ex)

        # Fallback background image if extraction fails
        if bg_pil is None:
            from PIL import Image
            bg_pil = Image.new("RGB", (1280, 720), color=(30, 35, 45))

        orig_w, orig_h = bg_pil.size
        canvas_w = 640
        canvas_h = max(200, int(round(canvas_w * (orig_h / float(orig_w)))))
        resized_bg = bg_pil.resize((canvas_w, canvas_h))

        try:
            from streamlit_drawable_canvas import st_canvas
            from src.ui.components import normalize_canvas_polygon, create_custom_restricted_zone
            from src.domain.entities import RestrictedZone

            st.caption(f"Canvas Scale: Rendered **{canvas_w}x{canvas_h}px** (Source Aspect: **{orig_w}x{orig_h}px**)")
            
            canvas_result = st_canvas(
                fill_color="rgba(239, 68, 68, 0.25)",
                stroke_width=2,
                stroke_color="#EF4444",
                background_image=resized_bg,
                update_streamlit=True,
                height=canvas_h,
                width=canvas_w,
                drawing_mode="polygon",
                key="ws_zone_canvas",
            )

            raw_points = []
            if canvas_result and canvas_result.json_data and "objects" in canvas_result.json_data:
                for obj in canvas_result.json_data["objects"]:
                    if obj.get("type") in ["path", "polygon"]:
                        path_data = obj.get("path", [])
                        for p in path_data:
                            if isinstance(p, list) and len(p) >= 3 and p[0] in ["M", "L"]:
                                raw_points.append((float(p[1]), float(p[2])))
                        if not raw_points and "points" in obj:
                            for pt in obj["points"]:
                                raw_points.append((float(pt["x"]), float(pt["y"])))

            col_z1, col_z2 = st.columns([3, 1])
            with col_z2:
                if st.button("🗑️ Clear Custom Zone", key="ws_clear_zone_btn"):
                    st.session_state["custom_zone_points"] = None
                    st.session_state["custom_zone_active"] = False
                    st.rerun()

            with col_z1:
                if raw_points:
                    norm_pts = normalize_canvas_polygon(raw_points, canvas_w, canvas_h)
                    if len(norm_pts) >= 3:
                        st.session_state["custom_zone_points"] = norm_pts
                        st.session_state["custom_zone_active"] = True
                        st.success(f"✅ Custom Zone Defined: {len(norm_pts)} vertices normalized to [0.0, 1.0]")
                    else:
                        st.warning(f"⚠️ Polygon requires at least 3 vertices (detected {len(norm_pts)} points). Using platform fallback zone.")
                        st.session_state["custom_zone_points"] = None
                        st.session_state["custom_zone_active"] = False
                elif st.session_state.get("custom_zone_points"):
                    pts = st.session_state["custom_zone_points"]
                    st.info(f"ℹ️ Active Custom Zone: {len(pts)} normalized vertices stored in session.")
                else:
                    st.caption("No custom polygon drawn. Standard platform fallback zone will be evaluated.")

        except ImportError:
            st.info("ℹ️ Interactive drawing canvas package `streamlit-drawable-canvas` is not active. Using standard platform zone fallback.")

    # Clear stale results if selection changed
    current_selection_key = f"{source_mode}_{platform_choice}_{selected_scenario_name}_{getattr(uploaded_file, 'name', 'none')}"
    last_selection_key = st.session_state.get("last_workspace_selection_key")
    if last_selection_key != current_selection_key:
        st.session_state["last_workspace_selection_key"] = current_selection_key
        st.session_state["active_analysis_response"] = None

    analysis_resp = st.session_state.get("active_analysis_response")
    current_stage = "REVIEW" if analysis_resp else "INPUT"
    render_workflow_stages(active_stage=current_stage)

    st.markdown("---")

    # STAGE 2: ANALYSIS EXECUTION
    st.markdown("#### Stage 2: Run Multimodal Analysis")
    run_disabled = st.session_state.get("is_analyzing", False)

    if st.button("🚀 Run Analysis", type="primary", use_container_width=True, disabled=run_disabled, key="ws_run_btn"):
        st.session_state["is_analyzing"] = True
        st.session_state["active_analysis_response"] = None
        st.session_state["analysis_error"] = None

        # Build custom RestrictedZone if present in session state
        custom_zones = None
        if st.session_state.get("custom_zone_points"):
            from src.ui.components import create_custom_restricted_zone
            user_zone = create_custom_restricted_zone(
                st.session_state["custom_zone_points"],
                platform=platform_choice.upper()
            )
            if user_zone:
                custom_zones = [user_zone]

        with st.spinner(f"Executing computer vision detection & threat evaluation on {media_type}..."):
            try:
                if media_type == "IMAGE":
                    req = ImageAnalysisRequest(
                        source_type="DEMO" if source_mode == "Built-in Demo Scenario" else "UPLOAD",
                        platform=platform_choice.upper(),
                        scenario_name=selected_scenario_name,
                        image_bytes=uploaded_file.getvalue() if uploaded_file else None,
                        zone_violation_flag=upload_zone_flag,
                        unauthorized_access_signal=upload_unauth_signal
                    )
                    resp = image_service.process_image(req)
                    st.session_state["active_analysis_response"] = resp
                    st.session_state["selected_analysis_id"] = resp.analysis_id
                else:
                    # Video analysis
                    video_bytes = None
                    temp_path = None
                    if uploaded_file:
                        import tempfile
                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                        tfile.write(uploaded_file.getvalue())
                        tfile.close()
                        temp_path = tfile.name

                    req = VideoAnalysisRequest(
                        source_type="DEMO" if source_mode == "Built-in Demo Scenario" else "UPLOAD",
                        platform=platform_choice.upper(),
                        scenario_name=selected_scenario_name,
                        video_path=temp_path,
                        zone_violation_flag=upload_zone_flag,
                        unauthorized_access_signal=upload_unauth_signal,
                        zones=custom_zones
                    )
                    resp = video_service.process_video(req)
                    st.session_state["active_analysis_response"] = resp
                    st.session_state["selected_analysis_id"] = resp.analysis_id

                # Diagnostic logging for development verification
                det_cnt = len(resp.detections) if hasattr(resp, "detections") else (resp.total_detections if hasattr(resp, "total_detections") else 0)
                zv = getattr(resp.threat_assessment, "zone_violation_flag", False)
                ua = getattr(resp.threat_assessment, "unauthorized_access_signal", False)
                score = resp.threat_assessment.threat_score
                level = resp.threat_assessment.threat_level
                print(f"ANALYSIS RUN: analysis_id={resp.analysis_id[:8]}... media_type={media_type} detections={det_cnt} zone_violation={zv} unauthorized_access={ua} score={score} level={level}")
                logger.info(
                    "ANALYSIS RUN: analysis_id=%s media_type=%s detections=%d score=%.1f level=%s",
                    resp.analysis_id, media_type, det_cnt, score, level
                )

                st.success("Analysis executed successfully!")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.session_state["analysis_error"] = str(e)
            finally:
                st.session_state["is_analyzing"] = False

    # STAGE 3 & 4: RESULTS ASSESSMENT & NAVIGATION SHORTCUTS
    resp = st.session_state.get("active_analysis_response")
    if resp:
        st.markdown("---")
        st.markdown("#### Stage 3: Assessment Summary")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Analysis ID", resp.analysis_id[:8] + "...")
        with c2:
            st.metric("Media Type", getattr(resp, "media_type", media_type))
        with c3:
            det_count = len(resp.detections) if hasattr(resp, "detections") else (getattr(resp, "total_detections", 0))
            st.metric("Detections", str(det_count))
        with c4:
            if hasattr(resp, "tracks"):
                st.metric("Track Count", str(len(resp.tracks)))
            else:
                st.metric("Track Count", "N/A (Image)")
        with c5:
            score = resp.threat_assessment.threat_score if hasattr(resp, "threat_assessment") else 0.0
            level = resp.threat_assessment.threat_level if hasattr(resp, "threat_assessment") else "LOW"
            st.metric("Threat Assessment", f"{score:.1f}/100 ({level})")

        st.markdown("---")
        st.markdown("#### Stage 4: Workstation View Shortcuts")
        st.caption("Select a detail view below to inspect specific computer vision and threat evidence outputs:")

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            if st.button("🎯 Open Detection View", use_container_width=True):
                st.session_state["nav_selection"] = "2. Detection"
                st.rerun()
        with s2:
            if st.button("🛣️ Open Tracking View", use_container_width=True):
                st.session_state["nav_selection"] = "3. Tracking"
                st.rerun()
        with s3:
            if st.button("🛡️ Open Threat Assessment", use_container_width=True):
                st.session_state["nav_selection"] = "4. Threat Assessment"
                st.rerun()
        with s4:
            if st.button("💡 Open Explainability", use_container_width=True):
                st.session_state["nav_selection"] = "5. Explainability"
                st.rerun()
