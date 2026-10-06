"""Deterministic IoU Multi-Object Tracking Service Module."""

import math
from typing import List, Dict, Tuple, Optional
import numpy as np

from src.domain.interfaces import AbstractTrackingService
from src.domain.entities import DetectionResult, BoundingBox, TrackRecord, TrajectoryPoint
from src.core.config import ConfigurationService


def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Calculates 2D Intersection-over-Union (IoU) ratio between two bounding boxes."""
    x_min = max(box1.x_min, box2.x_min)
    y_min = max(box1.y_min, box2.y_min)
    x_max = min(box1.x_max, box2.x_max)
    y_max = min(box1.y_max, box2.y_max)

    inter_width = max(0.0, x_max - x_min)
    inter_height = max(0.0, y_max - y_min)
    intersection = inter_width * inter_height

    area1 = max(0.0, box1.x_max - box1.x_min) * max(0.0, box1.y_max - box1.y_min)
    area2 = max(0.0, box2.x_max - box2.x_min) * max(0.0, box2.y_max - box2.y_min)
    union = area1 + area2 - intersection

    if union <= 0.0:
        return 0.0
    return round(intersection / union, 4)


def calculate_centroid(box: BoundingBox) -> Tuple[float, float]:
    """Calculates (x_center, y_center) centroid of a bounding box."""
    return (
        round((box.x_min + box.x_max) / 2.0, 2),
        round((box.y_min + box.y_max) / 2.0, 2)
    )


def calculate_cardinal_direction(dx: float, dy: float, min_displacement: float = 15.0) -> str:
    """
    Calculates cardinal trajectory direction from image-space displacement vector (dx, dy).
    Image-space axes: +x East, +y South.
    """
    distance = math.hypot(dx, dy)
    if distance < min_displacement:
        return "Stationary"

    # Math angle where +y is Up (so invert dy for image-space)
    angle_rad = math.atan2(-dy, dx)
    angle_deg = math.degrees(angle_rad) % 360.0

    # Map angle to 8 cardinal sectors
    # Sector width = 45 degrees
    sectors = ["East", "North-East", "North", "North-West", "West", "South-West", "South", "South-East"]
    idx = int(round(angle_deg / 45.0)) % 8
    return sectors[idx]


class ActiveTrack:
    """Internal helper encapsulating state of an active physical target track."""

    def __init__(self, track_id: int, detection: DetectionResult, frame_index: int, timestamp_sec: float):
        self.track_id = track_id
        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.first_frame = frame_index
        self.last_frame = frame_index
        self.first_timestamp = timestamp_sec
        self.last_timestamp = timestamp_sec
        self.detection_count = 1
        self.total_confidence = float(detection.confidence)
        self.last_bbox = detection.bbox
        self.missed_frames = 0

        cx, cy = calculate_centroid(detection.bbox)
        self.trajectory_points: List[TrajectoryPoint] = [
            TrajectoryPoint(x=cx, y=cy, frame_index=frame_index, timestamp_sec=timestamp_sec)
        ]

    def add_detection(self, detection: DetectionResult, frame_index: int, timestamp_sec: float) -> None:
        self.last_frame = frame_index
        self.last_timestamp = timestamp_sec
        self.detection_count += 1
        self.total_confidence += float(detection.confidence)
        self.last_bbox = detection.bbox
        self.missed_frames = 0

        cx, cy = calculate_centroid(detection.bbox)
        self.trajectory_points.append(
            TrajectoryPoint(x=cx, y=cy, frame_index=frame_index, timestamp_sec=timestamp_sec)
        )

    def to_track_record(self, movement_pixel_threshold: float = 15.0) -> TrackRecord:
        avg_conf = round(self.total_confidence / max(1, self.detection_count), 4)

        if len(self.trajectory_points) > 1:
            first_pt = self.trajectory_points[0]
            last_pt = self.trajectory_points[-1]
            dx = last_pt.x - first_pt.x
            dy = last_pt.y - first_pt.y
            displacement = round(math.hypot(dx, dy), 2)
            direction = calculate_cardinal_direction(dx, dy, min_displacement=movement_pixel_threshold)
        else:
            displacement = 0.0
            direction = "Stationary"

        movement_state = "MOVING" if displacement >= movement_pixel_threshold else "STATIONARY"

        return TrackRecord(
            track_id=self.track_id,
            class_id=self.class_id,
            class_name=self.class_name,
            first_frame=self.first_frame,
            last_frame=self.last_frame,
            first_timestamp=self.first_timestamp,
            last_timestamp=self.last_timestamp,
            detection_count=self.detection_count,
            avg_confidence=avg_conf,
            movement_state=movement_state,
            pixel_displacement=displacement,
            trajectory_direction=direction,
            trajectory_points=list(self.trajectory_points)
        )


class IoUTrackingService(AbstractTrackingService):
    """
    Lightweight, greedy, deterministic IoU multi-object tracking service.
    Maintains persistent track IDs, same-class priority matching, missed-frame buffer,
    and image-space centroid movement analysis.
    """

    def __init__(
        self,
        iou_threshold: float = ConfigurationService.TRACKER_IOU_THRESHOLD,
        max_missed_frames: int = ConfigurationService.TRACKER_MAX_MISSED_FRAMES,
        movement_pixel_threshold: float = ConfigurationService.MOVEMENT_PIXEL_THRESHOLD
    ):
        self.iou_threshold = float(iou_threshold)
        self.max_missed_frames = int(max_missed_frames)
        self.movement_pixel_threshold = float(movement_pixel_threshold)

        self._next_track_id = 1
        self._active_tracks: List[ActiveTrack] = []
        self._finished_tracks: List[TrackRecord] = []

    def reset(self) -> None:
        """Resets all tracking state for a new video analysis run."""
        self._next_track_id = 1
        self._active_tracks.clear()
        self._finished_tracks.clear()

    def update(
        self, frame_index: int, timestamp_sec: float, detections: List[DetectionResult]
    ) -> List[TrackRecord]:
        """
        Updates active tracks with detections from the current sampled frame.
        Sorts detections deterministically before matching.
        """
        # Sort detections deterministically by bounding box coordinates to ensure 100% reproducible matching
        sorted_detections = sorted(detections, key=lambda d: (d.bbox.x_min, d.bbox.y_min, d.bbox.x_max, d.bbox.y_max))

        unmatched_detections = list(range(len(sorted_detections)))
        unmatched_tracks = list(range(len(self._active_tracks)))

        # Build candidate matches list: (iou_val, same_class_flag, track_idx, det_idx)
        candidate_matches: List[Tuple[float, bool, int, int]] = []

        for t_idx, track in enumerate(self._active_tracks):
            for d_idx, det in enumerate(sorted_detections):
                iou_val = calculate_iou(track.last_bbox, det.bbox)
                if iou_val >= self.iou_threshold:
                    same_class = (det.class_name == track.class_name)
                    candidate_matches.append((iou_val, same_class, t_idx, d_idx))

        # Sort matches: same-class priority first, then highest IoU
        candidate_matches.sort(key=lambda item: (item[1], item[0]), reverse=True)

        matched_tracks = set()
        matched_dets = set()

        for iou_val, same_class, t_idx, d_idx in candidate_matches:
            if t_idx in matched_tracks or d_idx in matched_dets:
                continue

            matched_tracks.add(t_idx)
            matched_dets.add(d_idx)
            self._active_tracks[t_idx].add_detection(sorted_detections[d_idx], frame_index, timestamp_sec)

        # Handle unmatched active tracks (increment missed frames)
        remaining_active = []
        for t_idx, track in enumerate(self._active_tracks):
            if t_idx not in matched_tracks:
                track.missed_frames += 1
                if track.missed_frames > self.max_missed_frames:
                    # Track buffer memory exceeded -> close track
                    self._finished_tracks.append(track.to_track_record(self.movement_pixel_threshold))
                else:
                    remaining_active.append(track)
            else:
                remaining_active.append(track)

        self._active_tracks = remaining_active

        # Handle unmatched detections (spawn new track)
        for d_idx in range(len(sorted_detections)):
            if d_idx not in matched_dets:
                new_track = ActiveTrack(self._next_track_id, sorted_detections[d_idx], frame_index, timestamp_sec)
                self._next_track_id += 1
                self._active_tracks.append(new_track)

        # Return current active tracks as TrackRecord snapshots
        return [t.to_track_record(self.movement_pixel_threshold) for t in self._active_tracks]

    def finish_tracks(self) -> List[TrackRecord]:
        """Flushes remaining active tracks and returns the full complete TrackRecord list for all targets."""
        for track in self._active_tracks:
            self._finished_tracks.append(track.to_track_record(self.movement_pixel_threshold))
        self._active_tracks.clear()

        # Sort finished tracks by track_id deterministically
        result = sorted(self._finished_tracks, key=lambda t: t.track_id)
        return result
