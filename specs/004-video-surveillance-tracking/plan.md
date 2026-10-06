# Implementation Plan: Feature 004 - Video Surveillance & Object Tracking

**Branch**: `004-video-surveillance-tracking` | **Date**: 2026-09-13 | **Spec**: [specs/004-video-surveillance-tracking/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/004-video-surveillance-tracking/spec.md)

---

## Executive Summary

Feature 004 extends the AI Surveillance Command Center from single-image analysis to temporal video surveillance processing and multi-object tracking. The system ingests video inputs from built-in offline military demo assets or user-uploaded media files (`.mp4`, `.avi`, `.mov`), extracts video metadata, calculates deterministic frame sampling targeting approximately 5 processed frames per second (`VIDEO_TARGET_SAMPLE_FPS = 5`), runs frame detections through the existing fine-tuned KIIT-MiTA military YOLO model (`data/models/yolov8n_kiit_mita.pt`), tracks detected military entities across frames using a lightweight deterministic IoU-based tracker, evaluates image-space centroid movement (stationary vs. moving classification, pixel displacement, trajectory vector), assesses threat levels while maintaining strict Feature 003 threat engine neutrality, renders representative annotated video frames, and persists structured video analysis records to SQLite storage without breaking existing image records.

---

## Technical Context & Architecture Principles

- **Language/Version**: Python 3.11
- **Primary Dependencies**: OpenCV (`cv2`), Ultralytics YOLOv8, PyYAML, NumPy, Streamlit, Plotly, Pytest
- **Storage**: SQLite (`data/surveillance.db`) via `DatabaseService` and `AnalysisRepository`
- **Testing**: `pytest` (unit & integration test suites under `tests/unit` and `tests/integration`)
- **Target Platform**: macOS / Linux CPU offline execution
- **Project Type**: Desktop Command Center Web UI built with Streamlit adhering to Clean Architecture
- **Performance Goals**: Total video processing latency < 30 seconds for standard 60-second video clips at 5 FPS sampling rate on standard CPU hardware
- **Constraints**: 100% offline, zero network API calls, strict threat scoring neutrality (Feature 003 threat engine unchanged), Clean Architecture compliance, no live camera streaming or polygon geofencing

---

## Constitution & Architecture Compliance Checklist

- [x] **Modular Development & Clean Architecture**: Code strictly partitioned into Presentation (`ui/`), Application (`application/`), Domain (`domain/`), and Infrastructure (`infrastructure/`).
- [x] **UI Independence**: Video ingestion, frame extraction, IoU multi-object tracking, trajectory math, and persistence execute headlessly in Application/Infrastructure layers. Streamlit scripts (`ui/pages/surveillance.py`) only capture user selections and display DTO results.
- [x] **Reuse Core Services**: Reuses existing `ConfigurationService`, `DIContainer`, `DatabaseService`, `AnalysisRepository`, `DemoManager`, `YoloDetectionService`, `ThreatScoringService`, and `ExplainabilityService`.
- [x] **No Hardcoded Parameters**: `VIDEO_TARGET_SAMPLE_FPS = 5`, `MAX_VIDEO_DURATION_SECONDS = 120`, `TRACKER_IOU_THRESHOLD = 0.3`, `TRACKER_MAX_MISSED_FRAMES = 2`, `MOVEMENT_PIXEL_THRESHOLD = 15.0` externalized in `config/system_config.yaml` and `src/core/config.py`.
- [x] **Threat Scoring Neutrality**: Detections + zero verified evidence = 5.0/100 baseline (Feature 003); zero detections + zero verified evidence = 0.0/100 baseline. Movement or military target identity alone NEVER forces HIGH or CRITICAL threat levels without explicit security evidence (e.g. `zone_violation_flag`).

---

## Detailed Implementation Breakdown (17 Technical Focus Areas)

