"""Unit test suite for Phase 1 Dynamic Spatial Polygon Integration & Trajectory Evidence Tracking."""

import pytest
from typing import List
from src.domain.entities import (
    TrackRecord, TrajectoryPoint, RestrictedZone, VideoAnalysisRequest, DetectionResult, BoundingBox
)
from src.infrastructure.services.spatial_zone_evaluator import SpatialZoneEvaluator
from src.application.video_surveillance_service import VideoSurveillanceService


def build_track(track_id: int, points: List[tuple], class_name: str = "Tank", movement_state: str = "MOVING") -> TrackRecord:
    traj = [
        TrajectoryPoint(x=x, y=y, frame_index=i * 5, timestamp_sec=i * 1.0)
        for i, (x, y) in enumerate(points)
    ]
    return TrackRecord(
        track_id=track_id,
        class_id=5,
        class_name=class_name,
        first_frame=0,
        last_frame=len(points) * 5,
        first_timestamp=0.0,
        last_timestamp=float(len(points)),
        detection_count=len(points),
        avg_confidence=0.92,
        movement_state=movement_state,
        pixel_displacement=50.0 if movement_state == "MOVING" else 0.0,
        trajectory_direction="East",
        trajectory_points=traj
    )


@pytest.fixture
def evaluator():
    return SpatialZoneEvaluator()


@pytest.fixture
def sample_zone():
    return RestrictedZone(
        zone_id="Z1_TEST",
        name="Test Red Polygon",
        platform="DRONE",
        polygon_points=[(0.4, 0.4), (0.8, 0.4), (0.8, 0.8), (0.4, 0.8)],
        is_active=True
    )


# 1. Outside Zone Test
def test_track_strictly_outside_zone(evaluator, sample_zone):
    # Centroid points in normalized [0.0, 1.0] outside (0.4, 0.4)-(0.8, 0.8)
    tr = build_track(1, [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)])
    events = evaluator.evaluate_track_spatial_events(tr, [sample_zone], width=1280, height=720)
    
    assert len(events) == 0 or all(not e.curr_inside for e in events)
    for e in events:
        assert e.event_type != "ZONE_ENTRY"
        assert e.is_dynamic_evidence is True


# 2. Remaining Inside Zone Test
def test_track_remaining_inside_zone(evaluator, sample_zone):
    tr = build_track(2, [(0.5, 0.5), (0.6, 0.6), (0.7, 0.7)], movement_state="MOVING")
    events = evaluator.evaluate_track_spatial_events(tr, [sample_zone], width=1280, height=720)
    
    assert len(events) > 0
    assert any(e.event_type == "ZONE_TRANSIT" for e in events)
    first_event = events[0]
    assert first_event.curr_inside is True
    assert first_event.prev_inside is True
    assert first_event.zone_id == "Z1_TEST"
    assert first_event.is_dynamic_evidence is True


# 3. Zone Entry Test
def test_track_zone_entry(evaluator, sample_zone):
    # Starts outside at (0.2, 0.2), enters at (0.5, 0.5)
    tr = build_track(3, [(0.2, 0.2), (0.5, 0.5), (0.6, 0.6)])
    events = evaluator.evaluate_track_spatial_events(tr, [sample_zone], width=1280, height=720)
    
    entry_events = [e for e in events if e.event_type == "ZONE_ENTRY"]
    assert len(entry_events) == 1
    ev = entry_events[0]
    assert ev.prev_inside is False
    assert ev.curr_inside is True
    assert ev.prev_centroid == (0.2, 0.2)
    assert ev.curr_centroid == (0.5, 0.5)
    assert ev.is_dynamic_evidence is True


# 4. Zone Exit Test
def test_track_zone_exit(evaluator, sample_zone):
    # Starts inside at (0.5, 0.5), exits to (0.1, 0.1)
    tr = build_track(4, [(0.5, 0.5), (0.1, 0.1)])
    events = evaluator.evaluate_track_spatial_events(tr, [sample_zone], width=1280, height=720)
    
    exit_events = [e for e in events if e.event_type == "ZONE_EXIT"]
    assert len(exit_events) == 1
    ev = exit_events[0]
    assert ev.prev_inside is True
    assert ev.curr_inside is False
    assert ev.prev_centroid == (0.5, 0.5)
    assert ev.curr_centroid == (0.1, 0.1)


