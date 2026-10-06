# Feature Specification: Military Object Detection Integration

**Feature Branch**: `003-military-object-detection`

**Created**: 2026-09-13 (Updated: 2026-09-13)

**Status**: Draft (Revised)

**Input**: User description: "Integrate the fine-tuned KIIT-MiTA YOLO model into the existing Surveillance image-analysis workflow."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Military Object Detection & Dual-Image Result View (Priority: P1)

As a security operator monitoring drone surveillance feeds, I want the system to detect and identify specialized military targets (Artilary, Missile, Radar, M. Rocket Launcher, Soldier, Tank, Vehicle) in uploaded or demo surveillance images, while preserving both the original clean input image and the annotated detection image in the Surveillance result view, so that I can inspect raw imagery alongside AI detection overlays.

**Why this priority**: Core primary requirement. Replaces the generic pre-trained COCO object detector with the domain-specific KIIT-MiTA military object detector in the surveillance analysis workflow while ensuring visual verification capability.

**Independent Test**: Upload or select a military drone surveillance image (e.g., tank or missile battery), run analysis, and verify that:
1. Both the original input image and the annotated detection image are preserved and accessible in the Surveillance result view.
2. Military-specific class labels (`Tank`, `Missile`, `Artilary`, etc.), bounding boxes, and confidence percentages meeting the configured confidence threshold are rendered on the annotated image.

**Acceptance Scenarios**:

1. **Given** a military drone surveillance image containing a tank, **When** the operator submits the image for surveillance analysis, **Then** the system renders both the original un-annotated image and an annotated detection image showing a bounding box labeled `Tank` with confidence percentage.
2. **Given** a surveillance image containing multiple military assets (e.g., `Soldier` and `Artilary`), **When** the operator runs image surveillance processing, **Then** all detected targets above the configured confidence threshold are individually listed in structured results with class name, confidence score, and bounding box coordinates.
3. **Given** any detected class index ($0-6$), **When** processed by the detector, **Then** the class ID is deterministically mapped to its standard human-readable display string (`Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`).

---

### User Story 2 - Configurable Detection & Threat Assessment Independence (Priority: P2)

As a security intelligence analyst, I want the military detector's confidence threshold and model weight path to be externally configurable, and object detections to serve strictly as objective visual evidence without forcing automated threat escalation, so that routine military asset presence (e.g., authorized vehicle movement) does not generate false alarm critical alerts.

**Why this priority**: Ensures flexible system configuration, conservative evidence-based threat scoring, and prevents hardcoded threat elevation based solely on object class presence.

**Independent Test**: Configure the detector confidence threshold (e.g., `0.25`), process an image containing a `Vehicle` or `Tank` in a normal patrol context; verify that object detections are filtered by the confidence threshold, reported accurately, and passed as evidence while the threat score remains dependent on verified contextual security signals rather than object class identity alone.

**Acceptance Scenarios**:

1. **Given** a configured detection confidence threshold (default: `0.25`), **When** image detection completes, **Then** only detections with confidence equal to or exceeding the threshold are included in the detection results and visual overlay.
2. **Given** an image processed by the military detector, **When** detections are passed to the threat assessment engine, **Then** the presence of a specific object class (e.g., `Tank` or `Vehicle`) does NOT automatically force a `HIGH` or `CRITICAL` threat level.
3. **Given** an image with zero detected objects above the confidence threshold, **When** surveillance analysis completes, **Then** the system reports 0 objects detected, displays the original image alongside a clean result view, and completes threat scoring without error.

---

### User Story 3 - Robust Offline Execution & Configuration Boundaries (Priority: P3)

As a system administrator operating in an offline environment, I want the system to load the model strictly from a configurable local file path (defaulting to `data/models/yolov8n_kiit_mita.pt`) and gracefully handle missing files or inference errors without exposing stack traces, while persisting valid analyses to history.

**Why this priority**: Guarantees system resilience, offline-first execution compliance, clean UI feedback, and historical audit persistence.

**Independent Test**: Change the configured model path to a missing location, trigger surveillance analysis, and confirm that an operator-friendly error message is displayed in the UI without crashing the application or showing python tracebacks.

**Acceptance Scenarios**:

1. **Given** the configured model file path (default: `data/models/yolov8n_kiit_mita.pt`) is missing or invalid on disk, **When** an operator attempts surveillance processing, **Then** a clear operator-facing notification is displayed indicating model unavailability, and no raw stack trace is rendered.
2. **Given** a successful military image analysis, **When** processing completes, **Then** both original and annotated image paths/references, detections, threat level, and metadata are persisted to the local database and appear in the History log.
3. **Given** system navigation across Dashboard, Analytics, History, Reports, Settings, and About pages, **When** switching views after running military surveillance processing, **Then** all 7 primary pages function without error.

---

### Domain Applicability Disclaimer & Scope Boundaries

> [!IMPORTANT]
> **Domain Validation Disclaimer**: The fine-tuned KIIT-MiTA YOLO model is validated primarily for aerial/drone surveillance imagery. The system MUST NOT claim equivalent detection accuracy for ground-level CCTV imagery without dedicated evaluation evidence.
> 
> **Explicit Feature 003 Scope Boundaries**:
> Feature 003 is strictly limited to military object detector integration for single-image surveillance processing. The following capabilities are explicitly OUT OF SCOPE for Feature 003:
> - Video file analysis or temporal tracking
> - Live camera feeds (RTSP/Webcam)
> - Polygon geofencing or restricted-zone boundary math
> - Model retraining or dataset augmentation workflows
> - Redesign or modification of the contextual threat-scoring engine