### 1. Existing Files / Classes / Services to Reuse (Unchanged)
- **`src/core/config.py` & `src/core/di_container.py`**: Centralized configuration loading & Dependency Injection service resolution singleton.
- **`src/core/database.py`**: SQLite database connection provider & baseline schema initialization.
- **`src/core/exceptions.py`**: Domain exception classes (`ModelLoadError`, `AnalysisProcessingError`, `ValidationError`).
- **`src/domain/entities.py`**: `BoundingBox`, `DetectionResult`, `FactorContribution`, `ThreatAssessmentResult`, `AnalysisRecord`, `DetectionRecord`, `AlertRecord`, `ReportRecord`.
- **`src/domain/interfaces.py`**: `IConfigurationService`, `IDatabaseService`, `IAnalysisRepository`, `AbstractDetectionService`, `AbstractThreatScoringService`, `AbstractExplainabilityService`.
- **`src/infrastructure/services/yolo_detection.py`**: `YoloDetectionService` consuming local military weights `data/models/yolov8n_kiit_mita.pt` with exact 7 KIIT-MiTA military classes: `0: Artilary`, `1: Missile`, `2: Radar`, `3: M. Rocket Launcher`, `4: Soldier`, `5: Tank`, and `6: Vehicle`.
- **`src/infrastructure/services/threat_scoring.py`**: `ThreatScoringService` evaluating threat levels with strict evidence-based neutrality.
- **`src/infrastructure/services/explainability.py`**: `ExplainabilityService` generating XAI rationale narratives and SOP operator action steps.
- **`src/infrastructure/services/demo_manager.py`**: `DemoManager` serving built-in offline demo media assets.

---

### 2. Files Needing Modification
- **`config/system_config.yaml`**: Add video target FPS, maximum duration, tracker IoU threshold, max missed frames, and movement pixel threshold parameters under the `video:` configuration block.
- **`src/core/config.py`**: Add class-level default constants (`VIDEO_TARGET_SAMPLE_FPS = 5`, `MAX_VIDEO_DURATION_SECONDS = 120`, `TRACKER_IOU_THRESHOLD = 0.3`, `TRACKER_MAX_MISSED_FRAMES = 2`, `MOVEMENT_PIXEL_THRESHOLD = 15.0`) and getter helper methods.
- **`src/domain/entities.py`**: Append new dataclasses: `VideoMetadata`, `TrajectoryPoint`, `TrackRecord`, `VideoAnalysisRequest`, `VideoAnalysisResult`.
- **`src/domain/interfaces.py`**: Append abstract base classes: `AbstractVideoProcessingService`, `AbstractTrackingService`, `IVideoSurveillanceService`.
- **`src/infrastructure/database/repositories.py`**: Update `AnalysisRepository` to store video analysis headers in `analyses` (`media_type = 'VIDEO'`), representative detection records in `detections`, and serialized complete `TrackRecord` list in `AnalysisRecord.artifact_path` JSON file, fully preserving existing `IMAGE` records.
- **`src/core/di_container.py`**: Register `VideoProcessingService`, `IoUTrackingService`, and `VideoSurveillanceService` into DI container singleton.
- **`src/infrastructure/services/demo_manager.py`**: Register built-in offline military drone and CCTV demo video file paths under `data/demo/drone/videos/` and `data/demo/cctv/videos/`.
- **`src/ui/pages/surveillance.py`**: Update Step 1 (Input Selection: support Video media type, Video Demo dropdown, Video Upload file_uploader), Step 3 (Run Analysis for Video), Step 4 (Video Player, Frame Breakdown, Track Summary Table, Trajectory Visualizer, Representative Annotated Frames).
- **`src/ui/pages/history.py` & `analytics.py`**: Ensure video analysis history records (`media_type = 'VIDEO'`) render cleanly alongside static image records.

---

