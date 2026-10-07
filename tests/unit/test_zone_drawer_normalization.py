"""Unit & Integration test suite for Phase 2 Interactive Polygon Zone Drawer & Normalization."""

import pytest
from typing import List, Tuple
from src.ui.components import normalize_canvas_polygon, create_custom_restricted_zone
from src.domain.entities import RestrictedZone, VideoAnalysisRequest, VideoAnalysisResult, TrackRecord, TrajectoryPoint
from src.infrastructure.services.spatial_zone_evaluator import SpatialZoneEvaluator
from src.application.video_surveillance_service import VideoSurveillanceService


# 1. Coordinate Normalization Tests
def test_normalize_canvas_polygon_basic():
    # 640x360 canvas: midpoint (320, 180) -> (0.5, 0.5)
    pixel_pts = [(0.0, 0.0), (320.0, 180.0), (640.0, 360.0)]
    norm_pts = normalize_canvas_polygon(pixel_pts, canvas_w=640.0, canvas_h=360.0)
    
    assert len(norm_pts) == 3
    assert norm_pts[0] == (0.0, 0.0)
    assert norm_pts[1] == (0.5, 0.5)
    assert norm_pts[2] == (1.0, 1.0)


# 2. Different Canvas Aspect Ratios
def test_normalize_canvas_polygon_different_aspect_ratios():
    # Aspect Ratio 1: 16:9 canvas (1280x720)
    norm_16_9 = normalize_canvas_polygon([(640.0, 360.0)], canvas_w=1280.0, canvas_h=720.0)
    assert norm_16_9[0] == (0.5, 0.5)

    # Aspect Ratio 2: 4:3 canvas (640x480)
    norm_4_3 = normalize_canvas_polygon([(320.0, 240.0)], canvas_w=640.0, canvas_h=480.0)
    assert norm_4_3[0] == (0.5, 0.5)

    # Aspect Ratio 3: 1:1 canvas (1000x1000)
    norm_1_1 = normalize_canvas_polygon([(250.0, 750.0)], canvas_w=1000.0, canvas_h=1000.0)
    assert norm_1_1[0] == (0.25, 0.75)


# 3. Fewer Than 3 Vertices (Guard Test)
def test_fewer_than_3_vertices_returns_none():
    pts_1 = [(100.0, 100.0)]
    pts_2 = [(100.0, 100.0), (200.0, 200.0)]
    
    norm_1 = normalize_canvas_polygon(pts_1, canvas_w=640.0, canvas_h=360.0)
    norm_2 = normalize_canvas_polygon(pts_2, canvas_w=640.0, canvas_h=360.0)
    
    zone_1 = create_custom_restricted_zone(norm_1, platform="DRONE")
    zone_2 = create_custom_restricted_zone(norm_2, platform="DRONE")
    
    assert zone_1 is None
    assert zone_2 is None


# 4. Exactly 3 Vertices
def test_exactly_3_vertices_constructs_valid_zone():
    pixel_pts = [(100.0, 100.0), (300.0, 100.0), (200.0, 300.0)]
    norm_pts = normalize_canvas_polygon(pixel_pts, canvas_w=640.0, canvas_h=360.0)
    
    zone = create_custom_restricted_zone(norm_pts, platform="DRONE", zone_id="Z_TRIANGLE", name="Triangle Zone")
    assert zone is not None
    assert isinstance(zone, RestrictedZone)
    assert zone.zone_id == "Z_TRIANGLE"
    assert zone.platform == "DRONE"
    assert len(zone.polygon_points) == 3


# 5. More Than 3 Vertices (Complex Polygon)
def test_more_than_3_vertices_constructs_valid_zone():
    pixel_pts = [(100.0, 100.0), (400.0, 100.0), (500.0, 300.0), (300.0, 400.0), (100.0, 300.0)]
    norm_pts = normalize_canvas_polygon(pixel_pts, canvas_w=640.0, canvas_h=480.0)
    
    zone = create_custom_restricted_zone(norm_pts, platform="CCTV")
    assert zone is not None
    assert len(zone.polygon_points) == 5
    assert zone.platform == "CCTV"


