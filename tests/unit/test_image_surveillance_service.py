"""Unit tests for ImageSurveillanceService orchestrator."""

import pytest
import numpy as np
from src.application.image_surveillance_service import ImageSurveillanceService
from src.domain.entities import ImageAnalysisRequest, DetectionResult, BoundingBox, ThreatAssessmentResult, AnalysisRecord
from src.domain.interfaces import AbstractDetectionService, AbstractThreatScoringService, AbstractExplainabilityService, IAnalysisRepository
from src.infrastructure.services.demo_manager import DemoManager


class MockDetectionService(AbstractDetectionService):
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.25):
        return [
            DetectionResult(detection_id="d1", class_id=0, class_name="person", confidence=0.92, bbox=BoundingBox(10, 10, 50, 50))
        ]

    def draw_annotations(self, image: np.ndarray, detections):
        return image.copy()


class MockThreatScoringService(AbstractThreatScoringService):
    def evaluate_threat(self, detections, metadata):
        return ThreatAssessmentResult(threat_score=35.0, threat_level="MEDIUM", factors=[], xai_reason="", recommended_sop="")


class MockExplainabilityService(AbstractExplainabilityService):
    def explain(self, threat_score, threat_level, detections, metadata):
        return {"xai_reason": "Test rationale", "recommended_sop": "Test SOP"}


class MockAnalysisRepository(IAnalysisRepository):
    def get_all(self, platform=None, threat_level=None):
        return []
    def get_by_id(self, analysis_id):
        return None
    def save(self, record):
        return record
    def save_analysis_with_detections(self, record, detections, threat_assessment=None):
        return record


def test_image_surveillance_service_demo_flow():
    demo_manager = DemoManager()
    service = ImageSurveillanceService(
        detection_service=MockDetectionService(),
        threat_scoring_service=MockThreatScoringService(),
        explainability_service=MockExplainabilityService(),
        analysis_repository=MockAnalysisRepository(),
        demo_manager=demo_manager
    )

    req = ImageAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Normal Patrol"
    )

    resp = service.process_image(req)
    assert resp.analysis_id is not None
    assert resp.threat_assessment.threat_level == "MEDIUM"
    assert resp.threat_assessment.threat_score == 35.0
    assert len(resp.detections) == 1
    assert resp.persisted is True