### 3. New Files / Classes to Create
- **`src/infrastructure/services/video_processing.py`**: `VideoProcessingService(AbstractVideoProcessingService)` handling OpenCV `VideoCapture` validation, duration threshold enforcement, metadata extraction, derived frame sampling generator, and representative annotated frame extraction.
- **`src/infrastructure/services/iou_tracking.py`**: `IoUTrackingService(AbstractTrackingService)` implementing lightweight deterministic IoU multi-object tracking, same-class matching priority, missed-frame buffer memory retention, track ID lifecycle, and centroid displacement trajectory math.
- **`src/application/video_surveillance_service.py`**: `VideoSurveillanceService(IVideoSurveillanceService)` orchestrating the complete video pipeline: Video Ingestion → Metadata Extraction → Frame Sampling Generator → KIIT-MiTA Detection per frame → IoU Multi-Object Tracking & Trajectory Analysis → Aggregated Threat Assessment → XAI Narrative → SQLite Persistence → `VideoAnalysisResult` formatting.
- **`tests/unit/test_video_processing.py`**: Unit tests covering video validation, metadata extraction, frame sampling rate calculation, duration threshold rejection (>120s), corrupted file handling, 0-frame file handling.
- **`tests/unit/test_iou_tracking.py`**: Unit tests covering IoU distance calculations, same-class association priority, IoU threshold filtering, track creation, missed-frame buffer memory retention, track termination, centroid displacement, and Stationary vs Moving movement state classification.
- **`tests/unit/test_video_surveillance_service.py`**: Unit tests for application service pipeline with mocked dependencies.
- **`tests/integration/test_video_pipeline.py`**: Integration tests executing end-to-end video analysis on actual fine-tuned KIIT-MiTA YOLO model and real offline military demo video asset.

---

### 4. Domain Models Specifications

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid
from datetime import datetime

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
    representative_frame_bytes: List[bytes] = field(default_factory=list)
    annotated_video_path: Optional[str] = None
    processing_time_ms: float = 0.0
    persisted: bool = True