# 6. Coordinates Outside Canvas Bounds (Clamping Test)
def test_coordinates_outside_canvas_bounds_clamped():
    out_of_bounds = [(-50.0, -100.0), (800.0, 200.0), (300.0, 900.0)]
    norm_pts = normalize_canvas_polygon(out_of_bounds, canvas_w=640.0, canvas_h=360.0)
    
    assert len(norm_pts) == 3
    # Clamped to range [0.0, 1.0]
    assert norm_pts[0] == (0.0, 0.0)
    assert norm_pts[1] == (1.0, 0.5556)
    assert norm_pts[2] == (0.4688, 1.0)


# 7. RestrictedZone Construction & Properties
def test_restricted_zone_entity_properties():
    norm_pts = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
    zone = create_custom_restricted_zone(norm_pts, platform="DRONE", zone_id="Z_CUSTOM_123", name="Custom Zone Alpha")
    
    assert zone.zone_id == "Z_CUSTOM_123"
    assert zone.name == "Custom Zone Alpha"
    assert zone.platform == "DRONE"
    assert zone.is_active is True
    assert zone.polygon_points == norm_pts


# 8. Request.zones Propagation Test
def test_request_zones_propagation():
    norm_pts = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8)]
    custom_zone = create_custom_restricted_zone(norm_pts, platform="DRONE")
    
    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Aerial Border Patrol - Routine Transit",
        zones=[custom_zone]
    )
    
    assert req.zones is not None
    assert len(req.zones) == 1
    assert req.zones[0].zone_id == "Z_CUSTOM_DRONE"


# 9. Existing No-Custom-Zone Fallback Behavior
def test_request_without_custom_zones_uses_fallback():
    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Aerial Border Patrol - Routine Transit",
        zones=None
    )
    
    assert req.zones is None


# 10. Dynamic Zone Pipeline Integration Test
def test_custom_zone_dynamic_pipeline_integration(container_services=None):
    from src.core.di_container import DIContainer
    from unittest.mock import MagicMock
    from src.domain.entities import TrackRecord, TrajectoryPoint

    container = DIContainer()
    video_service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)
    
    # Define custom zone around (0.4, 0.4) to (0.9, 0.9)
    custom_zone = RestrictedZone(
        zone_id="Z_CUSTOM_TEST",
        name="Custom Analyst Zone",
        platform="DRONE",
        polygon_points=[(0.4, 0.4), (0.9, 0.4), (0.9, 0.9), (0.4, 0.9)],
        is_active=True
    )
    
    req = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="drone_restricted_video",
        zones=[custom_zone]
    )

    # Mock tracking_service to ensure a track enters the custom polygon deterministically across test environments
    mock_track = TrackRecord(
        track_id=1,
        class_id=5,
        class_name="Tank",
        first_frame=0,
        last_frame=10,
        first_timestamp=0.0,
        last_timestamp=0.4,
        detection_count=2,
        avg_confidence=0.9,
        movement_state="MOVING",
        pixel_displacement=50.0,
        trajectory_direction="East",
        trajectory_points=[
            TrajectoryPoint(x=0.2, y=0.2, frame_index=0, timestamp_sec=0.0),
            TrajectoryPoint(x=0.5, y=0.5, frame_index=5, timestamp_sec=0.2)
        ]
    )
    mock_tracker = MagicMock()
    mock_tracker.finish_tracks.return_value = [mock_track]
    mock_tracker.update.return_value = [mock_track]
    video_service.tracking_service = mock_tracker
    
    res: VideoAnalysisResult = video_service.process_video(req)
    assert res.analysis_id is not None
    assert res.threat_assessment is not None
    assert res.threat_assessment.threat_score >= 70.0  # Dynamic zone breach triggered (+65)
    assert res.threat_assessment.threat_level == "HIGH"
