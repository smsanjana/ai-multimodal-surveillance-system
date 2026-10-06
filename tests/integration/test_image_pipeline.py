"""End-to-end integration tests for Image Surveillance Processing pipeline."""

import os
import pytest
from src.core.di_container import DIContainer
from src.application.image_surveillance_service import ImageSurveillanceService
from src.infrastructure.database.repositories import AnalysisRepository
from src.domain.entities import ImageAnalysisRequest


def test_end_to_end_demo_image_pipeline():
    DIContainer.reset()
    container = DIContainer()
    service: ImageSurveillanceService = container.resolve(ImageSurveillanceService)
    analysis_repo: AnalysisRepository = container.resolve(AnalysisRepository)

    req = ImageAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Restricted Area Intrusion"
    )

    resp = service.process_image(req)

    assert resp.analysis_id is not None
    assert resp.source_type == "DEMO"
    assert resp.platform == "DRONE"
    assert resp.original_image_bytes is not None and len(resp.original_image_bytes) > 0
    assert resp.annotated_image_bytes is not None and len(resp.annotated_image_bytes) > 0
    assert resp.threat_assessment.threat_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert resp.processing_time_ms >= 0.0

    # Verify database persistence
    persisted_record = analysis_repo.get_by_id(resp.analysis_id)
    assert persisted_record is not None
    assert persisted_record.id == resp.analysis_id
    assert persisted_record.threat_level == resp.threat_assessment.threat_level