```

---

### 5. Video Processing Service & Interface Specification

- **Interface `AbstractVideoProcessingService(ABC)`**:
  ```python
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
  ```
- **Implementation `VideoProcessingService`**:
  - Uses OpenCV `cv2.VideoCapture` to read video headers (duration, FPS, frame count, resolution).
  - Enforces maximum video duration check: if `duration_seconds > 120.0` (`MAX_VIDEO_DURATION_SECONDS`), raises `ValidationError("Video duration exceeds maximum allowed limit of 120 seconds.")`, rejecting processing immediately without partial execution.
  - Calculates frame skip step $N = \max(1, \text{round}(\text{source\_fps} / \text{target\_fps}))$.
  - Yields `(frame_index, timestamp_sec, frame_bgr)` lazily to prevent memory spikes.
  - Safe error handling: raises `ValidationError` for zero-frame videos, missing files, or unreadable codecs.

---

### 6. Deterministic IoU Tracking Service & Interface Specification

- **Interface `AbstractTrackingService(ABC)`**:
  ```python
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
  ```
- **Implementation `IoUTrackingService`**:
  - Pure Python + NumPy deterministic tracking without external tracking framework dependencies.
  - **Intersection-over-Union (IoU) Formula**:
    $$\text{IoU}(A, B) = \frac{\text{Area}(A \cap B)}{\text{Area}(A \cup B)}$$
  - **Association Priority & Workflow**:
    1. For each incoming sampled frame, calculate pairwise IoU between current frame detections and active tracks' latest bounding boxes.
    2. Filter out matches with $\text{IoU} < \text{TRACKER\_IOU\_THRESHOLD}$ (default `0.30`).
    3. Prioritize same-class associations (`detection.class_name == track.class_name`).
    4. Greedily match highest IoU pairs first; update matched track's `last_frame`, `last_timestamp`, `detection_count`, `avg_confidence`, and append centroid `TrajectoryPoint`.
    5. Unmatched detections spawn new persistent `TrackRecord` with incrementing numerical `track_id` (1, 2, 3...).
    6. Unmatched active tracks increment missed-frame counter. If missed frames exceed `TRACKER_MAX_MISSED_FRAMES` (default `2`), close track.
  - **Determinism**: Sorting detections by bounding box coordinates before matching guarantees 100% reproducible output across identical runs.

---

### 7. Image-Space Movement & Trajectory Calculation

- **Centroid Calculation**: For bounding box $(x_1, y_1, x_2, y_2)$:
  $$x_c = \frac{x_1 + x_2}{2}, \quad y_c = \frac{y_1 + y_2}{2}$$
- **Pixel Displacement Calculation**: Euclidean distance between initial centroid $(x_0, y_0)$ and final centroid $(x_n, y_n)$:
  $$d_{\text{pixel}} = \sqrt{(x_n - x_0)^2 + (y_n - y_0)^2}$$
- **Movement State Classification**:
  $$\text{movement\_state} = \begin{cases} \text{"MOVING"}, & \text{if } d_{\text{pixel}} \ge \text{MOVEMENT\_PIXEL\_THRESHOLD} \quad (15.0 \text{ px}) \\ \text{"STATIONARY"}, & \text{otherwise} \end{cases}$$
- **Trajectory Direction Vector**: Cardinal direction calculated from $\Delta x = x_n - x_0$ and $\Delta y = y_n - y_0$:
  - Uses image-space axes ($+x$ East, $+y$ South). Calculates angle $\theta = \operatorname{atan2}(-\Delta y, \Delta x)$ mapped to 8 cardinal sectors: `North`, `North-East`, `East`, `South-East`, `South`, `South-West`, `West`, `North-West`.
- **Strict Terminology Enforced**: UI and XAI narratives explicitly use `image-space movement`, `pixel displacement`, `trajectory direction`, `observed duration`. Uncalibrated real-world physical speed (m/s) is NEVER claimed.

---

### 8. Existing Detector Integration & Zero-Detection Frame Handling

- Reuses `YoloDetectionService` without code modification.
- Invokes `yolo_service.detect(frame_rgb, confidence_threshold=0.25)` for each sampled frame.
- **Zero-Detection Frame Handling**: An individual sampled frame may contain 0 detections; processing MUST continue across all remaining sampled frames.
- **Zero-Detection Video Handling**: Only when ALL sampled frames across the entire video yield 0 detections will the final `VideoAnalysisResult` contain 0 tracks, render clean representative frames, and record a baseline `LOW` threat score ($0.0/100$) when no verified security evidence is present.

---

### 9. Configuration Additions

- **`config/system_config.yaml`**:
  ```yaml
  video:
    target_sample_fps: 5
    max_duration_seconds: 120
    tracker_iou_threshold: 0.30
    tracker_max_missed_frames: 2
    movement_pixel_threshold: 15.0
  ```
- **`src/core/config.py`**:
  ```python
  VIDEO_TARGET_SAMPLE_FPS: float = 5.0
  MAX_VIDEO_DURATION_SECONDS: int = 120
  TRACKER_IOU_THRESHOLD: float = 0.30
  TRACKER_MAX_MISSED_FRAMES: int = 2
  MOVEMENT_PIXEL_THRESHOLD: float = 15.0
  ```

---

### 10. Deterministic SQLite Persistence Strategy

- **Preserve Existing Schema**:
  - Insert row into existing `analyses` table:
    - `id`: analysis UUID
    - `timestamp`: ISO timestamp
    - `source_type`: DEMO or UPLOAD
    - `platform`: DRONE or CCTV
    - `media_type`: `'VIDEO'`
    - `scenario_name`: Scenario name or file name
    - `threat_score`, `threat_level`, `confidence_avg`, `processing_time_ms`, `status`
    - `artifact_path`: Path to JSON file containing serialized video analysis tracks and metadata (`data/artifacts/<analysis_id>_tracks.json`).
- **Detections Table Persistence**:
  - Insert representative detection records into the existing `detections` table schema, setting `frame_index` to the sampled frame number where each detection occurred.
- **Complete TrackRecord Persistence**:
  - Every completed `TrackRecord` is serialized to JSON and stored in the artifact JSON file (`artifact_path`).
  - Every persisted `TrackRecord` MUST explicitly include all 13 required fields:
    1. `track_id` (int)
    2. `class_id` (int)
    3. `class_name` (str)
    4. `first_frame` (int)
    5. `last_frame` (int)
    6. `first_timestamp` (float)
    7. `last_timestamp` (float)
    8. `detection_count` (int)
    9. `avg_confidence` (float)
    10. `movement_state` (str: 'STATIONARY' or 'MOVING')
    11. `pixel_displacement` (float)
    12. `trajectory_direction` (str)
    13. `trajectory_points` (List of dicts with `x`, `y`, `frame_index`, `timestamp_sec`)
- **Compatibility Guarantee**: Existing `IMAGE` records in `analyses` and `detections` remain 100% untouched and fully viewable.

---

### 11. Surveillance UI Changes

In `src/ui/pages/surveillance.py`:
- **Step 1 (Input Setup)**: Add Media Type toggle (`Image` vs `Video`). For Video, show Video Demo dropdown or Video File Uploader.
- **Step 3 (Execution Deck)**: Render "Run Video Surveillance Analysis" action button.
- **Step 4 (Results Deck)**:
  - Video Preview Player (`st.video`).
  - Video Metadata Metric Cards (Duration, Source FPS, Sampled Frames, Total Tracks, Processing Latency ms).
  - Multi-Object Tracking Breakdown Table (Track ID, Target Class, Detection Count, Observed Duration, Displacement px, Movement State).
  - Trajectory Breakdown Chart (Plotly 2D centroid movement visualizer).
  - Representative Annotated Frame Cards showing bounding boxes, class labels, and `Track #X` badges.
  - Threat Badge, Risk Factor Breakdown, XAI Rationale, and SOP Action Steps.

