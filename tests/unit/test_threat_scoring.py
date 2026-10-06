"""Unit tests for ThreatScoringService & Image Analysis Pipeline enforcing evidence-based threat scoring guidelines."""

import pytest
from src.infrastructure.services.threat_scoring import ThreatScoringService
from src.infrastructure.services.demo_manager import DemoManager
from src.core.di_container import DIContainer
from src.application.image_surveillance_service import ImageSurveillanceService
from src.domain.entities import DetectionResult, BoundingBox, ImageAnalysisRequest


def test_parking_lot_demo_no_longer_exists():
    manager = DemoManager()
    for scen in manager.list_scenarios():
        assert "parking" not in scen["title"].lower()
        assert "warehouse loading" not in scen["title"].lower()


def test_replacement_cctv_restricted_gate_vehicle_entry():
    manager = DemoManager()
    scen = manager.get_scenario("CCTV Restricted Gate Vehicle Entry")
    assert scen is not None
    assert scen["platform"] == "CCTV"
    assert scen["zone_violation_flag"] is True


def test_drone_traffic_observation_retains_multiple_yolo_detections():
    DIContainer.reset()
    container = DIContainer()
    service: ImageSurveillanceService = container.resolve(ImageSurveillanceService)
    
    req = ImageAnalysisRequest(source_type="DEMO", platform="DRONE", scenario_name="Drone Traffic Observation")
    resp = service.process_image(req)
    
    assert resp.scenario_name == "Drone Traffic Observation"
    assert len(resp.detections) > 1, f"Expected multiple YOLO detections for traffic image, got {len(resp.detections)}"
    for det in resp.detections:
        assert det.class_name is not None
        assert det.confidence > 0.0
        assert det.bbox is not None
        assert det.detection_id is not None


def test_cctv_normal_entrance_remains_low_without_verified_evidence():
    service = ThreatScoringService()
    dets = [
        DetectionResult(detection_id="1", class_id=2, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10)),
        DetectionResult(detection_id="2", class_id=0, class_name="person", confidence=0.85, bbox=BoundingBox(0,0,10,10))
    ]
    res = service.evaluate_threat(dets, {"platform": "CCTV", "scenario_name": "CCTV Normal Entrance Activity", "zone_violation_flag": False})
    assert res.threat_score == 5.0
    assert res.threat_level == "LOW"


def test_cctv_restricted_gate_vehicle_entry_receives_high_when_verified_zone_evidence_true():
    service = ThreatScoringService()
    dets = [
        DetectionResult(detection_id="1", class_id=2, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10))
    ]
    res = service.evaluate_threat(dets, {"platform": "CCTV", "scenario_name": "CCTV Restricted Gate Vehicle Entry", "zone_violation_flag": True})
    assert res.threat_score == 70.0
    assert res.threat_level == "HIGH"
    zone_factors = [f for f in res.factors if f.factor_name == "Verified Restricted Zone Signal"]
    assert len(zone_factors) == 1
    assert zone_factors[0].score_delta == 65.0


def test_scenario_names_do_not_alter_numeric_score():
    service = ThreatScoringService()
    dets = [
        DetectionResult(detection_id="1", class_id=2, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10)),
        DetectionResult(detection_id="2", class_id=0, class_name="person", confidence=0.8, bbox=BoundingBox(0,0,10,10))
    ]
    res_entrance = service.evaluate_threat(dets, {"platform": "CCTV", "scenario_name": "CCTV Normal Entrance Activity"})
    res_unauth = service.evaluate_threat(dets, {"platform": "CCTV", "scenario_name": "CCTV Restricted Gate Vehicle Entry", "zone_violation_flag": False})
    res_traffic = service.evaluate_threat(dets, {"platform": "DRONE", "scenario_name": "Drone Traffic Observation"})

    assert res_entrance.threat_score == res_unauth.threat_score == res_traffic.threat_score == 5.0
    assert res_entrance.threat_level == res_unauth.threat_level == res_traffic.threat_level == "LOW"


def test_false_or_absent_zone_evidence_produces_no_zone_threat_contribution():
    service = ThreatScoringService()
    dets = [
        DetectionResult(detection_id="1", class_id=2, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10))
    ]
    res = service.evaluate_threat(dets, {"platform": "CCTV", "scenario_name": "CCTV Facility Access Monitoring", "zone_violation_flag": False})
    assert res.threat_score == 5.0
    assert res.threat_level == "LOW"
    zone_factors = [f for f in res.factors if f.factor_name == "Restricted Zone Signal"]
    assert len(zone_factors) == 1
    assert zone_factors[0].score_delta == 0.0
    assert "No restricted-zone violation was established." in zone_factors[0].description


def test_threat_score_clamping_and_level_boundaries():
    service = ThreatScoringService()
    # Zero detections baseline LOW
    res_zero = service.evaluate_threat([], {})
    assert 0.0 <= res_zero.threat_score <= 24.9
    assert res_zero.threat_level == "LOW"
    assert res_zero.threat_score == 0.0

    # HIGH via verified zone violation (70.0)
    res_high = service.evaluate_threat([DetectionResult(detection_id="1", class_id=0, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10))], {"zone_violation_flag": True})
    assert 50.0 <= res_high.threat_score <= 74.9
    assert res_high.threat_level == "HIGH"
    assert res_high.threat_score == 70.0

    # CRITICAL via verified access signal (90.0)
    res_crit = service.evaluate_threat([DetectionResult(detection_id="1", class_id=0, class_name="car", confidence=0.9, bbox=BoundingBox(0,0,10,10))], {"zone_violation_flag": True, "unauthorized_access_signal": True})
    assert 75.0 <= res_crit.threat_score <= 100.0
    assert res_crit.threat_level == "CRITICAL"
    assert res_crit.threat_score == 90.0

def test_military_object_detections_are_neutral_observations_without_zone_violation():
    """T010: Verify military detections (Tank, Missile, Soldier, etc.) act as neutral observations."""
    service = ThreatScoringService()
    military_dets = [
        DetectionResult(detection_id="1", class_id=5, class_name="Tank", confidence=0.95, bbox=BoundingBox(10, 10, 100, 100)),
        DetectionResult(detection_id="2", class_id=1, class_name="Missile", confidence=0.88, bbox=BoundingBox(110, 10, 200, 100)),
        DetectionResult(detection_id="3", class_id=4, class_name="Soldier", confidence=0.91, bbox=BoundingBox(210, 10, 250, 100))
    ]
    res = service.evaluate_threat(military_dets, {"platform": "DRONE", "scenario_name": "Drone Normal Patrol", "zone_violation_flag": False})
    
    assert res.threat_level == "LOW"
    assert res.threat_score < 25.0
    assert res.threat_score == 5.0
