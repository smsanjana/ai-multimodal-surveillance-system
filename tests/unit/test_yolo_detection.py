"""Unit tests for YoloDetectionService with mocked YOLO detector."""

import pytest
import os
import numpy as np
from unittest.mock import MagicMock, patch
import torch

from src.infrastructure.services.yolo_detection import YoloDetectionService
from src.domain.entities import DetectionResult, BoundingBox
from src.core.exceptions import ModelLoadError, AnalysisProcessingError


def test_yolo_detection_missing_weights():
    """T004 / T011: Raises ModelLoadError if model weights file is missing."""
    service = YoloDetectionService(model_path="data/models/non_existent_model_weights.pt")
    img_arr = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(ModelLoadError) as exc_info:
        service.detect(img_arr)
    assert "YOLOv8 weights file not found" in str(exc_info.value)


def test_yolo_detection_invalid_numpy_input():
    """T004 / T011: Raises AnalysisProcessingError on empty or invalid numpy input."""
    service = YoloDetectionService(model_path="data/models/yolov8n_kiit_mita.pt")
    with pytest.raises(AnalysisProcessingError):
        service.detect(np.array([]))
    with pytest.raises(AnalysisProcessingError):
        service.detect(None)


@patch("os.path.exists", return_value=True)
def test_yolo_detection_mocked_class_mapping(mock_exists):
    """T003 / T005: Mocked YOLO inference verifying 7 KIIT-MiTA class mapping."""
    YoloDetectionService._model_instance = None
    YoloDetectionService._loaded_model_path = None

    service = YoloDetectionService(model_path="data/models/yolov8n_kiit_mita.pt", confidence_threshold=0.25)
    img_arr = np.ones((480, 640, 3), dtype=np.uint8) * 128

    # Create mock YOLO boxes and result
    mock_box_tank = MagicMock()
    mock_box_tank.xyxy = [torch.tensor([50.0, 50.0, 200.0, 200.0])]
    mock_box_tank.conf = [torch.tensor(0.85)]
    mock_box_tank.cls = [torch.tensor(5)] # Class 5: Tank

    mock_box_missile = MagicMock()
    mock_box_missile.xyxy = [torch.tensor([300.0, 100.0, 450.0, 300.0])]
    mock_box_missile.conf = [torch.tensor(0.92)]
    mock_box_missile.cls = [torch.tensor(1)] # Class 1: Missile

    mock_result = MagicMock()
    mock_result.boxes = [mock_box_tank, mock_box_missile]
    mock_result.names = {
        0: "Artilary",
        1: "Missile",
        2: "Radar",
        3: "M. Rocket Launcher",
        4: "Soldier",
        5: "Tank",
        6: "Vehicle"
    }

    mock_model_obj = MagicMock()
    mock_model_obj.return_value = [mock_result]

    with patch("ultralytics.YOLO", return_value=mock_model_obj):
        dets = service.detect(img_arr)

    assert len(dets) == 2
    assert dets[0].class_id == 5
    assert dets[0].class_name == "Tank"
    assert dets[0].confidence == 0.85
    assert dets[0].bbox.x_min == 50.0

    assert dets[1].class_id == 1
    assert dets[1].class_name == "Missile"
    assert dets[1].confidence == 0.92


@patch("os.path.exists", return_value=True)
def test_yolo_detection_zero_detections(mock_exists):
    """T009: Verify returning empty list when zero objects meet threshold."""
    YoloDetectionService._model_instance = None
    YoloDetectionService._loaded_model_path = None

    service = YoloDetectionService(model_path="data/models/yolov8n_kiit_mita.pt", confidence_threshold=0.50)
    img_arr = np.ones((480, 640, 3), dtype=np.uint8) * 128

    mock_result = MagicMock()
    mock_result.boxes = []
    mock_result.names = {0: "Artilary", 1: "Missile", 2: "Radar", 3: "M. Rocket Launcher", 4: "Soldier", 5: "Tank", 6: "Vehicle"}

    mock_model_obj = MagicMock()
    mock_model_obj.return_value = [mock_result]

    with patch("ultralytics.YOLO", return_value=mock_model_obj):
        dets = service.detect(img_arr)

    assert isinstance(dets, list)
    assert len(dets) == 0


def test_yolo_draw_annotations():
    """T005: Verify OpenCV bounding box rendering on image array."""
    service = YoloDetectionService(model_path="data/models/yolov8n_kiit_mita.pt")
    img_arr = np.zeros((480, 640, 3), dtype=np.uint8)
    dets = [
        DetectionResult(
            detection_id="det1",
            class_id=5,
            class_name="Tank",
            confidence=0.88,
            bbox=BoundingBox(10.0, 10.0, 100.0, 100.0)
        )
    ]
    annotated = service.draw_annotations(img_arr, dets)
    assert annotated is not None
    assert annotated.shape == (480, 640, 3)
    # Check that image pixels were modified by drawing bounding box
    assert not np.array_equal(annotated, img_arr)
