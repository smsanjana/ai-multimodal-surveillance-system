"""Unit tests for ContextualAssessmentService and missing zone fallback."""

import pytest
from src.application.contextual_assessment_service import ContextualAssessmentService
from src.domain.entities import TrackRecord, RestrictedZone, TrajectoryPoint


def test_missing_zone_fallback():
    service = ContextualAssessmentService()
    tracks = [
        TrackRecord(
            track_id=1,
            class_id=5,
            class_name="Tank",
            first_frame=0,
            last_frame=50,
            first_timestamp=0.0,
            last_timestamp=10.0,
            detection_count=10,
            avg_confidence=0.85,
            movement_state="MOVING",
            pixel_displacement=50.0,
            trajectory_direction="East",
            trajectory_points=[TrajectoryPoint(100.0, 100.0, 0, 0.0)]
        )
    ]

    res = service.evaluate_spatial_context(
        analysis_id="A101",
        detections=[],
        tracks=tracks,
        platform="DRONE",
        zones=None,
        scenario_metadata_signal=False
    )

    assert res.analysis_id == "A101"
    assert res.computed_spatial_breach is False
    assert res.spatial_threat_level == "LOW"
    assert len(res.events) == 1
    assert res.events[0].event_type == "ROUTINE_TRANSIT"


def test_spatial_zone_intersection_breach():
    service = ContextualAssessmentService()
    zone = RestrictedZone(
        zone_id="Z1",
        name="Restricted Gate",
        platform="CCTV",
        polygon_points=[(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
    )

    # Track with centroid at pixel (200, 200) -> normalized (0.156, 0.277) -> inside zone
    tracks = [
        TrackRecord(
            track_id=2,
            class_id=6,
            class_name="Vehicle",
            first_frame=0,
            last_frame=20,
            first_timestamp=0.0,
            last_timestamp=4.0,
            detection_count=5,
            avg_confidence=0.90,
            movement_state="MOVING",
            pixel_displacement=30.0,
            trajectory_direction="South",
            trajectory_points=[TrajectoryPoint(200.0, 200.0, 0, 0.0)]
        )
    ]

    res = service.evaluate_spatial_context(
        analysis_id="A102",
        detections=[],
        tracks=tracks,
        platform="CCTV",
        zones=[zone],
        scenario_metadata_signal=False
    )

    assert res.computed_spatial_breach is True
    assert res.spatial_threat_level == "HIGH"
    assert len(res.events) == 1
    assert res.events[0].event_type == "ZONE_ENTRY"
