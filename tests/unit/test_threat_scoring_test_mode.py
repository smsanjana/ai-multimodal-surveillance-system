"""
Synthetic Test Fixture and Automated Verification for Threat Scoring Service.

This module provides a clearly labeled TEST MODE synthetic fixture that passes
simulated zone_violation_flag and unauthorized_access_signal to the ThreatScoringService.
All test evidence is explicitly tagged with '[SIMULATED TEST FIXTURE]' to prevent
pretending uploaded images represent real perimeter breaches or polluting production data.
"""

import pytest
from src.infrastructure.services.threat_scoring import ThreatScoringService
from src.domain.entities import DetectionResult, BoundingBox


class SyntheticTestFixture:
    """
    Clearly labeled synthetic test fixture providing mock military detection data
    and simulated security evidence metadata for TEST MODE verification.
    """

    @staticmethod
    def create_military_detections():
        """Returns synthetic military object detections (Tank, Soldier, Missile)."""
        return [
            DetectionResult(
                detection_id="sim-det-001",
                class_id=5,
                class_name="Tank",
                confidence=0.92,
                bbox=BoundingBox(x_min=100, y_min=100, x_max=250, y_max=200)
            ),
            DetectionResult(
                detection_id="sim-det-002",
                class_id=4,
                class_name="Soldier",
                confidence=0.88,
                bbox=BoundingBox(x_min=260, y_min=100, x_max=300, y_max=200)
            )
        ]

    @staticmethod
    def get_metadata_detection_only():
        """Metadata for State 1: Detection only (No simulated zone breach)."""
        return {
            "test_mode": True,
            "simulated_evidence_label": "[SIMULATED TEST FIXTURE] Detection Only Baseline",
            "platform": "DRONE",
            "scenario_name": "Test Military Observation",
            "zone_violation_flag": False,
            "unauthorized_access_signal": False
        }

    @staticmethod
    def get_metadata_detection_and_zone_violation():
        """Metadata for State 2: Detection + Verified Zone Violation."""
        return {
            "test_mode": True,
            "simulated_evidence_label": "[SIMULATED TEST FIXTURE] Verified Restricted Zone Signal",
            "platform": "DRONE",
            "scenario_name": "Test Restricted Zone Breach",
            "zone_violation_flag": True,
            "unauthorized_access_signal": False
        }

    @staticmethod
    def get_metadata_detection_zone_and_unauthorized_access():
        """Metadata for State 3: Detection + Zone Violation + Unauthorized Access."""
        return {
            "test_mode": True,
            "simulated_evidence_label": "[SIMULATED TEST FIXTURE] Verified Access Breach Condition",
            "platform": "CCTV",
            "scenario_name": "Test Perimeter Access Breach",
            "zone_violation_flag": True,
            "unauthorized_access_signal": True
        }


def test_state_1_detection_only_yields_5_low():
    """Verify State 1: Detection only -> 5.0 / 100, LOW threat level."""
    service = ThreatScoringService()
    detections = SyntheticTestFixture.create_military_detections()
    metadata = SyntheticTestFixture.get_metadata_detection_only()

    result = service.evaluate_threat(detections, metadata)

    assert result.threat_score == 5.0, f"Expected 5.0, got {result.threat_score}"
    assert result.threat_level == "LOW", f"Expected LOW, got {result.threat_level}"
    assert any(f.factor_name == "Surveillance Baseline Observation" and f.score_delta == 5.0 for f in result.factors)
    assert any(f.factor_name == "Restricted Zone Signal" and f.score_delta == 0.0 for f in result.factors)


def test_state_2_detection_plus_zone_violation_yields_70_high():
    """Verify State 2: Detection + Verified Zone Violation -> 70.0 / 100, HIGH threat level."""
    service = ThreatScoringService()
    detections = SyntheticTestFixture.create_military_detections()
    metadata = SyntheticTestFixture.get_metadata_detection_and_zone_violation()

    result = service.evaluate_threat(detections, metadata)

    assert result.threat_score == 70.0, f"Expected 70.0, got {result.threat_score}"
    assert result.threat_level == "HIGH", f"Expected HIGH, got {result.threat_level}"
    assert any(f.factor_name == "Verified Restricted Zone Signal" and f.score_delta == 65.0 for f in result.factors)


def test_state_3_detection_zone_violation_and_unauthorized_access_yields_90_critical():
    """Verify State 3: Detection + Zone Violation + Unauthorized Access -> 90.0 / 100, CRITICAL threat level."""
    service = ThreatScoringService()
    detections = SyntheticTestFixture.create_military_detections()
    metadata = SyntheticTestFixture.get_metadata_detection_zone_and_unauthorized_access()

    result = service.evaluate_threat(detections, metadata)

    assert result.threat_score == 90.0, f"Expected 90.0, got {result.threat_score}"
    assert result.threat_level == "CRITICAL", f"Expected CRITICAL, got {result.threat_level}"
    assert any(f.factor_name == "Verified Restricted Zone Signal" and f.score_delta == 65.0 for f in result.factors)
    assert any(f.factor_name == "Verified Unauthorized Access Signal" and f.score_delta == 20.0 for f in result.factors)
