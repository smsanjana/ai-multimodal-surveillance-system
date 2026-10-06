# Implementation Tasks: Feature 004 - Video Surveillance & Object Tracking

**Branch**: `004-video-surveillance-tracking` | **Date**: 2026-09-13 | **Spec**: [specs/004-video-surveillance-tracking/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/004-video-surveillance-tracking/spec.md) | **Plan**: [specs/004-video-surveillance-tracking/plan.md](file:///Users/sanjana/Documents/ai_p2/specs/004-video-surveillance-tracking/plan.md)

---

## Phase 1: Setup & Configuration (Shared Infrastructure)

**Purpose**: Externalize all video processing and tracking configuration parameters in central YAML and Config service.

- [x] T001 Add video configuration block (`target_sample_fps: 5`, `max_duration_seconds: 120`, `tracker_iou_threshold: 0.30`, `tracker_max_missed_frames: 2`, `movement_pixel_threshold: 15.0`) in `config/system_config.yaml`
- [x] T002 Add class-level default constants (`VIDEO_TARGET_SAMPLE_FPS = 5.0`, `MAX_VIDEO_DURATION_SECONDS = 120`, `TRACKER_IOU_THRESHOLD = 0.30`, `TRACKER_MAX_MISSED_FRAMES = 2`, `MOVEMENT_PIXEL_THRESHOLD = 15.0`) and getter methods in `src/core/config.py`
- [x] T003 [P] Create/provide and verify deterministic offline playable demo video assets at `data/demo/drone/videos/kiit_mita_drone_demo.mp4` and `data/demo/cctv/videos/cctv_perimeter_demo.mp4` (reusing existing local KIIT-MiTA image assets/OpenCV video writer without cloud dependencies) and register paths in `src/infrastructure/services/demo_manager.py`

---

## Phase 2: Foundational Domain Contracts & Repositories

**Purpose**: Core domain DTOs, service interface abstractions, and SQLite repository persistence updating.

- [x] T004 [P] Add video domain dataclasses (`VideoMetadata`, `TrajectoryPoint`, `TrackRecord`, `VideoAnalysisRequest`, `VideoAnalysisResult`) in `src/domain/entities.py`
- [x] T005 [P] Add abstract interface base classes (`AbstractVideoProcessingService`, `AbstractTrackingService`, `IVideoSurveillanceService`) in `src/domain/interfaces.py`
- [x] T006 Update `AnalysisRepository` in `src/infrastructure/database/repositories.py` to store video headers in `analyses` (`media_type = 'VIDEO'`), representative detections in `detections`, and store the serialized 13-field `TrackRecord` list in artifact JSON file at `data/artifacts/<analysis_id>_tracks.json` referenced by `AnalysisRecord.artifact_path`, preserving existing `IMAGE` records

---

## Phase 3: User Story 1 - Video Surveillance Ingestion & Multi-Object Tracking (Priority: P1) 🎯 MVP

**Goal**: Ingest surveillance videos (demo or upload), extract metadata, sample frames at 5 FPS, detect KIIT-MiTA military objects, track entities using IoU, assign stable track IDs, and render annotated frame previews.

**Independent Test**: Submit a built-in demo or uploaded video file, run video processing, and verify video metadata display, stable numerical track IDs (`Track #1`, `Track #2`), and representative annotated video frame rendering.

### Unit Tests for User Story 1 (Mocked Dependencies)

- [x] T007 [P] [US1] Unit test for video processing service in `tests/unit/test_video_processing.py` (using mocked OpenCV `VideoCapture` to test metadata extraction, derived 5 FPS sampling rate calculation, corrupt file handling, and 0-frame file handling)
- [x] T008 [P] [US1] Unit test for IoU tracking service in `tests/unit/test_iou_tracking.py` (using mocked detections to test 2D IoU box overlap math, same-class priority matching, persistent track ID assignment, and missed-frame buffer memory retention up to `TRACKER_MAX_MISSED_FRAMES = 2`)

### Implementation for User Story 1

- [x] T009 [US1] Implement `VideoProcessingService` in `src/infrastructure/services/video_processing.py` (OpenCV `VideoCapture` metadata extraction, derived frame sampling generator targeting 5 FPS, temp upload file handling, safe error handling)
- [x] T010 [US1] Implement `IoUTrackingService` in `src/infrastructure/services/iou_tracking.py` (pure Python/NumPy IoU tracking, same-class association priority, greedy matching, persistent numerical track ID lifecycle, missed-frame buffer up to `TRACKER_MAX_MISSED_FRAMES = 2`)
- [x] T011 [US1] Implement `VideoSurveillanceService` in `src/application/video_surveillance_service.py` (orchestrates Video Ingestion → Metadata Extraction → Frame Sampling Generator → KIIT-MiTA YOLO Detection → IoU Tracking → Threat Assessment → XAI Rationale → SQLite Persistence → `VideoAnalysisResult`)
- [x] T012 [US1] Register video services (`VideoProcessingService`, `IoUTrackingService`, `VideoSurveillanceService`) in `src/core/di_container.py`
- [x] T013 [US1] Update Surveillance UI step controls and deck in `src/ui/pages/surveillance.py` (Media Type selector `Image` vs `Video`, Video Demo dropdown, Video Upload file_uploader, Run Video Surveillance Analysis button, Video Preview Player, representative annotated frame gallery)

---

## Phase 4: User Story 2 - Image-Space Movement & Trajectory Analysis (Priority: P2)

**Goal**: Compute centroid movement metrics, Euclidean pixel displacement, cardinal trajectory vector, stationary vs moving classification, and render trajectory visualizer deck in UI.

**Independent Test**: Process a video containing both stationary and moving target units; verify movement state classification as `Stationary` or `Moving` based on `MOVEMENT_PIXEL_THRESHOLD = 15.0` px, pixel displacement, trajectory vector, and Plotly trajectory graph.

### Unit Tests for User Story 2 (Mocked Dependencies)

- [x] T014 [P] [US2] Unit test for image-space movement and trajectory calculation in `tests/unit/test_iou_tracking.py` (verifying centroid calculation, Euclidean pixel displacement, `Stationary` vs `Moving` classification thresholding at 15.0 px, and cardinal direction vector calculation)

### Implementation for User Story 2

- [x] T015 [US2] Integrate image-space movement & trajectory math into `IoUTrackingService` in `src/infrastructure/services/iou_tracking.py` (`centroid_x`, `centroid_y`, `pixel_displacement`, `movement_state`, `trajectory_direction`, `trajectory_points`)
- [x] T016 [US2] Update Surveillance UI results deck in `src/ui/pages/surveillance.py` (Add Multi-Object Tracking Breakdown table, Trajectory Direction visualizer, Plotly 2D centroid trajectory chart, and enforce explicit image-space terminology in XAI rationale)

---

## Phase 5: User Story 3 - Evidence-Based Threat Neutrality, Error Boundaries & Persistence (Priority: P3)

**Goal**: Maintain threat-scoring neutrality, reject videos exceeding 120s, handle zero-detection frames, persist complete 13-field `TrackRecord` list to SQLite, and ensure History/Analytics view compatibility.

**Independent Test**: Attempt to ingest a video > 120 seconds (verify rejection warning banner), ingest a zero-detection video (verify 0 tracks, 0.0/100 threat score), verify SQLite database persistence, and confirm History and Analytics page display.

### Unit Tests for User Story 3 (Mocked Dependencies)

- [x] T017 [P] [US3] Unit test for video duration validation (>120s rejection) and zero-detection handling in `tests/unit/test_video_processing.py` & `tests/unit/test_video_surveillance_service.py`

### Implementation for User Story 3

- [x] T018 [US3] Enforce >120s duration rejection in `VideoProcessingService` in `src/infrastructure/services/video_processing.py` (raise `ValidationError` if `duration_seconds > 120.0`, rejecting processing immediately without partial execution)
- [x] T019 [US3] Handle zero-detection frames and zero-detection videos in `VideoSurveillanceService` in `src/application/video_surveillance_service.py` (continue processing remaining sampled frames when an individual frame has 0 detections; return 0 tracks and baseline $0.0/100$ threat score only when ALL frames yield 0 detections)
- [x] T020 [US3] Implement TrackRecord artifact persistence in `AnalysisRepository` in `src/infrastructure/database/repositories.py`: serialize the complete 13-field `TrackRecord` list (`track_id`, `class_id`, `class_name`, `first_frame`, `last_frame`, `first_timestamp`, `last_timestamp`, `detection_count`, `avg_confidence`, `movement_state`, `pixel_displacement`, `trajectory_direction`, `trajectory_points`) into a JSON artifact file at `data/artifacts/<analysis_id>_tracks.json`, storing this file path in `AnalysisRecord.artifact_path` without adding 13 columns to SQLite or redesigning the schema, fully preserving existing `IMAGE` persistence
- [x] T021 [US3] Update History and Analytics UI pages in `src/ui/pages/history.py` and `src/ui/pages/analytics.py` (Support rendering video records with `media_type = 'VIDEO'` alongside static image records without breaking past history)

---

## Phase 6: Verification & End-to-End Testing

**Purpose**: Execute real end-to-end integration tests using the actual trained KIIT-MiTA YOLO model and real offline military demo video, followed by full test suite regression verification.

- [x] T022 [P] Author real end-to-end integration test in `tests/integration/test_video_pipeline.py` (test execution requires completed Feature 004 implementation and offline demo video asset; loads actual `data/models/yolov8n_kiit_mita.pt` and offline demo video `data/demo/drone/videos/kiit_mita_drone_demo.mp4`, verifying end-to-end pipeline: video ingestion → frame sampling → KIIT-MiTA detection → IoU tracking → threat assessment → SQLite persistence)
- [x] T023 Run full regression test suite (`pytest tests/ -v`) to confirm 100% pass rate across Feature 001, Feature 002, Feature 003, and Feature 004 test suites
- [x] T024 Perform manual operator verification walkthrough in Streamlit UI (Launch application, test Video Demo ingestion, file upload, >120s error alert banner, trajectory visualizer, SQLite persistence, and History view)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup & Configuration (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion (MVP)
- **User Story 2 (Phase 4)**: Depends on User Story 1 tracking service completion
- **User Story 3 (Phase 5)**: Depends on User Story 1 & 2 completion
- **Verification (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities

- T003, T004, T005 can run in parallel during Setup/Foundational phases
- T007 and T008 (Unit tests for US1) can run in parallel
- T014 (Unit test for US2) can run in parallel with US1 work
- T017 (Unit test for US3) can run in parallel
- T022 (Real integration test) can be authored in parallel, but test execution requires completed implementation of video services (US1-US3) and offline demo video assets

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup & Configuration
2. Complete Phase 2: Foundational Domain Contracts & Repositories
3. Complete Phase 3: User Story 1 (Video Ingestion & Multi-Object Tracking)
4. **STOP and VALIDATE**: Verify User Story 1 independently using demo video assets
5. Deploy / demo MVP

### Incremental Delivery

1. Deliver US1 (MVP: Video ingestion, 5 FPS frame sampling, KIIT-MiTA detection, IoU tracking, annotated frames)
2. Add US2 (Image-space movement classification, pixel displacement, Plotly trajectory chart)
3. Add US3 (>120s duration rejection, zero-detection handling, complete 13-field `TrackRecord` persistence, History/Analytics compatibility)
4. Complete Phase 6: Real integration test with actual `yolov8n_kiit_mita.pt` model and full regression suite verification
