"""Unit tests for SpatialZoneEvaluator geometry math."""

import pytest
from src.infrastructure.services.spatial_zone_evaluator import SpatialZoneEvaluator
from src.domain.entities import RestrictedZone


def test_convert_normalized_polygon_to_pixels():
    evaluator = SpatialZoneEvaluator()
    norm_polygon = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
    pixel_pts = evaluator.convert_normalized_polygon_to_pixels(norm_polygon, width=1000, height=800)

    assert pixel_pts == [(0, 0), (500, 0), (500, 400), (0, 400)]


def test_is_centroid_in_zone_inside():
    evaluator = SpatialZoneEvaluator()
    zone = RestrictedZone(
        zone_id="Z1",
        name="Test Restricted Zone",
        platform="DRONE",
        polygon_points=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
    )

    # Centroid clearly inside (0.5, 0.5)
    assert evaluator.is_centroid_in_zone((0.5, 0.5), zone) is True


def test_is_centroid_in_zone_outside():
    evaluator = SpatialZoneEvaluator()
    zone = RestrictedZone(
        zone_id="Z1",
        name="Test Restricted Zone",
        platform="DRONE",
        polygon_points=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
    )

    # Centroid clearly outside (0.1, 0.1)
    assert evaluator.is_centroid_in_zone((0.1, 0.1), zone) is False


def test_is_centroid_on_boundary_edge():
    evaluator = SpatialZoneEvaluator()
    zone = RestrictedZone(
        zone_id="Z1",
        name="Test Restricted Zone",
        platform="DRONE",
        polygon_points=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
    )

    # Centroid exactly on edge (0.2, 0.5) -> dist >= 0 should be True
    assert evaluator.is_centroid_in_zone((0.2, 0.5), zone) is True


def test_invalid_or_missing_polygon():
    evaluator = SpatialZoneEvaluator()
    zone_invalid = RestrictedZone(
        zone_id="Z2",
        name="Invalid Zone",
        platform="CCTV",
        polygon_points=[(0.1, 0.1), (0.2, 0.2)]  # less than 3 points
    )

    assert evaluator.is_centroid_in_zone((0.15, 0.15), zone_invalid) is False
