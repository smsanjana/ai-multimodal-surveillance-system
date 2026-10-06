# Tasks: Feature 003 — Military Object Detection Integration (Completed)

**Feature**: [specs/003-military-object-detection/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)  
**Plan**: [specs/003-military-object-detection/plan.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/plan.md)  
**Quickstart**: [specs/003-military-object-detection/quickstart.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/quickstart.md)

---

## Phase 1: Setup & Configuration

**Purpose**: Externalize model path and confidence threshold configuration.

- [X] T001 Configure military YOLO settings in `src/core/config.py` defining `YOLO_MODEL_PATH = "data/models/yolov8n_kiit_mita.pt"` and `YOLO_CONFIDENCE_THRESHOLD = 0.25` with environment variable / setting override support
- [X] T002 Update dependency injection factory in `src/core/di_container.py` to pass `Config.YOLO_MODEL_PATH` and `Config.YOLO_CONFIDENCE_THRESHOLD` into `YoloDetectionService` using the project's existing DI pattern without introducing new DI frameworks

---

## Phase 2: Foundational Detector Updates

**Purpose**: Core infrastructure updates in `YoloDetectionService` for KIIT-MiTA 7-class military target detection.

**⚠️ CRITICAL**: Must complete before user story UI integration.

- [X] T003 Update `YoloDetectionService` in `src/infrastructure/services/yolo_detection.py` to load model from configured `model_path` (`data/models/yolov8n_kiit_mita.pt` default), manage lazy singleton instance reloads on path change, filter by `confidence_threshold` (`0.25` default), and map class IDs $0-6$ deterministically to `Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, and `Vehicle`
- [X] T004 Enhance exception handling in `src/infrastructure/services/yolo_detection.py` to raise domain `ModelLoadError` when local model file is missing or corrupt, and `AnalysisProcessingError` on inference failures

---

## Phase 3: User Story 1 - Military Object Detection & Dual-Image Result View (Priority: P1) 🎯 MVP

**Goal**: Detect 7 military classes (`Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`) and display clean original and annotated detection images side-by-side.

**Independent Test**: Run analysis on a military drone image in `src/ui/pages/surveillance.py`; verify both original clean image and annotated image (with bounding boxes, class labels, and confidence tags) are displayed.

- [X] T005 [P] [US1] Implement unit tests with mocked/stubbed YOLO detector in `tests/unit/test_yolo_detection.py` verifying deterministic 7-class name mapping, confidence threshold filtering, and OpenCV bounding box annotation drawing
- [X] T006 [P] [US1] Update `ImageSurveillanceService` in `src/application/image_surveillance_service.py` to preserve both original input image path (`image_path`) and annotated result image path (`annotated_image_path`) in `SurveillanceAnalysis` entity
- [X] T007 [US1] Update Surveillance result view deck in `src/ui/pages/surveillance.py` to render clean original image and annotated detection result image side-by-side with target detection summary cards
- [X] T008 [US1] Update built-in drone demo scenarios in `src/infrastructure/services/demo_manager.py` to reference military drone images under `data/demo/drone/images/`

**Checkpoint**: At this point, User Story 1 (MVP) is fully functional and testable.

---

## Phase 4: User Story 2 - Configurable Detection & Threat Assessment Independence (Priority: P2)

**Goal**: Ensure configurable confidence filtering (`0.25`), clean 0-detection handling, and strict evidence separation (object class presence does not dictate HIGH/CRITICAL threat score).

**Independent Test**: Process an image containing a `Vehicle` or `Tank` in normal patrol context; verify target detection is recorded while threat score remains dependent on contextual evidence rather than object class identity alone.

- [X] T009 [P] [US2] Implement unit tests with mocked detector in `tests/unit/test_yolo_detection.py` verifying confidence threshold filtering (`0.25` default) and 0-detection result handling
- [X] T010 [US2] Add and verify automated tests in `tests/unit/test_threat_scoring.py` confirming that military detections are passed as neutral observation evidence to the existing Feature 002 threat-scoring engine, and that object class identity alone cannot force HIGH or CRITICAL threat levels

**Checkpoint**: User Stories 1 AND 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Robust Offline Execution & Navigation Integrity (Priority: P3)

**Goal**: Operator-friendly error handling for missing/corrupt model files, SQLite persistence of dual-image references, and 7-page navigation integrity.

**Independent Test**: Set `YOLO_MODEL_PATH` to a non-existent file; verify clean operator alert banner renders in UI without python tracebacks. Run end-to-end integration test with real model weights on a deterministic military image.

- [X] T011 [P] [US3] Implement unit tests with mocked detector in `tests/unit/test_yolo_detection.py` verifying clean raising of `ModelLoadError` for missing/corrupt model paths and `AnalysisProcessingError` for execution failures
- [X] T012 [US3] Add UI error handling in `src/ui/pages/surveillance.py` to display operator alert banners when `ModelLoadError` or `AnalysisProcessingError` occurs without exposing raw stack traces
- [X] T013 [US3] Verify SQLite persistence in `src/infrastructure/database/repositories.py` ensuring `SurveillanceAnalysis` (including dual image paths and detection JSON) is stored and retrievable in `src/ui/pages/history.py` and `src/ui/pages/analytics.py`
- [X] T014 [US3] Create real model integration test in `tests/integration/test_pipeline.py` loading actual `data/models/yolov8n_kiit_mita.pt` weights and executing an end-to-end analysis on one deterministic built-in KIIT-MiTA military drone image, verifying real YOLO inference, structured detections, and SQLite persistence

**Checkpoint**: All 3 user stories are complete, robustly handled, and persisted.

---

## Phase 6: Polish & Verification

**Purpose**: Full automated and manual validation.

- [X] T015 Run full pytest suite (`pytest tests/ -v`) to confirm fast mocked unit tests pass and real model integration test succeeds
- [X] T016 Execute manual quickstart verification ([quickstart.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/quickstart.md)) in Streamlit app (`streamlit run app.py`) across all 7 primary navigation pages

---

## Dependencies & Execution Order

### User Story Sequence
- **Setup & Foundational (Phase 1 & 2)**: Core configuration and `YoloDetectionService` updates (T001-T004). Blocks all user stories.
- **User Story 1 (Phase 3)**: Primary MVP functionality (T005-T008).
- **User Story 2 (Phase 4)**: Configuration thresholding and neutral threat evidence verification (T009-T010).
- **User Story 3 (Phase 5)**: UI error boundaries, SQLite persistence, and real model integration test (T011-T014).
- **Polish (Phase 6)**: Validation across unit tests, integration tests, and 7 UI pages (T015-T016).

---

## Parallel Execution Opportunities

- `T005 [P] [US1]` (Mocked unit test for US1) can run in parallel with `T006 [P] [US1]` (`ImageSurveillanceService` dual-image update).
- `T009 [P] [US2]` (Mocked unit test for confidence filtering) can run in parallel with `T010 [US2]` (threat scoring evidence test).
- `T011 [P] [US3]` (Mocked unit test for error boundaries) can run in parallel with `T012 [US3]` (UI exception rendering).

---

## Implementation Strategy

### MVP First (User Story 1)
1. Complete Phase 1 & Phase 2 (Config & `YoloDetectionService` updates).
2. Complete Phase 3 (User Story 1).
3. Validate User Story 1: Display dual original + annotated military images.

### Incremental Delivery
1. Add User Story 2: Configurable thresholding & neutral threat evidence testing.
2. Add User Story 3: Clean error UI banners, SQLite persistence, real model integration test on deterministic image.
3. Validate complete system across all 7 pages.