---

### 12. Offline Demo Video Handling

- Place deterministic demo videos under:
  - `data/demo/drone/videos/kiit_mita_drone_demo.mp4`
  - `data/demo/cctv/videos/cctv_perimeter_demo.mp4`
- Update `DemoManager` to register video assets and resolve local file paths without network calls.

---

### 13. Error Handling & Guardrails

- **Unreadable / Corrupted Video File**: Catch OpenCV errors or 0-frame metadata; render operator warning banner `"Invalid or corrupted video file. Unable to decode frames."` without stack trace exposure.
- **Duration Exceeded (> 120 Seconds)**: If video duration exceeds 120 seconds, reject processing immediately, display clear operator warning banner (`"Video duration exceeds maximum allowed limit of 120 seconds."`), and do NOT partially analyze the video.
- **Zero Detections Across All Frames**: If an individual frame yields 0 detections, continue processing remaining frames. Only when ALL frames yield 0 detections will the result contain 0 tracks, baseline threat score $0.0/100$, and clean representative frames.
- **Codec / VideoWriter Fallback**: Fall back gracefully to rendering representative annotated frame cards if local OpenCV `VideoWriter` fails to encode video artifact.

---

### 14. Automated Unit Test Suite

- `tests/unit/test_video_processing.py`: Validate metadata extraction, FPS frame sampling calculation, duration threshold rejection (>120s), and error boundaries on corrupted files.
- `tests/unit/test_iou_tracking.py`: Validate IoU calculation math, same-class priority matching, track ID persistence, missed-frame buffer memory, and `Stationary` vs `Moving` classification.
- `tests/unit/test_video_surveillance_service.py`: Validate end-to-end application service orchestration using stubbed/mocked detector & video reader.

---

### 15. Real Integration Test Suite

- `tests/integration/test_video_pipeline.py`: Real integration test loading actual KIIT-MiTA YOLO model (`data/models/yolov8n_kiit_mita.pt`) and real offline military demo video asset. Verifies video ingestion, YOLO detection, IoU multi-object tracking, threat assessment, and SQLite persistence.

---

### 16. Dependency & Execution Structure

```text
Phase 1: Domain Dataclasses & Interfaces (domain/entities.py, domain/interfaces.py)
   ↓
Phase 2: Configuration & Services (config.py, system_config.yaml, video_processing.py, iou_tracking.py)
   ↓
Phase 3: Application Service & DI Registration (video_surveillance_service.py, di_container.py)
   ↓
Phase 4: Repositories & Demo Assets (repositories.py, demo_manager.py, demo video files)
   ↓
Phase 5: Presentation Layer UI (surveillance.py, history.py, analytics.py)
   ↓
Phase 6: Automated Testing & End-to-End Verification (unit and integration tests)
```

---

### 17. Verification Commands

```bash
# 1. Run all unit tests for video processing, tracking, and services
pytest tests/unit/test_video_processing.py tests/unit/test_iou_tracking.py tests/unit/test_video_surveillance_service.py -v

# 2. Run real integration test with actual YOLO model and demo video
pytest tests/integration/test_video_pipeline.py -v

# 3. Run full test suite to verify zero regressions across Feature 001, 002, 003
pytest tests/ -v
```
