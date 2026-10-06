"""Integration test using the real fine-tuned KIIT-MiTA YOLO model on a deterministic military drone image."""

import os
import pytest
import numpy as np
import cv2

from src.core.config import ConfigurationService
from src.core.di_container import DIContainer
from src.infrastructure.services.yolo_detection import YoloDetectionService
from src.application.image_surveillance_service import ImageSurveillanceService
from src.infrastructure.database.repositories import AnalysisRepository
from src.domain.entities import ImageAnalysisRequest


def test_real_kiit_mita_model_integration_on_military_drone_image():
    """
    T014: Real model integration test loading actual data/models/yolov8n_kiit_mita.pt weights
    and processing one deterministic built-in KIIT-MiTA military drone image.
    Verifies real YOLO inference, structured target detections, dual image output, and SQLite persistence.
    """
    model_path = ConfigurationService.YOLO_MODEL_PATH
    assert os.path.exists(model_path), f"Required model file not found at '{model_path}'"

    # Reset container to ensure real configured YoloDetectionService is initialized
    DIContainer.reset()
    container = DIContainer()
    service: ImageSurveillanceService = container.resolve(ImageSurveillanceService)
    analysis_repo: AnalysisRepository = container.resolve(AnalysisRepository)

    # Use deterministic military drone image path
    military_image_path = "data/demo/drone/images/image_s3r2_kiit_1607.jpeg"
    if not os.path.exists(military_image_path):
        military_image_path = "data/demo/drone/images/drone_restricted_area.jpg"
    assert os.path.exists(military_image_path), f"Deterministic test image not found at '{military_image_path}'"

    with open(military_image_path, "rb") as f:
        img_bytes = f.read()

    req = ImageAnalysisRequest(
        source_type="UPLOAD",
        platform="DRONE",
        scenario_name="Military Drone Field Reconnaissance",
        image_bytes=img_bytes
    )

    resp = service.process_image(req)

    # Verify structured response and real inference outputs
    assert resp.analysis_id is not None
    assert resp.source_type == "UPLOAD"
    assert resp.platform == "DRONE"
    assert resp.original_image_bytes is not None and len(resp.original_image_bytes) > 0
    assert resp.annotated_image_bytes is not None and len(resp.annotated_image_bytes) > 0
    assert resp.threat_assessment.threat_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # Verify detections container structure
    assert isinstance(resp.detections, list)
    for det in resp.detections:
        assert det.class_id in range(7)
        assert det.class_name in ("Artilary", "Missile", "Radar", "M. Rocket Launcher", "Soldier", "Tank", "Vehicle")
        assert 0.0 <= det.confidence <= 1.0
        assert det.bbox is not None

    # Verify SQLite database persistence
    persisted_record = analysis_repo.get_by_id(resp.analysis_id)
    assert persisted_record is not None
    assert persisted_record.id == resp.analysis_id
    assert persisted_record.threat_level == resp.threat_assessment.threat_level
