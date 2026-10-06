"""Dependency Injection Container Module."""

from typing import Any, Dict, Optional, Type
from src.core.config import ConfigurationService
from src.core.database import DatabaseService
from src.core.logger import setup_logger
from src.infrastructure.database.repositories import (
    AnalysisRepository,
    AlertRepository,
    ReportRepository,
    SettingsRepository,
    seed_database_if_empty
)
from src.infrastructure.services.yolo_detection import YoloDetectionService
from src.infrastructure.services.threat_scoring import ThreatScoringService
from src.infrastructure.services.explainability import ExplainabilityService
from src.infrastructure.services.demo_manager import DemoManager
from src.application.image_surveillance_service import ImageSurveillanceService



class DIContainer:
    """Central Dependency Injection Container singleton."""

    _instance: Optional["DIContainer"] = None
    _services: Dict[Type, Any] = {}

    def __new__(cls) -> "DIContainer":
        if cls._instance is None:
            cls._instance = super(DIContainer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initializes core services and repositories."""
        # 1. Config Service
        config_service = ConfigurationService()
        self._services[ConfigurationService] = config_service

        # 2. Logger
        log_level = config_service.get("logging.level", "INFO")
        log_file = config_service.get("logging.log_file", "logs/surveillance.log")
        logger = setup_logger(log_level=log_level, log_file=log_file)
        self._services["logger"] = logger

        # 3. Database Service
        db_path = config_service.get("database.db_path", "data/surveillance.db")
        db_service = DatabaseService(db_path=db_path)
        self._services[DatabaseService] = db_service

        # 4. Repositories
        analysis_repo = AnalysisRepository(db_service)
        alert_repo = AlertRepository(db_service)
        report_repo = ReportRepository(db_service)
        settings_repo = SettingsRepository(db_service)

        self._services[AnalysisRepository] = analysis_repo
        self._services[AlertRepository] = alert_repo
        self._services[ReportRepository] = report_repo
        self._services[SettingsRepository] = settings_repo

        # 5. Feature 002 / 003 AI Services & Demo Manager
        model_path = config_service.get("ai.model_path", ConfigurationService.YOLO_MODEL_PATH)
        conf_thresh = float(config_service.get("ai.confidence_threshold", ConfigurationService.YOLO_CONFIDENCE_THRESHOLD))

        demo_manager = DemoManager()
        yolo_service = YoloDetectionService(model_path=model_path, confidence_threshold=conf_thresh)
        threat_service = ThreatScoringService()
        explainability_service = ExplainabilityService()

        image_surveillance_service = ImageSurveillanceService(
            detection_service=yolo_service,
            threat_scoring_service=threat_service,
            explainability_service=explainability_service,
            analysis_repository=analysis_repo,
            demo_manager=demo_manager
        )

        from src.infrastructure.services.video_processing import VideoProcessingService
        from src.infrastructure.services.iou_tracking import IoUTrackingService
        from src.application.video_surveillance_service import VideoSurveillanceService

        video_proc_service = VideoProcessingService(
            max_duration_sec=float(config_service.get("video.max_duration_seconds", ConfigurationService.MAX_VIDEO_DURATION_SECONDS))
        )
        iou_tracking_service = IoUTrackingService(
            iou_threshold=float(config_service.get("video.tracker_iou_threshold", ConfigurationService.TRACKER_IOU_THRESHOLD)),
            max_missed_frames=int(config_service.get("video.tracker_max_missed_frames", ConfigurationService.TRACKER_MAX_MISSED_FRAMES)),
            movement_pixel_threshold=float(config_service.get("video.movement_pixel_threshold", ConfigurationService.MOVEMENT_PIXEL_THRESHOLD))
        )
        from src.infrastructure.database.repositories import AnalystReviewRepository
        from src.infrastructure.services.spatial_zone_evaluator import SpatialZoneEvaluator
        from src.application.contextual_assessment_service import ContextualAssessmentService
        from src.application.analyst_review_service import AnalystReviewService

        spatial_zone_evaluator = SpatialZoneEvaluator()
        video_surveillance_service = VideoSurveillanceService(
            video_processing_service=video_proc_service,
            detection_service=yolo_service,
            tracking_service=iou_tracking_service,
            threat_scoring_service=threat_service,
            explainability_service=explainability_service,
            analysis_repository=analysis_repo,
            demo_manager=demo_manager,
            spatial_zone_evaluator=spatial_zone_evaluator
        )

        analyst_review_repo = AnalystReviewRepository(db_service)
        contextual_assessment_service = ContextualAssessmentService(zone_evaluator=spatial_zone_evaluator)
        default_analyst_id = str(config_service.get("analyst.default_id", ConfigurationService.DEFAULT_ANALYST_ID))
        analyst_review_service = AnalystReviewService(review_repository=analyst_review_repo, default_analyst_id=default_analyst_id)

        self._services[DemoManager] = demo_manager
        self._services[YoloDetectionService] = yolo_service
        self._services[ThreatScoringService] = threat_service
        self._services[ExplainabilityService] = explainability_service
        self._services[ImageSurveillanceService] = image_surveillance_service
        self._services[VideoProcessingService] = video_proc_service
        self._services[IoUTrackingService] = iou_tracking_service
        self._services[VideoSurveillanceService] = video_surveillance_service
        self._services[AnalystReviewRepository] = analyst_review_repo
        self._services[SpatialZoneEvaluator] = spatial_zone_evaluator
        self._services[ContextualAssessmentService] = contextual_assessment_service
        self._services[AnalystReviewService] = analyst_review_service

        # 7. Startup Database Seeding
        seed_database_if_empty(db_service)


    def resolve(self, service_cls: Type[Any]) -> Any:
        """Resolves a registered service instance by class type or string key."""
        if service_cls in self._services:
            return self._services[service_cls]
        raise KeyError(f"Service '{service_cls}' is not registered in the DIContainer.")

    @classmethod
    def reset(cls) -> None:
        """Resets container instance (useful for testing)."""
        cls._instance = None
        cls._services = {}
