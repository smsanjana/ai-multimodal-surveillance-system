"""Domain entity dataclasses for the AI Surveillance Command Center."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import uuid


@dataclass
class AnalysisRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_type: str = "DEMO"       # DEMO, UPLOAD, LIVE
    platform: str = "DRONE"          # DRONE, CCTV
    media_type: str = "IMAGE"        # IMAGE, VIDEO
    scenario_name: Optional[str] = None
    threat_score: float = 0.0        # 0.0 - 100.0
    threat_level: str = "LOW"        # LOW, MEDIUM, HIGH, CRITICAL
    confidence_avg: float = 0.85
    processing_time_ms: float = 120.0
    status: str = "COMPLETED"        # COMPLETED, PENDING, FAILED
    artifact_path: Optional[str] = None


@dataclass
class DetectionRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    class_name: str = "person"
    confidence: float = 0.90
    bbox_json: str = '{"x_min": 0.1, "y_min": 0.1, "x_max": 0.5, "y_max": 0.5}'
    frame_index: Optional[int] = None


@dataclass
class ThreatAssessmentRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    score: float = 0.0
    level: str = "LOW"
    xai_reason: str = "Normal activity detected."
    recommended_sop: str = "Continue routine monitoring."


@dataclass
class AlertRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    severity: str = "LOW"           # LOW, MEDIUM, HIGH, CRITICAL
    reason: str = "Perimeter clear."
    status: str = "UNACKNOWLEDGED"  # UNACKNOWLEDGED, ACKNOWLEDGED, RESOLVED
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ReportRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    file_path: str = "reports/incident_summary.pdf"
    report_type: str = "INCIDENT_SUMMARY"  # INCIDENT_SUMMARY, DAILY_AUDIT, FULL_EXPORT
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SystemSettings:
    key: str
    value: str
    category: str  # AI, VIDEO, THREAT, CAMERA, SYSTEM


# --- Feature 002 DTOs & Value Objects ---

@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class DetectionResult:
    detection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    class_id: int = 0
    class_name: str = "person"
    confidence: float = 0.0
    bbox: BoundingBox = field(default_factory=lambda: BoundingBox(0.0, 0.0, 0.0, 0.0))


@dataclass
class FactorContribution:
    factor_name: str
    score_delta: float
    description: str


@dataclass
class ThreatAssessmentResult:
    threat_score: float = 0.0
    threat_level: str = "LOW"
    factors: List[FactorContribution] = field(default_factory=list)
    xai_reason: str = ""
    recommended_sop: str = ""


@dataclass
class ImageAnalysisRequest:
    source_type: str = "DEMO"             # "UPLOAD" or "DEMO"
    platform: str = "DRONE"                # "DRONE" or "CCTV"
    scenario_name: Optional[str] = None
    image_bytes: Optional[bytes] = None
    image_path: Optional[str] = None
    zone_violation_flag: bool = False
    unauthorized_access_signal: bool = False


@dataclass
class ImageAnalysisResponse:
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_type: str = "DEMO"
    platform: str = "DRONE"
    scenario_name: Optional[str] = None
    original_image_bytes: bytes = b""
    annotated_image_bytes: bytes = b""
    detections: List[DetectionResult] = field(default_factory=list)
    threat_assessment: ThreatAssessmentResult = field(default_factory=ThreatAssessmentResult)
    processing_time_ms: float = 0.0
    persisted: bool = True


# --- Feature 004 Video DTOs & Value Objects ---

@dataclass
class VideoMetadata:
    file_path: str
    duration_seconds: float
    fps: float
    total_frames: int
    sampled_frames: int
    width: int
    height: int


@dataclass
class TrajectoryPoint:
    x: float
    y: float
    frame_index: int
    timestamp_sec: float


@dataclass
class TrackRecord:
    track_id: int
    class_id: int
    class_name: str
    first_frame: int
    last_frame: int
    first_timestamp: float
    last_timestamp: float
    detection_count: int
    avg_confidence: float
    movement_state: str                # 'STATIONARY' or 'MOVING'
    pixel_displacement: float          # Centroid Euclidean distance across observed frames
    trajectory_direction: str          # Cardinal direction e.g., 'North-East', 'South', 'Stationary'
    trajectory_points: List[TrajectoryPoint] = field(default_factory=list)


@dataclass
class VideoAnalysisRequest:
    source_type: str = "DEMO"           # "UPLOAD" or "DEMO"
    platform: str = "DRONE"              # "DRONE" or "CCTV"
    scenario_name: Optional[str] = None
    video_path: Optional[str] = None
    video_bytes: Optional[bytes] = None
    target_sample_fps: float = 5.0
    zone_violation_flag: bool = False
    unauthorized_access_signal: bool = False
    zones: Optional[List['RestrictedZone']] = None


@dataclass
class VideoAnalysisResult:
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_type: str = "DEMO"
    platform: str = "DRONE"
    scenario_name: Optional[str] = None
    video_metadata: Optional[VideoMetadata] = None
    tracks: List[TrackRecord] = field(default_factory=list)
    total_detections: int = 0
    class_counts: Dict[str, int] = field(default_factory=dict)
    threat_assessment: ThreatAssessmentResult = field(default_factory=ThreatAssessmentResult)
    events: List['ObservableEvent'] = field(default_factory=list)
    representative_frame_bytes: List[bytes] = field(default_factory=list)
    annotated_video_path: Optional[str] = None
    processing_time_ms: float = 0.0
    persisted: bool = True


# --- Feature 005: Contextual Assessment & Analyst Review Domain Entities ---

@dataclass
class RestrictedZone:
    zone_id: str
    name: str
    platform: str                        # "DRONE" or "CCTV"
    camera_id: Optional[str] = None
    polygon_points: List[Tuple[float, float]] = field(default_factory=list)  # [(x1, y1), ...] in normalized [0.0, 1.0] scale
    is_active: bool = True


@dataclass
class ObservableEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    track_id: int = 0
    class_name: str = "Unknown"
    event_type: str = "ROUTINE_TRANSIT"  # "NO_EVENT", "ZONE_ENTRY", "ZONE_EXIT", "BOUNDARY_CROSSING", "ZONE_TRANSIT", "STATIONARY_OBJECT_IN_ZONE"
    timestamp_sec: float = 0.0
    frame_index: Optional[int] = None
    zone_id: Optional[str] = None
    prev_centroid: Optional[Tuple[float, float]] = None
    curr_centroid: Optional[Tuple[float, float]] = None
    prev_inside: bool = False
    curr_inside: bool = False
    is_dynamic_evidence: bool = True
    description: str = ""
    confidence_score: float = 0.0
    is_uncertain: bool = False


@dataclass
class SeparateContextualAssessment:
    analysis_id: str
    spatial_threat_score: float = 0.0
    spatial_threat_level: str = "LOW"
    computed_spatial_breach: bool = False
    scenario_metadata_signal: bool = False
    events: List[ObservableEvent] = field(default_factory=list)
    xai_reason: str = ""
    recommended_sop: str = ""


@dataclass
class AnalystReviewRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    review_status: str = "PENDING_REVIEW"  # "PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"
    analyst_id: str = "OPERATOR_01"
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AnalystReviewHistoryRecord:
    history_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    review_id: str = ""
    analysis_id: str = ""
    from_status: str = "PENDING_REVIEW"
    to_status: str = "ACKNOWLEDGED"
    analyst_id: str = "OPERATOR_01"
    notes: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())



