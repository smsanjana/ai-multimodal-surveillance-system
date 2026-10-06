# Feature Specification: Video Surveillance & Object Tracking

**Feature Branch**: `004-video-surveillance-tracking`

**Created**: 2026-09-13

**Status**: Draft

**Input**: User description: "Extend the existing unified Surveillance workspace from image analysis to video surveillance, incorporating frame sampling, military object detection, multi-object tracking, image-space movement analysis, and SQLite persistence while maintaining strict threat-scoring neutrality."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Video Surveillance Ingestion & Multi-Object Tracking (Priority: P1) 🎯 MVP

As a security command deck operator, I want to ingest surveillance videos (from built-in offline demo assets or uploaded video files) within the unified Surveillance workspace, process selected frames through the KIIT-MiTA military object detector, and assign stable track IDs across frames so that I can observe individual target identities (`Tank`, `Missile`, `Soldier`, `Vehicle`, `Artilary`, `Radar`, `M. Rocket Launcher`) and their spatial persistence over time.

**Why this priority**: Core primary requirement for Feature 004. Extends the surveillance workspace from single static images to temporal video processing and multi-object tracking.

**Independent Test**: Select or upload a surveillance video, execute video analysis, and verify that:
1. Video metadata (duration, FPS, total frame count, sampled frame count) is extracted and displayed.
2. Target detections are assigned consistent numerical track IDs (e.g. `Track #1`, `Track #2`) across consecutive sampled frames.
3. Representative annotated video frames are rendered displaying bounding boxes, track IDs, class labels, and confidence tags.

**Acceptance Scenarios**:

1. **Given** a built-in military drone video, **When** the operator submits the video for surveillance analysis, **Then** the system extracts frames using the configured sampling strategy, detects military objects using the `yolov8n_kiit_mita.pt` model, and assigns persistent track IDs across frames.
2. **Given** an uploaded surveillance video file (`.mp4`, `.avi`, or `.mov`), **When** the operator runs video processing, **Then** the system extracts video metadata, tracks detected entities, and renders structured tracking summary cards showing track ID, associated target class, detection count, and duration observed.
3. **Given** temporary detection misses across 1–2 sampled frames due to minor occlusion or low confidence, **When** the object reappears, **Then** the tracking service re-associates the detection with the existing track ID rather than spawning a duplicate track.

---

### User Story 2 - Image-Space Movement & Trajectory Analysis (Priority: P2)

As a surveillance intelligence analyst, I want the system to calculate basic image-space movement metrics (stationary vs. moving, movement distance in pixels, trajectory direction, and observation duration) from tracked bounding box centroids, so that I can evaluate spatial target behavior without making uncalibrated physical speed claims.

**Why this priority**: Provides quantitative spatial-temporal telemetry for tracked objects while maintaining academic rigor by avoiding uncalibrated real-world physical speed assertions (e.g., m/s or km/h).

**Independent Test**: Process a video containing both parked/stationary vehicles and moving military units; verify that the system accurately classifies each track as `Stationary` or `Moving`, computes image-space pixel displacement and trajectory direction, and displays trajectory summaries.

**Acceptance Scenarios**:

1. **Given** a tracked object whose centroid displacement remains below the movement threshold across sampled frames, **When** trajectory analysis runs, **Then** the system classifies its movement state as `Stationary`.
2. **Given** a tracked object with significant centroid displacement across sampled frames, **When** trajectory analysis completes, **Then** the system classifies its movement state as `Moving`, computes approximate image-space pixel displacement, and logs its directional vector (e.g. `North-East`).
3. **Given** temporal telemetry displayed in the UI, **When** reading the XAI rationale, **Then** the system explicitly references `image-space movement`, `trajectory`, and `observed duration`, without claiming real-world physical speed measurements (m/s) or inferring hostile intent from movement alone.

---

### User Story 3 - Evidence-Based Threat Neutrality, Error Boundaries & Persistence (Priority: P3)

As a system administrator operating an offline command center, I want video analysis results (including metadata, detection summaries, track records, and threat evaluations) to be persisted to SQLite without corrupting past image records, while unreadable videos or processing exceptions trigger clean operator warning banners without stack traces.

**Why this priority**: Ensures system resilience, database contract integrity, offline-first compliance, clean UI feedback, and historical audit persistence.

**Independent Test**: Attempt to upload a corrupted or unreadable video file, trigger video processing, and confirm that an operator-friendly error message is displayed in the UI without crashing the application or showing Python tracebacks.