---

### Edge Cases

- **Missing Model File**: What happens when `data/models/yolov8n_kiit_mita.pt` (or configured path) does not exist on disk? System displays a clear warning banner asking the operator to verify model placement, preventing crashes.
- **Corrupt / Invalid Image File**: How does the system handle uploaded non-image or truncated binary files? System validates image file integrity during preprocessing and reports an input error.
- **No Objects Detected**: How does the system handle images where no military targets meet the confidence threshold? System completes the pipeline cleanly, recording 0 detections, rendering both original and clean result views, and setting threat score based on zero-detection context.
- **Low-Confidence Detections**: How does the system handle detections below the configured threshold? Detections below threshold (e.g., `< 0.25`) are filtered out and omitted from both structured output and visual overlay.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load the military object detection model from a configurable local file path, defaulting to `data/models/yolov8n_kiit_mita.pt`, with zero runtime network dependency.
- **FR-002**: System MUST replace generic COCO detection in the Surveillance image workflow with the fine-tuned KIIT-MiTA military object detector.
- **FR-003**: System MUST support a configurable detection confidence threshold (float between $0.0$ and $1.0$), with a documented default value of `0.25`.
- **FR-004**: System MUST deterministically map class IDs $0-6$ to the 7 supported KIIT-MiTA target class names: `0: Artilary`, `1: Missile`, `2: Radar`, `3: M. Rocket Launcher`, `4: Soldier`, `5: Tank`, and `6: Vehicle`.
- **FR-005**: System MUST extract structured detection records for every target meeting or exceeding the confidence threshold, containing class ID, class display name, confidence percentage, and bounding box coordinates $[x_1, y_1, x_2, y_2]$.
- **FR-006**: System MUST preserve both the original clean input image and the annotated detection image in the Surveillance result view.
- **FR-007**: System MUST render bounding boxes, class labels, and confidence values directly on the annotated surveillance image output.
- **FR-008**: System MUST treat object detections strictly as neutral observations and MUST NOT derive threat scores directly or automatically force `HIGH` or `CRITICAL` threat levels based on object class identity alone.
- **FR-009**: System MUST preserve the existing clean architecture detector interface abstraction, allowing alternative detection models to be configured without domain layer refactoring.
- **FR-010**: System MUST update built-in drone demo scenarios to execute against the military object detector.
- **FR-011**: System MUST handle model loading failures, missing weights files, invalid model paths, and inference exceptions gracefully with operator-focused status messages.
- **FR-012**: System MUST prevent raw internal exception tracebacks from displaying in the Streamlit UI.
- **FR-013**: System MUST persist all successful surveillance analysis results (including original and annotated image references, detections, and threat evaluations) to the existing SQLite database.
- **FR-014**: System MUST ensure all 7 primary navigation pages (Dashboard, Surveillance, Analytics, History, Reports, Settings, About) remain fully operational.
- **FR-015**: System MUST maintain the unified Surveillance workspace without creating separate isolated Drone or CCTV software pages.
- **FR-016**: System MUST include comprehensive unit and integration tests verifying model configuration, confidence threshold filtering, class mapping, and error handling.

### Key Entities

- **MilitaryDetection**: Represents an individual target detection in a surveillance image, containing class index, target class label, confidence score ($0.0 - 1.0$), and bounding box coordinates.
- **DetectionResult**: Aggregated container holding all detections meeting the confidence threshold, frame dimensions, processing status, and detection execution time.
- **SurveillanceAnalysis**: Domain entity encapsulating image metadata, source platform (Drone/CCTV), original image reference, annotated image reference, raw detections evidence, threat score evaluation, XAI explanation, and timestamp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Military surveillance images are processed using the local model at the configured path (defaulting to `data/models/yolov8n_kiit_mita.pt`) with zero external network calls.
- **SC-002**: 100% of valid detected class IDs ($0-6$) are deterministically mapped to their exact corresponding KIIT-MiTA class names (`Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`). Note: This criterion measures class ID mapping correctness, not overall model detection accuracy.
- **SC-003**: The Surveillance result view successfully preserves and displays both the original input image and the annotated detection image.
- **SC-004**: 100% of valid surveillance analyses are persisted to local database storage and viewable in History and Analytics pages.
- **SC-005**: System handles missing model files or corrupt images without application crashes, displaying operator feedback in under 1 second.
- **SC-006**: All existing unit and integration tests pass, alongside new integration tests for the military detection service.

---

## Assumptions

- **Local Model Availability**: The trained model weights `yolov8n_kiit_mita.pt` exist under `data/models/` in the project root.
- **Clean Architecture Preservation**: Infrastructure layer manages YOLO model instantiation while Domain/Application layers interact via abstract `ObjectDetector` interfaces.
- **Threat Engine Stability**: Feature 002 threat assessment engine contracts remain intact; detection evidence is supplied to the threat engine as neutral observation inputs.
- **Single Unified UI**: Navigation remains fixed across the 7 standard pages defined in the Project Constitution.
