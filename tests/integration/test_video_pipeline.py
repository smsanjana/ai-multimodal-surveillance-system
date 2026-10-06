"""End-to-end integration tests for Video Surveillance & Object Tracking pipeline."""

import os
import pytest
from src.core.di_container import DIContainer
from src.application.video_surveillance_service import VideoSurveillanceService
from src.infrastructure.database.repositories import AnalysisRepository
from src.domain.entities import VideoAnalysisRequest
from src.core.exceptions import ValidationError


def test_end_to_end_demo_video_pipeline():
    DIContainer.reset()
    container = DIContainer()
    service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)
    analysis_repo: AnalysisRepository = container.resolve(AnalysisRepository)

    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Military Reconnaissance Feed"
    )

    resp = service.process_video_analysis(req)

    assert resp.analysis_id is not None
    assert resp.source_type == "DEMO"
    assert resp.platform == "DRONE"
    assert resp.video_metadata is not None
    assert resp.video_metadata.duration_seconds > 0
    assert resp.video_metadata.fps > 0
    assert resp.video_metadata.sampled_frames > 0
    assert resp.threat_assessment.threat_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert resp.processing_time_ms >= 0.0

    # Verify database persistence
    persisted_record = analysis_repo.get_by_id(resp.analysis_id)
    assert persisted_record is not None
    assert persisted_record.id == resp.analysis_id
    assert persisted_record.media_type == "VIDEO"
    assert persisted_record.threat_level == resp.threat_assessment.threat_level

    # Verify artifact JSON persistence and track retrieval
    assert persisted_record.artifact_path is not None
    assert os.path.exists(persisted_record.artifact_path)
    tracks = analysis_repo.get_tracks_by_artifact_path(persisted_record.artifact_path)
    assert isinstance(tracks, list)


def test_end_to_end_uploaded_video_pipeline():
    DIContainer.reset()
    container = DIContainer()
    service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)
    analysis_repo: AnalysisRepository = container.resolve(AnalysisRepository)

    video_path = "data/demo/cctv/videos/cctv_perimeter_demo.mp4"
    assert os.path.exists(video_path)

    req = VideoAnalysisRequest(
        source_type="UPLOAD",
        platform="CCTV",
        video_path=video_path
    )

    resp = service.process_video_analysis(req)

    assert resp.analysis_id is not None
    assert resp.source_type == "UPLOAD"
    assert resp.platform == "CCTV"
    assert resp.video_metadata is not None
    assert resp.video_metadata.sampled_frames > 0

    persisted_record = analysis_repo.get_by_id(resp.analysis_id)
    assert persisted_record is not None
    assert persisted_record.media_type == "VIDEO"
