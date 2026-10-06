# Tasks: Image Surveillance Processing

**Feature Identifier**: `specs/002-image-surveillance-processing`  
**Date**: 2026-09-13  
**Status**: Completed  
**Plan**: [`plan.md`](file:///Users/sanjana/Documents/ai_p2/specs/002-image-surveillance-processing/plan.md)  
**Spec**: [`spec.md`](file:///Users/sanjana/Documents/ai_p2/specs/002-image-surveillance-processing/spec.md)  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify local assets and core configuration required for Feature 002.

- [x] T001 Verify local YOLOv8 weights asset exists at `data/models/yolov8n.pt` and is loadable offline in `config/system_config.yaml`
- [x] T002 [P] Verify system configuration schema in `src/core/config.py` supports model path `data/models/yolov8n.pt` and default detection confidence threshold `0.25`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain contracts, DTOs, and base exception handling required by all Feature 002 services.

**⚠️ CRITICAL**: Must be completed before implementing specific user story services.

- [x] T003 [P] Add domain value objects and DTOs (`BoundingBox`, `DetectionResult`, `FactorContribution`, `ThreatAssessmentResult`, `ImageAnalysisRequest`, `ImageAnalysisResponse`) in `src/domain/entities.py`
- [x] T004 [P] Define core domain service abstract interfaces (`AbstractDetectionService`, `AbstractThreatScoringService`, `AbstractExplainabilityService`, `IAnalysisRepository`) in `src/domain/interfaces.py`
- [x] T005 [P] Add domain-specific exceptions (`ImageValidationError`, `ModelLoadError`, `AnalysisProcessingError`) in `src/core/exceptions.py`

**Checkpoint**: Core domain interfaces and DTOs established - service implementations can proceed.

---

## Phase 3: User Story 1 - Real AI Image Detection & Annotation (Priority: P1) 🎯 MVP

**Goal**: Security operators can upload an image or select a demo image, execute YOLOv8 detection, view annotated bounding boxes/labels side-by-side, and inspect structured object counts.

**Independent Test**: Upload a test image or select a demo image, click "Run Surveillance Analysis", and verify that bounding boxes, class labels, confidence tags, and detected objects table render with latency displayed in ms.

### Tests for User Story 1
- [x] T006 [P] [US1] Unit test for image file validation rules (`.jpg`, `.png`, size/header checks) in `tests/unit/test_image_validator.py`
- [x] T007 [P] [US1] Unit test for YOLOv8 object detection inference, bounding box normalization, and image annotation in `tests/unit/test_yolo_detection.py`

### Implementation for User Story 1
- [x] T008 [P] [US1] Implement `ImageValidator` in `src/infrastructure/services/image_validator.py` validating `.jpg`, `.jpeg`, `.png` extensions, image header integrity, and max payload limits (FR-001)
- [x] T009 [US1] Implement `YoloDetectionService` in `src/infrastructure/services/yolo_detection.py` extending `AbstractDetectionService`, lazily loading `data/models/yolov8n.pt` as a singleton, executing YOLO inference, normalizing coordinates into `DetectionResult` DTOs, and rendering annotated bounding box overlays onto RGB image arrays using OpenCV (FR-003, FR-004, FR-005)

**Checkpoint**: `YoloDetectionService` is fully functional and testable independently.

---

## Phase 4: User Story 2 - Contextual Threat Assessment & Explainable AI (Priority: P1)

**Goal**: Analyzed images produce a quantitative threat score (0–100), threat level (LOW, MEDIUM, HIGH, CRITICAL), XAI factor breakdown, natural language summary, and SOP recommended actions.

**Independent Test**: Execute analysis on images representing different threat levels and verify dynamic score calculation, threat level badges, XAI rationale, and SOP decision support wording.

### Tests for User Story 2
- [x] T010 [P] [US2] Unit test for contextual threat scoring math, signal weights, and threat level mapping in `tests/unit/test_threat_scoring.py`
- [x] T011 [P] [US2] Unit test for XAI factor attributions, justification narrative, and SOP action mapping in `tests/unit/test_explainability.py`

### Implementation for User Story 2
- [x] T012 [P] [US2] Implement `ThreatScoringService` in `src/infrastructure/services/threat_scoring.py` extending `AbstractThreatScoringService`, aggregating detected object classes, counts, crowding density, and scenario metadata into a 0.0–100.0 score mapped to LOW (0–24.9), MEDIUM (25–49.9), HIGH (50–74.9), and CRITICAL (75–100.0) without assuming single classes are inherently dangerous (FR-009, FR-010)
- [x] T013 [US2] Implement `ExplainabilityService` in `src/infrastructure/services/explainability.py` extending `AbstractExplainabilityService`, generating itemized `FactorContribution` lists, natural language decision rationale, and safety-compliant operator SOP recommendations (FR-011, FR-012)

**Checkpoint**: Threat assessment and XAI engine fully functional and testable independently.

---

## Phase 5: User Story 3 - Built-in Offline Demo Image Scenarios (Priority: P1)

**Goal**: Provide 6 pre-packaged built-in Drone and CCTV demo image scenarios operating 100% offline through the exact production AI detection and threat scoring pipeline.

**Independent Test**: Disconnect network, select each of the 6 built-in demo image scenarios, execute analysis, and verify real AI pipeline execution offline.

### Tests for User Story 3
- [x] T014 [P] [US3] Unit test for demo scenario asset loading and manifest listing in `tests/unit/test_demo_manager.py`

### Implementation for User Story 3
- [x] T015 [P] [US3] Ensure 6 built-in demo image assets exist under `data/demo/drone/images/` and `data/demo/cctv/images/` explicitly for: Drone Normal Patrol, Drone Traffic Density, Drone Restricted Area Intrusion, CCTV Entrance Patrol, CCTV Parking Lot Activity, and CCTV Unauthorized Perimeter Access (FR-015)
- [x] T016 [US3] Implement `DemoManager` in `src/infrastructure/services/demo_manager.py` listing and reading local demo image scenarios and providing file paths/bytes for production pipeline execution (FR-015, FR-016, FR-017)

**Checkpoint**: 6 built-in demo image scenarios load and execute offline.

---

## Phase 6: User Story 4 - SQLite Persistence & System-Wide Metrics Integration (Priority: P1)

**Goal**: Automatically persist completed image analysis runs to SQLite via `DatabaseService` and `IAnalysisRepository`, immediately updating History audit logs, Dashboard executive metrics, and Analytics trends.

**Independent Test**: Complete an image analysis run, navigate to History, Dashboard, and Analytics pages, and verify new record appears immediately in recent activity tables and metric summary charts.

### Tests for User Story 4
- [x] T017 [P] [US4] Unit test for repository persistence of analysis runs and detections in `tests/unit/test_analysis_repository.py`
- [x] T018 [P] [US4] Unit test for `ImageSurveillanceService` use case orchestrator in `tests/unit/test_image_surveillance_service.py`

### Implementation for User Story 4
- [x] T019 [P] [US4] Extend `AnalysisRepository` in `src/infrastructure/database/repositories.py` implementing `IAnalysisRepository` to persist analysis records, detection lists, threat scores, XAI rationale, and SOP text using the existing `DatabaseService` (FR-013)
- [x] T020 [US4] Implement `ImageSurveillanceService` use case in `src/application/image_surveillance_service.py` orchestrating validation, detection, threat scoring, XAI generation, image annotation, and automatic repository persistence (FR-008, FR-013)
- [x] T021 [US4] Register `ImageSurveillanceService`, `YoloDetectionService`, `ThreatScoringService`, `ExplainabilityService`, `DemoManager`, and `AnalysisRepository` in `src/core/di_container.py`
- [x] T022 [US4] Update `src/ui/pages/surveillance.py` UI deck to consume `ImageSurveillanceService` from `DIContainer`, render guided wizard workflow (Source → Platform → Type → Scenario/Input → Run → Results) on the existing unified Surveillance page (without creating separate Drone, CCTV, Image, or Video pages), display side-by-side original and annotated output images, render detected objects breakdown table, show processing latency in ms (acceptance target < 3000 ms), render threat level badges, XAI rationale panel, and SOP recommendations (FR-005, FR-006, FR-007, FR-018, FR-019)
- [x] T023 [US4] Verify `src/ui/pages/dashboard.py`, `src/ui/pages/analytics.py`, and `src/ui/pages/history.py` query SQLite via repositories to immediately display newly saved image analysis records upon page navigation without application restart (FR-014)

**Checkpoint**: End-to-end image surveillance pipeline complete, persisted, and synchronized across UI decks.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, performance verification, and quickstart validation.

- [x] T024 [P] Implement end-to-end pipeline integration test in `tests/integration/test_image_pipeline.py` verifying full flow (Validation → Detection → Scoring → XAI → Persistence)
- [x] T025 Execute test suite `python -m pytest tests/ -v` to ensure 100% pass rate across all unit and integration tests (SC-006)
- [x] T026 Execute end-to-end UI quickstart validation scenarios from `specs/002-image-surveillance-processing/quickstart.md` using `streamlit run app.py`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all User Stories.
- **Phase 3 (User Story 1 - Detection & Annotation)**: Depends on Phase 2.
- **Phase 4 (User Story 2 - Threat Scoring & XAI)**: Depends on Phase 2 and DTOs from US1.
- **Phase 5 (User Story 3 - Built-in Offline Demos)**: Depends on Phase 2.
- **Phase 6 (User Story 4 - Persistence & UI Integration)**: Depends on Phases 3, 4, and 5.
- **Phase 7 (Polish & Verification)**: Depends on all User Stories complete.

### Parallel Opportunities
- T002, T003, T004, T005 can run in parallel (Phase 1 & 2 DTOs and contracts).
- T006, T007, T008 (US1 validation and detection unit tests/services) can run in parallel.
- T010, T011, T012 (US2 scoring and XAI unit tests/services) can run in parallel.
- T014, T015 (US3 demo manager unit tests and asset check) can run in parallel.
- T017, T018, T019 (US4 repository tests and implementation) can run in parallel.

---

## Implementation Strategy

### MVP First Scope (Phases 1–3)
1. Complete Setup and Foundational DTOs/contracts (T001–T005).
2. Complete User Story 1 (T006–T009) to verify local YOLOv8 detection and bounding box annotation.

### Full Feature Incremental Delivery (Phases 4–7)
1. Add Threat Scoring & XAI Engine (T010–T013).
2. Add Offline Demo Manager & Assets (T014–T016).
3. Connect Use Case Orchestrator, SQLite Persistence, and Streamlit Surveillance UI (T017–T023).
4. Run integration tests and quickstart validation (T024–T026).