**Acceptance Scenarios**:

1. **Given** a corrupted, unreadable, or 0-frame video file, **When** an operator submits it for analysis, **Then** a clear operator alert banner is displayed indicating video file invalidity, preventing application crash or stack trace exposure.
2. **Given** a successful video surveillance analysis, **When** processing completes, **Then** the video analysis record, track summaries, and frame references are persisted to the SQLite database and appear in History and Analytics views.
3. **Given** detected military objects (`Tank`, `Soldier`, `Vehicle`, `Missile`, etc.) moving in a video feed without a verified restricted-zone signal, **When** threat evaluation completes, **Then** the threat level remains `LOW`, confirming that object class identity and movement alone do NOT force `HIGH` or `CRITICAL` threat levels.

---

### Out-of-Scope Declarations

To preserve project boundaries, the following capabilities are explicitly **OUT OF SCOPE** for Feature 004:
- Live camera feeds, RTSP network streaming, or WebRTC real-time ingestion
- Polygon geofencing, multi-point spatial zone geometry, or GIS coordinate mapping
- Real-world physical speed estimation (m/s or km/h) requiring camera calibration
- Autonomous targeting, weapon classification, or automated hostile-intent inference
- Model retraining or custom fine-tuning of YOLO weights
- LLM-based threat reasoning or cloud-dependent API calls
- Redesign or modification of the core Feature 003 threat-scoring algorithm

### Edge Cases & Failure Modes

- **Unreadable / Corrupted Video File**: System validates video header and frame reader initialization; displays a user-friendly error banner if video cannot be opened.
- **Zero Frames / Empty Video**: System checks total frame count and width/height dimensions; fails gracefully if frame count is 0.
- **Excessively Long Video**: System enforces a maximum video duration setting (`MAX_VIDEO_DURATION_SECONDS = 120` default) and applies configurable frame sampling derived from source FPS to cap processing time.
- **Zero Objects Detected Across All Frames**: System completes video analysis cleanly, reporting 0 tracks, rendering representative clean frames, and recording baseline `LOW` threat score ($0.0 / 100$) when no verified threat evidence is present. (When detections are present without verified evidence, the threat score remains the existing Feature 003 baseline of $5.0 / 100$).
- **Frequent Occlusion / Fragmented Tracks**: Deterministic IoU tracker maintains a configurable missed-frame buffer (`TRACKER_MAX_MISSED_FRAMES = 2`) to re-associate temporarily lost objects before closing a track.
- **Annotated Video Writing Failure**: If local OpenCV video writer fails (e.g. missing codec), system falls back gracefully to representative annotated frames and structured tracking summaries without losing analysis results.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extend the existing unified Surveillance workspace (Steps 1–5) to ingest and process video inputs for both `Drone` and `CCTV` platforms across `Built-in Demo` and `Upload Media` sources.
- **FR-002**: System MUST preserve existing Feature 002 and Feature 003 single-image surveillance workflows without modification or regression.
- **FR-003**: System MUST execute object detection on sampled video frames using the fine-tuned KIIT-MiTA military YOLO model (`data/models/yolov8n_kiit_mita.pt`) with default confidence threshold of `0.25`.
- **FR-004**: System MUST maintain exact KIIT-MiTA class mapping for all 7 military target classes: `0: Artilary`, `1: Missile`, `2: Radar`, `3: M. Rocket Launcher`, `4: Soldier`, `5: Tank`, and `6: Vehicle`.
- **FR-005**: System MUST implement a dedicated video processing service responsible for video validation, metadata extraction (duration, FPS, resolution, total frame count), deterministic frame sampling, and frame decoding.
- **FR-006**: System MUST calculate the frame sampling interval derived from the source video's actual FPS to target approximately 5 processed frames per second (`VIDEO_TARGET_SAMPLE_FPS = 5`), falling back safely to a default sampling interval if source FPS is invalid or missing.
- **FR-007**: System MUST implement a lightweight, deterministic IoU-based object tracking service without external tracking APIs. For each sampled frame, the tracker MUST: run detections, calculate IoU between current detections and active tracks, prefer same-class associations, associate detections when IoU meets or exceeds `TRACKER_IOU_THRESHOLD`, create new tracks for unmatched detections, keep unmatched tracks alive for up to `TRACKER_MAX_MISSED_FRAMES`, and close tracks once the missed-frame buffer is exceeded.
- **FR-008**: System MUST maintain structured track records containing `track_id`, `class_id`, `class_name`, `first_frame`, `last_frame`, `first_timestamp`, `last_timestamp`, `detection_count`, `avg_confidence`, `bounding_box_history`, and `trajectory_points`.
- **FR-009**: System MUST handle temporary detection misses (up to a configurable frame-buffer threshold) without spawning duplicate track IDs for the same physical target.
- **FR-010**: System MUST compute image-space movement metrics from tracked bounding box centroids, classifying each track's movement state as `Stationary` or `Moving` using the configured image-space pixel displacement threshold (`MOVEMENT_PIXEL_THRESHOLD`).
- **FR-011**: System MUST report movement strictly using image-space terminology (`image-space movement`, `pixel displacement`, `trajectory direction`, `observed duration`) without claiming uncalibrated physical speed (m/s).
- **FR-012**: System MUST maintain strict threat-scoring neutrality without modifying the Feature 003 threat scoring engine: when zero objects are detected and no verified evidence is present, threat score MUST be baseline $0.0/100$; when military object detections are present with no verified evidence, threat score MUST yield the existing Feature 003 baseline ($5.0/100$). Presence of military target classes or movement alone MUST NOT force `HIGH` or `CRITICAL` threat scores without explicit verified security evidence (e.g. `zone_violation_flag`).
- **FR-013**: System MUST update the Surveillance result view deck for video analyses to display:
  1. Original video preview / player
  2. Processing information (filename, platform, duration, FPS, total frames, sampled frames, processing time)
  3. Aggregated detection summary (total detections, observed classes, average confidence, per-class counts)
  4. Tracking summary (total tracks, track IDs, class name, detection count per track, duration, movement state)
  5. Trajectory & movement breakdown
  6. Representative annotated video frames displaying bounding boxes, track IDs, class labels, and confidence tags
  7. Threat evidence & risk assessment
  8. Explainable AI rationale narrative
  9. Recommended operator Standard Operating Procedure (SOP) action steps
  10. Persistence & export controls