# 5. Boundary Crossing Test
def test_track_boundary_crossing_transitions(evaluator, sample_zone):
    # Outside -> Inside -> Outside
    tr = build_track(5, [(0.2, 0.2), (0.5, 0.5), (0.9, 0.9)])
    events = evaluator.evaluate_track_spatial_events(tr, [sample_zone], width=1280, height=720)
    
    event_types = [e.event_type for e in events]
    assert "ZONE_ENTRY" in event_types
    assert "ZONE_EXIT" in event_types


# 6. Multiple Tracks Test
def test_multiple_tracks_dynamic_evaluation(evaluator, sample_zone):
    tr_outside = build_track(10, [(0.1, 0.1), (0.2, 0.2)])
    tr_inside = build_track(11, [(0.2, 0.2), (0.6, 0.6)])
    
    events_out = evaluator.evaluate_track_spatial_events(tr_outside, [sample_zone], width=1280, height=720)
    events_in = evaluator.evaluate_track_spatial_events(tr_inside, [sample_zone], width=1280, height=720)
    
    assert any(e.event_type == "ZONE_ENTRY" for e in events_in)
    assert not any(e.event_type == "ZONE_ENTRY" for e in events_out)


# 7. Disappearing / Reappearing Tracks Test
def test_disappearing_and_reappearing_tracks(evaluator, sample_zone):
    tr1 = build_track(20, [(0.1, 0.1), (0.2, 0.2)])  # Track 20 ends outside
    tr2 = build_track(21, [(0.5, 0.5), (0.6, 0.6)])  # Track 21 appears inside later
    
    events1 = evaluator.evaluate_track_spatial_events(tr1, [sample_zone], width=1280, height=720)
    events2 = evaluator.evaluate_track_spatial_events(tr2, [sample_zone], width=1280, height=720)
    
    assert len(events1) == 0 or all(not e.curr_inside for e in events1)
    assert len(events2) > 0 and all(e.curr_inside for e in events2)


# 8. Empty Detections Test
def test_empty_detections_spatial_eval(evaluator, sample_zone):
    empty_tr = TrackRecord(
        track_id=99, class_id=0, class_name="Vehicle", first_frame=0, last_frame=0,
        first_timestamp=0.0, last_timestamp=0.0, detection_count=0, avg_confidence=0.0,
        movement_state="STATIONARY", pixel_displacement=0.0, trajectory_direction="Stationary",
        trajectory_points=[]
    )
    events = evaluator.evaluate_track_spatial_events(empty_tr, [sample_zone], width=1280, height=720)
    assert len(events) == 0


# 9. Invalid Polygons Test
def test_invalid_polygon_graceful_handling(evaluator):
    invalid_zone = RestrictedZone(
        zone_id="Z_INVALID",
        name="Invalid 2-point Line",
        platform="DRONE",
        polygon_points=[(0.1, 0.1), (0.2, 0.2)],  # Less than 3 points
        is_active=True
    )
    tr = build_track(30, [(0.15, 0.15), (0.18, 0.18)])
    events = evaluator.evaluate_track_spatial_events(tr, [invalid_zone], width=1280, height=720)
    assert len(events) == 0
    assert evaluator.is_centroid_in_zone((0.15, 0.15), invalid_zone) is False


# 10. Normalized Coordinate vs Pixel Coordinates Test
def test_normalized_vs_pixel_coordinates(evaluator, sample_zone):
    # Normalized centroid inside (0.5, 0.5)
    assert evaluator.is_centroid_in_zone((0.5, 0.5), sample_zone, width=1280, height=720) is True
    # Raw pixel centroid (640, 360) corresponding to (0.5, 0.5)
    assert evaluator.is_centroid_in_zone((640.0, 360.0), sample_zone, width=1280, height=720) is True
    # Outside pixel centroid (100, 100)
    assert evaluator.is_centroid_in_zone((100.0, 100.0), sample_zone, width=1280, height=720) is False
