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