- **FR-014**: System MUST attempt to render a processed/annotated video artifact when feasible, falling back gracefully to representative annotated frames if video encoding fails.
- **FR-015**: System MUST persist video analysis records, video metadata, detection summaries, track records, and movement summaries to the local SQLite database without breaking existing image analysis records.
- **FR-016**: System MUST bundle local offline military demo videos under `data/demo/drone/videos/` and `data/demo/cctv/videos/` prioritizing drone military target scenarios.
- **FR-017**: System MUST handle video ingestion and processing errors (unsupported format, corrupt file, 0 frames, missing file, detector/tracker failure) gracefully by rendering operator alert banners without exposing raw Python tracebacks.
- **FR-018**: System MUST preserve all 7 primary navigation pages (Dashboard, Surveillance, Analytics, History, Reports, Settings, About) and ensure past image history remains viewable alongside new video history entries.
- **FR-019**: System MUST expose all video processing and tracking parameters via the existing centralized configuration service (`src/core/config.py`), including `VIDEO_TARGET_SAMPLE_FPS = 5`, `MAX_VIDEO_DURATION_SECONDS = 120`, `TRACKER_IOU_THRESHOLD = 0.3`, `TRACKER_MAX_MISSED_FRAMES = 2`, and `MOVEMENT_PIXEL_THRESHOLD = 15.0`.
- **FR-020**: System MUST include comprehensive automated unit tests (metadata extraction, frame sampling, tracking association, stable track IDs, track lifecycle, movement classification, error boundaries) and end-to-end integration tests (deterministic demo video processing, KIIT-MiTA detector integration, tracking output, SQLite persistence).

---

## Non-Functional Requirements

- **NFR-001 (Offline Autonomy)**: System MUST operate 100% offline without requiring internet connectivity or cloud dependencies.
- **NFR-002 (Performance & Scalability)**: Frame sampling MUST cap video processing latency to under 30 seconds for standard 60-second demo clips on standard CPU hardware.
- **NFR-003 (Architecture Compliance)**: Implementation MUST follow Clean Architecture layers (Presentation $\to$ Application $\to$ Domain $\to$ Infrastructure) and consume dependencies via the existing DI Container.
- **NFR-004 (Resource Safety)**: Video frame processing MUST use generators or sliding frame buffers to prevent memory leaks or out-of-memory errors.
- **NFR-005 (Safety & Alignment)**: System MUST NOT perform autonomous targeting, weapon classification, or automated hostile-intent inference.
- **NFR-006 (UI Consistency)**: Interface MUST maintain the professional dark theme, minimalist controls, and high-contrast alert badges.
- **NFR-007 (Test Reliability)**: Unit and integration tests MUST be deterministic, fast, and execute cleanly via `pytest`.
- **NFR-008 (Maintainability)**: Detector and tracker components MUST remain abstract interfaces allowing future algorithm replacement without refactoring domain layers.

