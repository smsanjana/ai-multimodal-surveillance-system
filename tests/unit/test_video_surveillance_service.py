"""Unit tests for VideoSurveillanceService."""

import pytest
import os
import json
import tempfile
import cv2
import numpy as np
from unittest.mock import MagicMock

from src.domain.entities import (
    VideoAnalysisRequest,
    VideoAnalysisResult,
    VideoMetadata,
    DetectionResult,
    BoundingBox,
    ThreatAssessmentResult,
    TrackRecord,
    TrajectoryPoint,
)
from src.application.video_surveillance_service import VideoSurveillanceService
from src.core.exceptions import ValidationError


@pytest.fixture
def mock_dependencies():
    video_proc = MagicMock()
    detector = MagicMock()
    tracker = MagicMock()
    threat_service = MagicMock()
    explainability = MagicMock()
    analysis_repo = MagicMock()
    demo_manager = MagicMock()

    # Default metadata mock
    video_proc.validate_video.return_value = VideoMetadata(
        file_path="data/demo/drone/videos/real_drone_perimeter_surveillance.mp4",
        duration_seconds=5.0,
        fps=25.0,
        total_frames=125,
        sampled_frames=25,
        width=1280,
        height=720
    )

    # Frame generator mock: 2 sampled frames
    frame1 = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)
    video_proc.extract_sampled_frames.return_value = iter([
        (0, 0.0, frame1),
        (5, 0.2, frame2),
    ])

    det1 = DetectionResult(class_id=5, class_name="Tank", confidence=0.9, bbox=BoundingBox(100, 100, 200, 200))
    detector.detect.return_value = [det1]

    track1 = TrackRecord(
        track_id=1,
        class_id=5,
        class_name="Tank",
        first_frame=0,
        last_frame=5,
        first_timestamp=0.0,
        last_timestamp=0.2,
        detection_count=2,
        avg_confidence=0.9,
        movement_state="MOVING",
        pixel_displacement=30.0,
        trajectory_direction="East",
        trajectory_points=[TrajectoryPoint(150, 150, 0, 0.0), TrajectoryPoint(180, 150, 5, 0.2)]
    )

    tracker.update.return_value = [track1]
    tracker.finish_tracks.return_value = [track1]

    threat_service.evaluate_threat.return_value = ThreatAssessmentResult(
        threat_score=5.0,
        threat_level="LOW",
        factors=[],
        xai_reason="Routine military observation.",
        recommended_sop="Continue monitoring."
    )

    explainability.explain.return_value = {
        "xai_reason": "Routine military observation.",
        "recommended_sop": "Continue monitoring."
    }

    # Analysis repo mock save return
    saved_rec = MagicMock()
    saved_rec.timestamp = "2026-09-13T12:00:00Z"
    analysis_repo.save_video_analysis_with_tracks.return_value = saved_rec

    return {
        "video_proc": video_proc,
        "detector": detector,
        "tracker": tracker,
        "threat_service": threat_service,
        "explainability": explainability,
        "analysis_repo": analysis_repo,
        "demo_manager": demo_manager,
    }


def test_video_surveillance_service_successful_flow(mock_dependencies):
    service = VideoSurveillanceService(
        video_processing_service=mock_dependencies["video_proc"],
        detection_service=mock_dependencies["detector"],
        tracking_service=mock_dependencies["tracker"],
        threat_scoring_service=mock_dependencies["threat_service"],
        explainability_service=mock_dependencies["explainability"],
        analysis_repository=mock_dependencies["analysis_repo"],
        demo_manager=mock_dependencies["demo_manager"],
    )

    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Military Reconnaissance Feed",
        target_sample_fps=5.0,
        zone_violation_flag=False
    )

    result = service.process_video_analysis(req)

    assert isinstance(result, VideoAnalysisResult)
    assert result.platform == "DRONE"
    assert len(result.tracks) == 1
    assert result.tracks[0].class_name == "Tank"
    assert result.threat_assessment.threat_level == "LOW"
    assert result.persisted is True
    assert mock_dependencies["analysis_repo"].save_video_analysis_with_tracks.called


def test_video_surveillance_service_exceeds_duration_rejection(mock_dependencies):
    mock_dependencies["video_proc"].validate_video.side_effect = ValidationError("Video duration exceeds maximum allowed limit of 120 seconds.")

    mock_dependencies["video_proc"].save_temp_upload.return_value = "data/temp/long_video.mp4"

    service = VideoSurveillanceService(
        video_processing_service=mock_dependencies["video_proc"],
        detection_service=mock_dependencies["detector"],
        tracking_service=mock_dependencies["tracker"],
        threat_scoring_service=mock_dependencies["threat_service"],
        explainability_service=mock_dependencies["explainability"],
        analysis_repository=mock_dependencies["analysis_repo"],
        demo_manager=mock_dependencies["demo_manager"],
    )

    req = VideoAnalysisRequest(
        source_type="UPLOAD",
        video_bytes=b"dummy_long_video_bytes",
        scenario_name="long_video.mp4"
    )

    with pytest.raises(ValidationError) as excinfo:
        service.process_video_analysis(req)
    assert "exceeds maximum allowed limit" in str(excinfo.value)
    assert not mock_dependencies["analysis_repo"].save_video_analysis_with_tracks.called


def test_video_surveillance_service_zero_detections_video(mock_dependencies):
    # Detector returns 0 detections for all frames
    mock_dependencies["detector"].detect.return_value = []
    mock_dependencies["tracker"].finish_tracks.return_value = []

    service = VideoSurveillanceService(
        video_processing_service=mock_dependencies["video_proc"],
        detection_service=mock_dependencies["detector"],
        tracking_service=mock_dependencies["tracker"],
        threat_scoring_service=mock_dependencies["threat_service"],
        explainability_service=mock_dependencies["explainability"],
        analysis_repository=mock_dependencies["analysis_repo"],
        demo_manager=mock_dependencies["demo_manager"],
    )

    req = VideoAnalysisRequest(source_type="DEMO", platform="CCTV")
    result = service.process_video_analysis(req)

    assert len(result.tracks) == 0
    assert result.total_detections == 0
    assert result.threat_assessment.threat_score == 0.0
    assert result.threat_assessment.threat_level == "LOW"
