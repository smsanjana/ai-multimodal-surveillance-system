"""Unit tests for IoUTrackingService and trajectory math."""

import pytest
from src.domain.entities import DetectionResult, BoundingBox
from src.infrastructure.services.iou_tracking import (
    IoUTrackingService,
    calculate_iou,
    calculate_centroid,
    calculate_cardinal_direction
)


def test_calculate_iou():
    box1 = BoundingBox(10.0, 10.0, 50.0, 50.0)
    box2 = BoundingBox(10.0, 10.0, 50.0, 50.0)
    assert calculate_iou(box1, box2) == 1.0

    box3 = BoundingBox(100.0, 100.0, 150.0, 150.0)
    assert calculate_iou(box1, box3) == 0.0

    box4 = BoundingBox(30.0, 10.0, 70.0, 50.0)
    # Area1 = 40x40 = 1600, Area4 = 40x40 = 1600. Inter = 20x40 = 800. Union = 2400. IoU = 800/2400 = 0.3333
    assert abs(calculate_iou(box1, box4) - 0.3333) < 0.001


def test_calculate_centroid():
    box = BoundingBox(10.0, 20.0, 110.0, 120.0)
    cx, cy = calculate_centroid(box)
    assert cx == 60.0
    assert cy == 70.0


def test_calculate_cardinal_direction():
    assert calculate_cardinal_direction(0.0, 0.0, min_displacement=15.0) == "Stationary"
    assert calculate_cardinal_direction(5.0, 5.0, min_displacement=15.0) == "Stationary"
    assert calculate_cardinal_direction(100.0, 0.0, min_displacement=15.0) == "East"
    assert calculate_cardinal_direction(100.0, -100.0, min_displacement=15.0) == "North-East"
    assert calculate_cardinal_direction(0.0, -100.0, min_displacement=15.0) == "North"
    assert calculate_cardinal_direction(0.0, 100.0, min_displacement=15.0) == "South"
    assert calculate_cardinal_direction(-100.0, 0.0, min_displacement=15.0) == "West"


def test_iou_tracker_association_and_persistence():
    tracker = IoUTrackingService(iou_threshold=0.3, max_missed_frames=2, movement_pixel_threshold=15.0)

    # Frame 0: 2 detections
    det0_1 = DetectionResult(class_id=5, class_name="Tank", confidence=0.9, bbox=BoundingBox(10, 10, 50, 50))
    det0_2 = DetectionResult(class_id=6, class_name="Vehicle", confidence=0.85, bbox=BoundingBox(200, 200, 250, 250))
    active_0 = tracker.update(frame_index=0, timestamp_sec=0.0, detections=[det0_1, det0_2])

    assert len(active_0) == 2
    track_ids_0 = {t.track_id for t in active_0}
    assert track_ids_0 == {1, 2}

    # Frame 1: Tank moves slightly (dx=20, dy=0 -> displacement=20 >= 15 -> MOVING), Vehicle stays stationary
    det1_1 = DetectionResult(class_id=5, class_name="Tank", confidence=0.92, bbox=BoundingBox(30, 10, 70, 50))
    det1_2 = DetectionResult(class_id=6, class_name="Vehicle", confidence=0.87, bbox=BoundingBox(200, 200, 250, 250))
    active_1 = tracker.update(frame_index=5, timestamp_sec=0.2, detections=[det1_1, det1_2])

    assert len(active_1) == 2
    tank_track = next(t for t in active_1 if t.class_name == "Tank")
    vehicle_track = next(t for t in active_1 if t.class_name == "Vehicle")

    assert tank_track.track_id == 1 or tank_track.track_id == 2
    assert tank_track.detection_count == 2
    assert tank_track.movement_state == "MOVING"
    assert tank_track.pixel_displacement >= 15.0
    assert vehicle_track.movement_state == "STATIONARY"

    # Finish tracks
    finished = tracker.finish_tracks()
    assert len(finished) == 2
    assert finished[0].track_id == 1
    assert finished[1].track_id == 2


def test_iou_tracker_missed_frame_buffer():
    tracker = IoUTrackingService(iou_threshold=0.3, max_missed_frames=2, movement_pixel_threshold=15.0)

    # Frame 0: 1 target
    det0 = DetectionResult(class_id=4, class_name="Soldier", confidence=0.8, bbox=BoundingBox(50, 50, 80, 80))
    tracker.update(frame_index=0, timestamp_sec=0.0, detections=[det0])

    # Frame 1 & 2: Target occluded (0 detections)
    tracker.update(frame_index=5, timestamp_sec=0.2, detections=[])
    tracker.update(frame_index=10, timestamp_sec=0.4, detections=[])

    # Frame 3: Target reappears -> should re-associate with track ID 1
    det3 = DetectionResult(class_id=4, class_name="Soldier", confidence=0.85, bbox=BoundingBox(55, 52, 85, 82))
    active_3 = tracker.update(frame_index=15, timestamp_sec=0.6, detections=[det3])

    assert len(active_3) == 1
    assert active_3[0].track_id == 1
    assert active_3[0].detection_count == 2

    # Frame 4, 5, 6: Missed for 3 frames > max_missed_frames (2) -> track closes
    tracker.update(frame_index=20, timestamp_sec=0.8, detections=[])
    tracker.update(frame_index=25, timestamp_sec=1.0, detections=[])
    tracker.update(frame_index=30, timestamp_sec=1.2, detections=[])

    finished = tracker.finish_tracks()
    assert len(finished) == 1
    assert finished[0].track_id == 1
    assert finished[0].detection_count == 2