---

## Key Entities

- **VideoAnalysisRequest**: Application DTO encapsulating video source type (`DEMO`/`UPLOAD`), platform (`DRONE`/`CCTV`), scenario name, video file path or uploaded bytes, frame skip rate, and contextual security flags.
- **VideoMetadata**: Value object containing video file path, duration in seconds, frame rate (FPS), total frame count, resolution (width $\times$ height), and sampled frame count.
- **TrajectoryPoint**: Value object storing centroid coordinates $(x, y)$, frame index, and timestamp relative to video start.
- **TrackRecord**: Domain entity encapsulating a single tracked physical object across frames:
  ```python
  class TrackRecord:
      track_id: int                    # Persistent numerical track identifier
      class_id: int                    # KIIT-MiTA class ID (0 to 6)
      class_name: str                  # Target class label ('Tank', 'Missile', etc.)
      first_frame: int                 # Frame index where track first appeared
      last_frame: int                  # Frame index where track was last observed
      first_timestamp: float           # Timestamp (seconds) of first appearance
      last_timestamp: float            # Timestamp (seconds) of last appearance
      detection_count: int             # Total detections associated with this track
      avg_confidence: float            # Mean confidence score across detections
      movement_state: str              # 'STATIONARY' or 'MOVING'
      pixel_displacement: float        # Total centroid movement distance in pixels
      trajectory_direction: str        # Approximate cardinal direction (e.g. 'North-East')
      trajectory_points: List[TrajectoryPoint] # Bounding box centroid history
  ```
- **VideoAnalysisResult**: Aggregate root encapsulating `analysis_id`, `source_type`, `platform`, `video_metadata`, list of `TrackRecord` items, aggregated detection counts, threat assessment result, XAI narrative, SOP recommendation, original video reference, annotated video/frame references, processing time in ms, and creation timestamp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can select a built-in demo video or upload a video file in the Surveillance workspace and execute video analysis cleanly.
- **SC-002**: System processes video frames through the existing KIIT-MiTA military detector (`data/models/yolov8n_kiit_mita.pt`) with zero network dependencies.
- **SC-003**: Detections across consecutive sampled frames are assigned stable, persistent track IDs (`track_id`).
- **SC-004**: Each track record provides complete structured fields (class ID, class name, first/last frame, confidence statistics, detection count, bounding box history, trajectory points).
- **SC-005**: The system classifies each track's movement state as Stationary or Moving using the configured image-space pixel displacement threshold.
- **SC-006**: Surveillance UI displays video metadata, detection summary, tracking breakdown table, trajectory information, and representative annotated frames.
- **SC-007**: Successful video analyses are persisted to SQLite database storage and viewable in History and Analytics without breaking existing image records.
- **SC-008**: System operates 100% offline using built-in military drone demo video assets under `data/demo/drone/videos/`.
- **SC-009**: System handles unreadable files, corrupted headers, or processing failures gracefully by displaying user-friendly operator alert banners without raw Python stack traces.
- **SC-010**: 100% of existing Feature 001, Feature 002, and Feature 003 automated tests continue passing cleanly.
- **SC-011**: System maintains threat-scoring neutrality: military object presence and movement alone do NOT force `HIGH` or `CRITICAL` threat levels without verified security evidence.
- **SC-012**: System accurately logs and reports actual video processing latency in milliseconds.

---

## Assumptions & Dependencies

- **Local Weights Availability**: The fine-tuned KIIT-MiTA military detector weights `yolov8n_kiit_mita.pt` exist in `data/models/`.
- **OpenCV Video Utilities**: OpenCV (`cv2.VideoCapture`, `cv2.VideoWriter`) is available for frame extraction and video decoding.
- **Clean Architecture Preservation**: Infrastructure layer manages OpenCV video ingestion and tracking logic while Application/Domain layers operate on abstract interfaces (`AbstractVideoProcessingService`, `AbstractTrackingService`).
- **Single Unified Workspace**: Navigation remains fixed across the 7 primary pages defined in the Project Constitution.
