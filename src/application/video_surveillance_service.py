"""Video Surveillance Application Service Module."""

import time
import os
import uuid
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
import cv2

from src.domain.interfaces import (
    IVideoSurveillanceService,
    AbstractVideoProcessingService,
    AbstractDetectionService,
    AbstractTrackingService,
    AbstractThreatScoringService,
    AbstractExplainabilityService,
)
from src.domain.entities import (
    VideoAnalysisRequest,
    VideoAnalysisResult,
    AnalysisRecord,
    DetectionRecord,
    DetectionResult,
    TrackRecord,
    BoundingBox,
    ThreatAssessmentResult,
)
from src.infrastructure.database.repositories import AnalysisRepository
from src.infrastructure.services.demo_manager import DemoManager
from src.core.exceptions import ValidationError, AnalysisProcessingError

logger = logging.getLogger("SurveillanceSystem")


class VideoSurveillanceService(IVideoSurveillanceService):
    """
    Application Service orchestrating end-to-end video surveillance workflow:
    Video Ingestion → Metadata Extraction → Frame Sampling Generator → KIIT-MiTA Detection
    → IoU Multi-Object Tracking & Trajectory Analysis → Aggregated Threat Assessment
    → XAI Rationale → SQLite Persistence → VideoAnalysisResult formatting.
    """

    def __init__(
        self,
        video_processing_service: AbstractVideoProcessingService,
        detection_service: AbstractDetectionService,
        tracking_service: AbstractTrackingService,
        threat_scoring_service: AbstractThreatScoringService,
        explainability_service: AbstractExplainabilityService,
        analysis_repository: AnalysisRepository,
        demo_manager: DemoManager,
    ):
        self.video_processing = video_processing_service
        self.detection_service = detection_service
        self.tracking_service = tracking_service
        self.threat_scoring_service = threat_scoring_service
        self.explainability_service = explainability_service
        self.analysis_repo = analysis_repository
        self.demo_manager = demo_manager

    def _draw_track_annotations(
        self, image_rgb: np.ndarray, detections: List[DetectionResult], tracks_in_frame: Dict[str, int]
    ) -> np.ndarray:
        """
        Draws bounding box annotations overlaid with persistent track ID tags (e.g. 'Track #1: Tank 92%').
        """
        if image_rgb is None or image_rgb.size == 0:
            return image_rgb

        annotated = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        color_palette = [
            (0, 255, 0),    # Green
            (255, 165, 0),  # Orange
            (0, 191, 255),  # Deep Sky Blue
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
        ]

        for det in detections:
            bbox = det.bbox
            x1, y1 = int(bbox.x_min), int(bbox.y_min)
            x2, y2 = int(bbox.x_max), int(bbox.y_max)

            track_id = tracks_in_frame.get(det.detection_id, None)
            track_prefix = f"Track #{track_id}: " if track_id is not None else ""
            label = f"{track_prefix}{det.class_name} {det.confidence * 100:.1f}%"

            color_idx = abs(hash(det.class_name)) % len(color_palette)
            color = color_palette[color_idx]

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)

            cv2.rectangle(annotated, (x1, max(0, y1 - h - 6)), (x1 + w + 6, max(h + 6, y1)), color, -1)
            cv2.putText(annotated, label, (x1 + 3, max(h + 3, y1 - 3)), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

        return cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

    def process_video(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        """Alias for process_video_analysis to support UI and application callers."""
        return self.process_video_analysis(request)

    def process_video_analysis(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        """
        Executes end-to-end video surveillance processing pipeline.
        """
        start_time = time.time()
        logger.info("Starting video surveillance analysis for request: platform=%s, source=%s", request.platform, request.source_type)

        # 1. Resolve Video File Path
        if request.source_type.upper() == "DEMO":
            scenario_name = request.scenario_name or "Drone Military Reconnaissance Feed"
            scenario = self.demo_manager.get_video_scenario(scenario_name)
            if scenario and "file_path" in scenario:
                video_path = scenario["file_path"]
            else:
                # Default video scenario fallback
                scenarios = self.demo_manager.list_video_scenarios(request.platform)
                video_path = scenarios[0]["file_path"] if scenarios else "data/demo/drone/videos/real_drone_perimeter_surveillance.mp4"
            request.scenario_name = scenario_name
        elif request.source_type.upper() == "UPLOAD":
            if request.video_path and os.path.exists(request.video_path):
                video_path = request.video_path
            elif request.video_bytes:
                filename = request.scenario_name or "uploaded_video.mp4"
                video_path = self.video_processing.save_temp_upload(request.video_bytes, filename)
            else:
                raise ValidationError("No video file path or uploaded binary payload provided.")
            request.scenario_name = request.scenario_name or os.path.basename(video_path)
        else:
            raise ValidationError(f"Unsupported source type '{request.source_type}'. Only 'DEMO' and 'UPLOAD' are supported.")

        # 2. Validate Video (enforces >120s duration rejection immediately)
        metadata = self.video_processing.validate_video(video_path)

        # 3. Reset Tracker State
        self.tracking_service.reset()

        representative_frame_bytes_list: List[bytes] = []
        frame_samples_recorded = 0
        target_sample_frames_interval = max(1, metadata.sampled_frames // 4)

        all_sampled_detections: List[DetectionResult] = []

        # 4. Stream Frame Sampling Generator & Perform Detection + Tracking
        frame_generator = self.video_processing.extract_sampled_frames(video_path, target_fps=request.target_sample_fps)

        for frame_idx, timestamp_sec, frame_bgr in frame_generator:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # Detect objects on current sampled frame (confidence 0.25)
            # Note: Zero detections on an individual frame is allowed; loop continues.
            frame_detections = self.detection_service.detect(frame_rgb, confidence_threshold=0.25)
            all_sampled_detections.extend(frame_detections)

            # Update tracker
            active_tracks = self.tracking_service.update(frame_idx, timestamp_sec, frame_detections)

            # Build map of detection_id -> track_id for visual annotation
            tracks_in_frame: Dict[str, int] = {}
            for tr in active_tracks:
                for det in frame_detections:
                    cx, cy = (det.bbox.x_min + det.bbox.x_max) / 2.0, (det.bbox.y_min + det.bbox.y_max) / 2.0
                    if tr.trajectory_points:
                        last_pt = tr.trajectory_points[-1]
                        if abs(last_pt.x - cx) < 2.0 and abs(last_pt.y - cy) < 2.0:
                            tracks_in_frame[det.detection_id] = tr.track_id

            # Capture representative annotated frames (up to 4 across video)
            if frame_samples_recorded < 4 and (frame_samples_recorded == 0 or frame_idx % target_sample_frames_interval == 0):
                annotated_rgb = self._draw_track_annotations(frame_rgb, frame_detections, tracks_in_frame)
                _, buffer = cv2.imencode(".png", cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))
                representative_frame_bytes_list.append(buffer.tobytes())
                frame_samples_recorded += 1

        # 5. Flush Completed Track Records
        tracks: List[TrackRecord] = self.tracking_service.finish_tracks()

        # 6. Aggregate Detections & Per-Class Counts
        total_detections = sum(t.detection_count for t in tracks)
        class_counts: Dict[str, int] = {}
        for t in tracks:
            class_counts[t.class_name] = class_counts.get(t.class_name, 0) + t.detection_count

        # 7. Evaluate Threat Level (Feature 003 Neutral Engine)
        # Convert tracks to representative DetectionResult objects for threat evaluator
        rep_detections_for_threat: List[DetectionResult] = []
        for t in tracks:
            # Create synthetic bounding box from track history
            rep_bbox = BoundingBox(0.1, 0.1, 0.5, 0.5)
            if t.trajectory_points:
                pt = t.trajectory_points[0]
                rep_bbox = BoundingBox(
                    x_min=max(0.0, pt.x - 20),
                    y_min=max(0.0, pt.y - 20),
                    x_max=min(float(metadata.width), pt.x + 20),
                    y_max=min(float(metadata.height), pt.y + 20)
                )
            rep_detections_for_threat.append(DetectionResult(
                detection_id=str(uuid.uuid4()),
                class_id=t.class_id,
                class_name=t.class_name,
                confidence=t.avg_confidence,
                bbox=rep_bbox
            ))

        zone_flag = request.zone_violation_flag
        unauth_signal = getattr(request, "unauthorized_access_signal", False)

        if request.source_type.upper() == "DEMO" and request.scenario_name:
            scen_info = self.demo_manager.get_scenario(request.scenario_name)
            if scen_info:
                if not zone_flag:
                    zone_flag = scen_info.get("zone_violation_flag", False)
                if not unauth_signal:
                    unauth_signal = scen_info.get("unauthorized_access_signal", False)

        threat_eval_metadata = {
            "zone_violation_flag": zone_flag,
            "unauthorized_access_signal": unauth_signal,
            "media_type": "VIDEO",
            "platform": request.platform,
            "scenario_name": request.scenario_name or ""
        }

        # If zero objects detected across ALL frames, threat score is baseline 0.0/100
        if not tracks:
            threat_assessment = ThreatAssessmentResult(
                threat_score=0.0,
                threat_level="LOW",
                factors=[],
                xai_reason="No target objects detected across sampled video frames.",
                recommended_sop="Continue routine video surveillance monitoring."
            )
        else:
            threat_assessment = self.threat_scoring_service.evaluate_threat(rep_detections_for_threat, threat_eval_metadata)
            xai_data = self.explainability_service.explain(
                threat_assessment.threat_score, threat_assessment.threat_level, rep_detections_for_threat, threat_eval_metadata
            )
            threat_assessment.xai_reason = xai_data.get("xai_reason", threat_assessment.xai_reason)
            threat_assessment.recommended_sop = xai_data.get("recommended_sop", threat_assessment.recommended_sop)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        analysis_id = str(uuid.uuid4())

        # 8. Create Analysis Record & Detection Records for SQLite
        avg_conf = round(sum(t.avg_confidence for t in tracks) / max(1, len(tracks)), 4) if tracks else 0.0
        analysis_record = AnalysisRecord(
            id=analysis_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            source_type=request.source_type,
            platform=request.platform,
            media_type="VIDEO",
            scenario_name=request.scenario_name,
            threat_score=threat_assessment.threat_score,
            threat_level=threat_assessment.threat_level,
            confidence_avg=avg_conf,
            processing_time_ms=processing_time_ms,
            status="COMPLETED",
            artifact_path=None
        )

        detection_records: List[DetectionRecord] = []
        for t in tracks:
            detection_records.append(DetectionRecord(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                class_name=t.class_name,
                confidence=t.avg_confidence,
                bbox_json=f'{{"track_id": {t.track_id}, "movement_state": "{t.movement_state}", "displacement_px": {t.pixel_displacement}}}',
                frame_index=t.first_frame
            ))

        # 9. Persist Header in analyses, Detections in detections, & 13-field TrackRecord JSON in data/artifacts/
        saved_record = self.analysis_repo.save_video_analysis_with_tracks(
            analysis_record, detection_records, tracks, threat_assessment.__dict__
        )

        logger.info("Video surveillance processing completed cleanly in %s ms. Tracks: %s, Threat Level: %s", processing_time_ms, len(tracks), threat_assessment.threat_level)

        return VideoAnalysisResult(
            analysis_id=analysis_id,
            timestamp=saved_record.timestamp,
            source_type=request.source_type,
            platform=request.platform,
            scenario_name=request.scenario_name,
            video_metadata=metadata,
            tracks=tracks,
            total_detections=total_detections,
            class_counts=class_counts,
            threat_assessment=threat_assessment,
            representative_frame_bytes=representative_frame_bytes_list,
            annotated_video_path=video_path,
            processing_time_ms=processing_time_ms,
            persisted=True
        )
