"""End-to-end integration tests for Feature 005 Contextual Threat Assessment & Analyst Review pipeline."""

import os
import pytest
from src.core.di_container import DIContainer
from src.application.video_surveillance_service import VideoSurveillanceService
from src.application.contextual_assessment_service import ContextualAssessmentService
from src.application.analyst_review_service import AnalystReviewService
from src.infrastructure.database.repositories import AnalysisRepository, AnalystReviewRepository
from src.domain.entities import VideoAnalysisRequest, RestrictedZone


def test_end_to_end_contextual_threat_and_analyst_review_pipeline():
    DIContainer.reset()
    container = DIContainer()

    video_service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)
    contextual_service: ContextualAssessmentService = container.resolve(ContextualAssessmentService)
    review_service: AnalystReviewService = container.resolve(AnalystReviewService)
    analysis_repo: AnalysisRepository = container.resolve(AnalysisRepository)
    review_repo: AnalystReviewRepository = container.resolve(AnalystReviewRepository)

    # 1. Video ingestion -> YOLO detection -> IoU tracking
    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Restricted Breach"
    )

    resp = video_service.process_video_analysis(req)
    assert resp.analysis_id is not None
    assert resp.tracks is not None
    assert len(resp.tracks) > 0

    # Verify primary Feature 003 threat score baseline formula intact
    original_ai_score = resp.threat_assessment.threat_score
    assert 0.0 <= original_ai_score <= 100.0

    # 2. Spatial zone evaluation & Separate Contextual Assessment
    zones = [
        RestrictedZone(
            zone_id="Z1",
            name="Perimeter Red Zone",
            platform="DRONE",
            polygon_points=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
            is_active=True
        )
    ]
    assessment = contextual_service.evaluate_spatial_context(
        analysis_id=resp.analysis_id,
        detections=[],
        tracks=resp.tracks,
        platform="DRONE",
        zones=zones,
        scenario_metadata_signal=False
    )

    assert assessment.analysis_id == resp.analysis_id
    assert assessment.spatial_threat_score >= 0.0
    # Primary threat score baseline formula intact
    assert resp.threat_assessment.threat_score == original_ai_score
    assert len(assessment.events) > 0

    # 3. Initial Analyst Review Submission (PENDING_REVIEW -> ACKNOWLEDGED)
    review_record_1 = review_service.submit_review(
        analysis_id=resp.analysis_id,
        review_status="ACKNOWLEDGED",
        analyst_id="OPERATOR_01",
        notes="Confirmed drone perimeter breach event."
    )

    assert review_record_1.analysis_id == resp.analysis_id
    assert review_record_1.review_status == "ACKNOWLEDGED"
    assert review_record_1.analyst_id == "OPERATOR_01"

    # Verify persistence in analyst_reviews repository
    saved_review = review_repo.get_review_by_analysis_id(resp.analysis_id)
    assert saved_review is not None
    assert saved_review.review_status == "ACKNOWLEDGED"

    # 4. Secondary Analyst Review Status Transition (ACKNOWLEDGED -> FALSE_POSITIVE)
    review_record_2 = review_service.submit_review(
        analysis_id=resp.analysis_id,
        review_status="FALSE_POSITIVE",
        analyst_id="OPERATOR_02",
        notes="Re-classified as authorized maintenance vehicle after cross-checking logs."
    )

    assert review_record_2.review_status == "FALSE_POSITIVE"
    assert review_record_2.analyst_id == "OPERATOR_02"

    # 5. Strict Score Preservation Verification: Primary AI Threat score in analyses MUST NOT be altered
    db_analysis_record = analysis_repo.get_by_id(resp.analysis_id)
    assert db_analysis_record is not None
    assert db_analysis_record.threat_score == original_ai_score

    # 6. Audit Transition History Logging Verification
    history = review_repo.get_review_history(saved_review.id)
    assert len(history) == 2
    assert history[0].from_status == "PENDING_REVIEW"
    assert history[0].to_status == "ACKNOWLEDGED"
    assert history[0].analyst_id == "OPERATOR_01"

    assert history[1].from_status == "ACKNOWLEDGED"
    assert history[1].to_status == "FALSE_POSITIVE"
    assert history[1].analyst_id == "OPERATOR_02"
