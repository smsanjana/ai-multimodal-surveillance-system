"""YOLOv8 Detection Service implementing AbstractDetectionService."""

import os
import uuid
import logging
from typing import List, Optional
import numpy as np
import cv2

from src.domain.interfaces import AbstractDetectionService
from src.domain.entities import DetectionResult, BoundingBox
from src.core.exceptions import ModelLoadError, AnalysisProcessingError

logger = logging.getLogger("SurveillanceSystem")


class YoloDetectionService(AbstractDetectionService):
    """
    Object detection service wrapper around Ultralytics YOLOv8.
    Loads local military weights from data/models/yolov8n_kiit_mita.pt lazily as a singleton.
    """
    _model_instance = None
    _loaded_model_path = None

    DEFAULT_MILITARY_CLASSES = {
        0: "Artilary",
        1: "Missile",
        2: "Radar",
        3: "M. Rocket Launcher",
        4: "Soldier",
        5: "Tank",
        6: "Vehicle"
    }

    def __init__(self, model_path: str = "data/models/yolov8n_kiit_mita.pt", confidence_threshold: float = 0.25):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold

    def _get_model(self):
        if not os.path.exists(self.model_path):
            raise ModelLoadError(
                f"YOLOv8 weights file not found at '{self.model_path}'. "
                "Ensure local weights file exists prior to execution."
            )
        if YoloDetectionService._model_instance is None or YoloDetectionService._loaded_model_path != self.model_path:
            try:
                from ultralytics import YOLO
                logger.info("Loading YOLOv8 model lazily from %s", self.model_path)
                YoloDetectionService._model_instance = YOLO(self.model_path)
                YoloDetectionService._loaded_model_path = self.model_path
            except Exception as e:
                raise ModelLoadError(f"Failed to initialize YOLO model from '{self.model_path}': {e}")
        return YoloDetectionService._model_instance

    def detect(self, image: np.ndarray, confidence_threshold: Optional[float] = None) -> List[DetectionResult]:
        """
        Runs YOLOv8 object detection on input numpy image (RGB or BGR).

        :param image: Input image as numpy array (H, W, 3).
        :param confidence_threshold: Optional threshold override.
        :return: List of DetectionResult DTOs.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise AnalysisProcessingError("Invalid or empty numpy array provided for object detection.")

        conf = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        model = self._get_model()

        try:
            results = model(image, conf=conf, verbose=False)
        except Exception as e:
            raise AnalysisProcessingError(f"YOLO inference execution failed: {e}")

        detections: List[DetectionResult] = []
        if not results:
            return detections

        first_result = results[0]
        if first_result.boxes is None:
            return detections

        boxes = first_result.boxes
        names = first_result.names if hasattr(first_result, "names") and first_result.names else self.DEFAULT_MILITARY_CLASSES

        for box in boxes:
            try:
                xyxy = box.xyxy[0].cpu().numpy()
                conf_val = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = names.get(cls_id, self.DEFAULT_MILITARY_CLASSES.get(cls_id, str(cls_id)))

                bbox = BoundingBox(
                    x_min=float(xyxy[0]),
                    y_min=float(xyxy[1]),
                    x_max=float(xyxy[2]),
                    y_max=float(xyxy[3])
                )
                det = DetectionResult(
                    detection_id=str(uuid.uuid4()),
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=round(conf_val, 4),
                    bbox=bbox
                )
                detections.append(det)
            except Exception as e:
                logger.warning("Failed to parse box item: %s", e)

        return detections

    def draw_annotations(self, image: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """
        Draws bounding box rectangles, labels, and confidence tags on image copy.

        :param image: Input numpy array (H, W, 3).
        :param detections: List of DetectionResult items.
        :return: Annotated numpy array copy.
        """
        if image is None or image.size == 0:
            return image

        annotated = image.copy()
        
        # Consistent color map for common classes
        color_palette = [
            (0, 255, 0),    # Green
            (255, 165, 0),  # Orange
            (0, 191, 255),  # Deep Sky Blue
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
        ]

        for det in detections:
            bbox = det.bbox
            x1, y1 = int(bbox.x_min), int(bbox.y_min)
            x2, y2 = int(bbox.x_max), int(bbox.y_max)

            color_idx = abs(hash(det.class_name)) % len(color_palette)
            color = color_palette[color_idx]

            # Bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label text & background
            label = f"{det.class_name} {det.confidence * 100:.1f}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)

            # Filled label background rectangle
            cv2.rectangle(annotated, (x1, max(0, y1 - h - 6)), (x1 + w + 6, max(h + 6, y1)), color, -1)
            # Text on background
            cv2.putText(annotated, label, (x1 + 3, max(h + 3, y1 - 3)), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

        return annotated
