"""Unit tests for ExplainabilityService."""

from src.infrastructure.services.explainability import ExplainabilityService
from src.domain.entities import DetectionResult, BoundingBox


def test_explainability_service_low():
    service = ExplainabilityService()
    dets = [DetectionResult(detection_id="1", class_id=0, class_name="person", confidence=0.9, bbox=BoundingBox(0,0,10,10))]
    res = service.explain(5.0, "LOW", dets, {"platform": "DRONE"})
    assert "xai_reason" in res
    assert "recommended_sop" in res
    assert "LOW" in res["xai_reason"]
    assert "normal surveillance observations" in res["xai_reason"]
    assert "No verified security-risk signal was available" in res["xai_reason"]
    assert "no temporal risk signal was evaluated in this image-only analysis" in res["xai_reason"]
    assert "Continue routine monitoring" in res["recommended_sop"]


def test_explainability_service_verified_zone_violation():
    service = ExplainabilityService()
    dets = [DetectionResult(detection_id="1", class_id=0, class_name="person", confidence=0.9, bbox=BoundingBox(0,0,10,10))]
    res = service.explain(70.0, "HIGH", dets, {"platform": "CCTV", "zone_violation_flag": True})
    assert "xai_reason" in res
    assert "verified" in res["xai_reason"]
    assert "restricted-zone violation signal" in res["xai_reason"]
    assert "No temporal risk signal was evaluated in this image-only analysis" in res["xai_reason"]
    assert "Escalate to the designated site duty supervisor" in res["recommended_sop"]


def test_explainability_service_critical_safety_wording():
    service = ExplainabilityService()
    dets = [DetectionResult(detection_id="1", class_id=0, class_name="person", confidence=0.9, bbox=BoundingBox(0,0,10,10))]
    res = service.explain(90.0, "CRITICAL", dets, {"platform": "CCTV", "zone_violation_flag": True, "unauthorized_access_signal": True})
    sop_text = res["recommended_sop"]
    assert "Immediately escalate to the designated supervisor" in sop_text
    assert "authorized emergency response procedure" in sop_text


