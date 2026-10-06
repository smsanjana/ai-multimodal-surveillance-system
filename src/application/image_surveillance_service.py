"""Image Surveillance Service application use case orchestrator."""

import io
import json
import time
import uuid
from datetime import datetime
from typing import Optional
import numpy as np
import cv2
from PIL import Image

from src.domain.entities import (
    ImageAnalysisRequest, ImageAnalysisResponse, AnalysisRecord,
    DetectionRecord, ThreatAssessmentResult
)
from src.domain.interfaces import (
    AbstractDetectionService, AbstractThreatScoringService,
    AbstractExplainabilityService, IAnalysisRepository
)
from src.infrastructure.services.image_validator import ImageValidator
from src.infrastructure.services.demo_manager import DemoManager
from src.core.exceptions import AnalysisProcessingError, ImageValidationError
from src.core.logger import setup_logger

logger = setup_logger()


class ImageSurveillanceService:
    """
    Application use case orchestrator for single-image surveillance analysis.
    Decouples UI deck from backend computer vision detection, threat scoring, XAI, and persistence.
    """

    def __init__(
        self,
        detection_service: AbstractDetectionService,
        threat_scoring_service: AbstractThreatScoringService,
        explainability_service: AbstractExplainabilityService,
        analysis_repository: IAnalysisRepository,
        demo_manager: DemoManager
    ):
        self.detection_service = detection_service
        self.threat_scoring_service = threat_scoring_service
        self.explainability_service = explainability_service
        self.analysis_repository = analysis_repository
        self.demo_manager = demo_manager

    def process_image(self, request: ImageAnalysisRequest) -> ImageAnalysisResponse:
        """
        Orchestrates full image analysis workflow:
        1. Validate input media
        2. Convert to numpy RGB frame
        3. Execute object detection
        4. Render bounding box annotations
        5. Calculate multi-factor threat score & classification
        6. Build Explainable AI (XAI) rationale and SOP decision support
        7. Automatically persist results to SQLite database
        8. Return structured ImageAnalysisResponse DTO.
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        timestamp_str = datetime.utcnow().isoformat()

        # Step 1: Input Media Extraction & Validation
        image_bytes: bytes
        scenario_name: Optional[str] = request.scenario_name

        if request.source_type.upper() == "DEMO":
            if not scenario_name:
                scenario_name = "Drone Normal Patrol" if request.platform.upper() == "DRONE" else "CCTV Entrance Patrol"
            image_bytes = self.demo_manager.load_demo_image_bytes(scenario_name)
        else:  # UPLOAD
            if request.image_bytes:
                image_bytes = request.image_bytes
            elif request.image_path:
                with open(request.image_path, "rb") as f:
                    image_bytes = f.read()
            else:
                raise ImageValidationError("No image bytes or file path provided for uploaded image.")

        # Validate image bytes
        validated_bytes, (width, height) = ImageValidator.validate_image(image_bytes)

        # Step 2: Convert bytes to BGR numpy array for OpenCV/YOLO
        try:
            np_arr = np.frombuffer(validated_bytes, np.uint8)
            np_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if np_bgr is None or np_bgr.size == 0:
                raise AnalysisProcessingError("Failed to decode image bytes into OpenCV frame.")
        except Exception as e:
            raise AnalysisProcessingError(f"Failed to decode image bytes into numpy array: {e}")

        # Step 3: Run Object Detection
        detections = self.detection_service.detect(np_bgr)

        # Step 4: Render Bounding Box Annotations onto BGR image
        annotated_bgr = self.detection_service.draw_annotations(np_bgr, detections)

        # Convert BGR annotated image to RGB for PIL JPEG encoding
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        annotated_pil = Image.fromarray(annotated_rgb)
        annotated_buffer = io.BytesIO()
        annotated_pil.save(annotated_buffer, format="JPEG")
        annotated_bytes = annotated_buffer.getvalue()

        # Step 5: Threat Evaluation
        zone_flag = request.zone_violation_flag
        unauth_signal = getattr(request, "unauthorized_access_signal", False)

        if request.source_type.upper() == "DEMO" and scenario_name:
            scen_info = self.demo_manager.get_scenario(scenario_name)
            if scen_info:
                if not zone_flag:
                    zone_flag = scen_info.get("zone_violation_flag", False)
                if not unauth_signal:
                    unauth_signal = scen_info.get("unauthorized_access_signal", False)

        metadata = {
            "platform": request.platform,
            "source_type": request.source_type,
            "scenario_name": scenario_name or "",
            "zone_violation_flag": zone_flag,
            "unauthorized_access_signal": unauth_signal,
            "width": width,
            "height": height
        }
        threat_assessment = self.threat_scoring_service.evaluate_threat(detections, metadata)

        # Step 6: Explainable AI & SOP Decision Support
        xai_info = self.explainability_service.explain(
            threat_score=threat_assessment.threat_score,
            threat_level=threat_assessment.threat_level,
            detections=detections,
            metadata=metadata
        )
        threat_assessment.xai_reason = xai_info.get("xai_reason", "")
        threat_assessment.recommended_sop = xai_info.get("recommended_sop", "")

        # Calculate latency
        processing_time_ms = round((time.time() - start_time) * 1000.0, 2)
        avg_confidence = round(
            sum(d.confidence for d in detections) / len(detections), 4
        ) if detections else 0.0

        # Step 7: Automatic SQLite Persistence
        analysis_rec = AnalysisRecord(
            id=analysis_id,
            timestamp=timestamp_str,
            source_type=request.source_type,
            platform=request.platform,
            media_type="IMAGE",
            scenario_name=scenario_name,
            threat_score=threat_assessment.threat_score,
            threat_level=threat_assessment.threat_level,
            confidence_avg=avg_confidence,
            processing_time_ms=processing_time_ms,
            status="COMPLETED",
            artifact_path=None
        )

        detection_records = [
            DetectionRecord(
                id=d.detection_id,
                analysis_id=analysis_id,
                class_name=d.class_name,
                confidence=d.confidence,
                bbox_json=json.dumps({
                    "x_min": d.bbox.x_min,
                    "y_min": d.bbox.y_min,
                    "x_max": d.bbox.x_max,
                    "y_max": d.bbox.y_max
                })
            )
            for d in detections
        ]

        try:
            self.analysis_repository.save_analysis_with_detections(analysis_rec, detection_records)
            logger.info("Successfully persisted analysis run %s (Threat: %s)", analysis_id, threat_assessment.threat_level)
        except Exception as e:
            logger.error("Failed to persist analysis run to database: %s", e)

        # Step 8: Return structured response
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=timestamp_str,
            source_type=request.source_type,
            platform=request.platform,
            scenario_name=scenario_name,
            original_image_bytes=validated_bytes,
            annotated_image_bytes=annotated_bytes,
            detections=detections,
            threat_assessment=threat_assessment,
            processing_time_ms=processing_time_ms,
            persisted=True
        )
