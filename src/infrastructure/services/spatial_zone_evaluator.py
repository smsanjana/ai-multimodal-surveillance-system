"""Spatial Zone Evaluator module for normalized point-in-polygon geometry math."""

from typing import List, Tuple, Optional
import numpy as np
import cv2
from src.domain.interfaces import ISpatialZoneEvaluator
from src.domain.entities import RestrictedZone


class SpatialZoneEvaluator(ISpatialZoneEvaluator):
    """
    Evaluates normalized image-space geometric polygon coordinates ([0.0, 1.0] scale)
    against target object centroids using OpenCV point-in-polygon geometry.
    """

    def convert_normalized_polygon_to_pixels(
        self, polygon_norm: List[Tuple[float, float]], width: int, height: int
    ) -> List[Tuple[int, int]]:
        """
        Converts normalized float polygon vertices in range [0.0, 1.0] to frame pixel coordinates.
        Origin (0.0, 0.0) is top-left corner, +X extends right, +Y extends down.
        """
        if not polygon_norm or len(polygon_norm) < 3:
            return []
        
        pixel_pts = []
        for x, y in polygon_norm:
            px = max(0, min(width, int(round(x * width))))
            py = max(0, min(height, int(round(y * height))))
            pixel_pts.append((px, py))
        return pixel_pts

    def is_centroid_in_zone(
        self,
        centroid_norm: Tuple[float, float],
        zone: RestrictedZone,
        width: int = 1280,
        height: int = 720
    ) -> bool:
        """
        Evaluates whether a normalized centroid (x, y) intersects a restricted zone.
        Points lying on the polygon boundary edge are evaluated as inside the zone (cv2.pointPolygonTest >= 0).
        """
        if not zone or not zone.is_active or not zone.polygon_points or len(zone.polygon_points) < 3:
            return False

        cx, cy = centroid_norm
        if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
            # Convert if provided in raw pixel format
            cx = max(0.0, min(1.0, cx / float(width)))
            cy = max(0.0, min(1.0, cy / float(height)))

        px = int(round(cx * width))
        py = int(round(cy * height))

        pixel_polygon = self.convert_normalized_polygon_to_pixels(zone.polygon_points, width, height)
        if len(pixel_polygon) < 3:
            return False

        pts_array = np.array(pixel_polygon, dtype=np.int32)
        dist = cv2.pointPolygonTest(pts_array, (float(px), float(py)), measureDist=False)
        return dist >= 0

    def evaluate_track_spatial_events(
        self,
        track: 'TrackRecord',
        zones: List[RestrictedZone],
        width: int = 1280,
        height: int = 720
    ) -> List['ObservableEvent']:
        """
        Evaluates a track's trajectory points across active normalized restricted zones [0.0, 1.0],
        detecting state transitions (NO_EVENT, ZONE_ENTRY, ZONE_EXIT, BOUNDARY_CROSSING, etc.)
        and generating granular evidence records.
        """
        from src.domain.entities import ObservableEvent
        events: List[ObservableEvent] = []
        if not track or not track.trajectory_points or not zones:
            return events

        active_zones = [z for z in zones if z and z.is_active and z.polygon_points and len(z.polygon_points) >= 3]
        if not active_zones:
            return events

        for zone in active_zones:
            prev_inside = False
            prev_pt = None

            for i, pt in enumerate(track.trajectory_points):
                norm_cx = pt.x / float(width) if pt.x > 1.0 else pt.x
                norm_cy = pt.y / float(height) if pt.y > 1.0 else pt.y

                curr_inside = self.is_centroid_in_zone((norm_cx, norm_cy), zone, width=width, height=height)

                if i == 0:
                    prev_inside = curr_inside
                    prev_pt = pt
                    if curr_inside:
                        event_type = "STATIONARY_OBJECT_IN_ZONE" if track.movement_state.upper() == "STATIONARY" else "ZONE_TRANSIT"
                        events.append(ObservableEvent(
                            track_id=track.track_id,
                            class_name=track.class_name,
                            event_type=event_type,
                            timestamp_sec=pt.timestamp_sec,
                            frame_index=pt.frame_index,
                            zone_id=zone.zone_id,
                            prev_centroid=(round(norm_cx, 4), round(norm_cy, 4)),
                            curr_centroid=(round(norm_cx, 4), round(norm_cy, 4)),
                            prev_inside=curr_inside,
                            curr_inside=curr_inside,
                            is_dynamic_evidence=True,
                            description=f"Track #{track.track_id} ({track.class_name}) initial centroid observed inside restricted zone '{zone.name}' (ID: {zone.zone_id}).",
                            confidence_score=track.avg_confidence
                        ))
                    continue

                prev_norm_x = prev_pt.x / float(width) if prev_pt.x > 1.0 else prev_pt.x
                prev_norm_y = prev_pt.y / float(height) if prev_pt.y > 1.0 else prev_pt.y

                event_type = None
                desc = ""

                if not prev_inside and curr_inside:
                    event_type = "ZONE_ENTRY"
                    desc = f"Track #{track.track_id} ({track.class_name}) entered restricted zone '{zone.name}' (ID: {zone.zone_id}) crossing boundary at t={pt.timestamp_sec:.2f}s."
                elif prev_inside and not curr_inside:
                    event_type = "ZONE_EXIT"
                    desc = f"Track #{track.track_id} ({track.class_name}) exited restricted zone '{zone.name}' (ID: {zone.zone_id}) crossing boundary at t={pt.timestamp_sec:.2f}s."
                elif prev_inside and curr_inside:
                    event_type = "STATIONARY_OBJECT_IN_ZONE" if track.movement_state.upper() == "STATIONARY" else "ZONE_TRANSIT"
                    desc = f"Track #{track.track_id} ({track.class_name}) continuing transit inside restricted zone '{zone.name}' (ID: {zone.zone_id})."

                if event_type:
                    events.append(ObservableEvent(
                        track_id=track.track_id,
                        class_name=track.class_name,
                        event_type=event_type,
                        timestamp_sec=pt.timestamp_sec,
                        frame_index=pt.frame_index,
                        zone_id=zone.zone_id,
                        prev_centroid=(round(prev_norm_x, 4), round(prev_norm_y, 4)),
                        curr_centroid=(round(norm_cx, 4), round(norm_cy, 4)),
                        prev_inside=prev_inside,
                        curr_inside=curr_inside,
                        is_dynamic_evidence=True,
                        description=desc,
                        confidence_score=track.avg_confidence
                    ))

                prev_inside = curr_inside
                prev_pt = pt

        return events
