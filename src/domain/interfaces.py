"""Domain interface abstractions and contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.domain.entities import (
    AnalysisRecord, AlertRecord, ReportRecord, SystemSettings,
    DetectionResult, ThreatAssessmentResult, DetectionRecord,
    VideoMetadata, TrackRecord, VideoAnalysisRequest, VideoAnalysisResult
)
from typing import Generator, Tuple, Union
import numpy as np


class IConfigurationService(ABC):
    @abstractmethod
    def get(self, key_path: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def reload(self) -> None:
        pass


class IDatabaseService(ABC):
    @abstractmethod
    def initialize_database(self) -> None:
        pass

    @abstractmethod
    def seed_initial_data(self) -> None:
        pass


class IAnalysisRepository(ABC):
    @abstractmethod
    def get_all(self, platform: Optional[str] = None, threat_level: Optional[str] = None) -> List[AnalysisRecord]:
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> Optional[AnalysisRecord]:
        pass

    @abstractmethod
    def save(self, record: AnalysisRecord) -> AnalysisRecord:
        pass

    @abstractmethod
    def save_analysis_with_detections(
        self, record: AnalysisRecord, detections: List[DetectionRecord], threat_assessment: Optional[Dict[str, Any]] = None
    ) -> AnalysisRecord:
        pass


class AbstractDetectionService(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.25) -> List[DetectionResult]:
        pass

    @abstractmethod
    def draw_annotations(self, image: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        pass


class AbstractThreatScoringService(ABC):
    @abstractmethod
    def evaluate_threat(
        self, detections: List[DetectionResult], metadata: Dict[str, Any]
    ) -> ThreatAssessmentResult:
        pass


class AbstractExplainabilityService(ABC):
    @abstractmethod
    def explain(
        self, threat_score: float, threat_level: str, detections: List[DetectionResult], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass


class AbstractVideoProcessingService(ABC):
    @abstractmethod
    def validate_video(self, video_path: str) -> VideoMetadata:
        pass

    @abstractmethod
    def extract_sampled_frames(
        self, video_path: str, target_fps: float = 5.0
    ) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        pass

    @abstractmethod
    def save_temp_upload(self, video_bytes: bytes, filename: str) -> str:
        pass


class AbstractTrackingService(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def update(
        self, frame_index: int, timestamp_sec: float, detections: List[DetectionResult]
    ) -> List[TrackRecord]:
        pass

    @abstractmethod
    def finish_tracks(self) -> List[TrackRecord]:
        pass


class IVideoSurveillanceService(ABC):
    @abstractmethod
    def process_video_analysis(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        pass

    @abstractmethod
    def process_video(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        pass


class IAlertRepository(ABC):
    @abstractmethod
    def get_all(self, status: Optional[str] = None) -> List[AlertRecord]:
        pass

    @abstractmethod
    def save(self, alert: AlertRecord) -> AlertRecord:
        pass


class IReportRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[ReportRecord]:
        pass

    @abstractmethod
    def save(self, report: ReportRecord) -> ReportRecord:
        pass


class ISettingsRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[SystemSettings]:
        pass

    @abstractmethod
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str, category: str = "SYSTEM") -> None:
        pass


class IDIContainer(ABC):
    @abstractmethod
    def resolve(self, service_cls: type) -> Any:
        pass


# --- Feature 005: Contextual Assessment & Analyst Review Interfaces ---

class ISpatialZoneEvaluator(ABC):
    @abstractmethod
    def convert_normalized_polygon_to_pixels(
        self, polygon_norm: List[Tuple[float, float]], width: int, height: int
    ) -> List[Tuple[int, int]]:
        pass

    @abstractmethod
    def is_centroid_in_zone(
        self, centroid_norm: Tuple[float, float], zone: Any
    ) -> bool:
        pass


class IContextualAssessmentService(ABC):
    @abstractmethod
    def evaluate_spatial_context(
        self,
        analysis_id: str,
        detections: List[DetectionResult],
        tracks: List[TrackRecord],
        platform: str,
        zones: Optional[List[Any]] = None,
        scenario_metadata_signal: bool = False
    ) -> Any:
        pass


class IAnalystReviewRepository(ABC):
    @abstractmethod
    def save_review(
        self, review: Any, history_entry: Any
    ) -> Any:
        pass

    @abstractmethod
    def get_review_by_analysis_id(self, analysis_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    def get_review_history(self, review_id: str) -> List[Any]:
        pass


class IAnalystReviewService(ABC):
    @abstractmethod
    def submit_review(
        self,
        analysis_id: str,
        review_status: str,
        analyst_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Any:
        pass



