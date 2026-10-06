# Feature Specification: Image Surveillance Processing

**Feature Identifier**: `specs/002-image-surveillance-processing`  
**Created**: 2026-09-13  
**Status**: Draft  
**Input**: `/speckit-specify Create Feature 002 specification for Image Surveillance Processing for the AI Surveillance Command Center.`  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## 1. User Scenarios & Testing *(mandatory)*

### User Story 1 - Real AI Image Detection & Annotation (Priority: P1)

As a security operator, I want to upload a surveillance image or select a built-in demo image (Drone or CCTV) and run analysis, so that object detection identifies objects, highlights them with bounding boxes and labels on the image, and displays structured detection results.

**Why this priority**: Core AI image processing capability upgrading the Surveillance deck from shell placeholders to production computer vision analysis.

**Independent Test**: Upload a test image or select a built-in demo image, click "Run Surveillance Analysis", and verify that the output image is rendered with bounding boxes, class labels, and confidence tags, and the detected objects table is populated.

**Acceptance Scenarios**:
1. **Given** the Surveillance page is in Image mode, **When** an image file (e.g. `.jpg`, `.png`) is uploaded or a built-in demo scenario is selected, **Then** clicking "Run Surveillance Analysis" preprocesses the image and passes it to the `AbstractDetectionService`.
2. **Given** object detection completes, **When** results are rendered, **Then** an annotated output image displaying bounding boxes, class names, and confidence percentages is shown alongside an object count breakdown.
3. **Given** an invalid or corrupted file (e.g. non-image file, corrupt headers), **When** uploaded, **Then** an operator-friendly error banner is displayed and execution halts safely without crashing the UI.

---

### User Story 2 - Contextual Threat Assessment & Explainable AI (Priority: P1)

As a surveillance supervisor, I want every analyzed image to produce a quantitative threat score (0–100), threat level classification (LOW, MEDIUM, HIGH, CRITICAL), XAI decision rationale, and recommended SOP action, so that I can understand why a threat level was assigned without guessing.

**Why this priority**: Fulfills the mission-critical requirement of `constitution.md` (Section 3) and `architecture.md` (Section 9) for explainable decision intelligence.

**Independent Test**: Run image analysis on scenarios representing different threat levels and verify that threat score, level badge, primary contributing factors, and SOP recommended actions update dynamically.

**Acceptance Scenarios**:
1. **Given** object detection results for an image, **When** evaluated by `ThreatScoringService`, **Then** a threat score between 0.0 and 100.0 is computed based on contextual signals (object classes, counts, scenario metadata, zone rules) rather than assuming any single class is automatically dangerous.
2. **Given** the computed score, **When** mapped to a threat level, **Then**:
   - `0 - 24`: 🟢 **LOW**
   - `25 - 49`: 🟡 **MEDIUM**
   - `50 - 74`: 🟠 **HIGH**
   - `75 - 100`: 🔴 **CRITICAL**
3. **Given** a threat level assignment, **When** rendered in the UI, **Then** `ExplainabilityService` outputs a human-readable "Why?" breakdown showing factor contributions and recommended SOP operator actions.

---

### User Story 3 - Built-in Offline Demo Image Scenarios (Priority: P1)

As a system demonstrator, I want pre-packaged built-in Drone and CCTV demo images representing Low, Medium, and High/Critical threat scenarios that run through the exact production AI pipeline offline, so that I can conduct live demonstrations without internet access.

**Why this priority**: Implements `constitution.md` (Section 6) and `architecture.md` (Section 14) for offline demonstration readiness.

**Independent Test**: Disconnect from the internet, select each of the 6 built-in demo image scenarios, execute analysis, and verify real AI pipeline execution and deterministic, explainable threat outputs.

**Acceptance Scenarios**:
1. **Given** offline execution, **When** the demonstrator selects a Drone demo scenario (Normal/Traffic/Restricted Area) or CCTV demo scenario (Normal/Activity/Unauthorized Area), **Then** the local demo image file is loaded from `data/demo/`.
2. **Given** demo image selection, **When** "Run Surveillance Analysis" is clicked, **Then** the image passes through the exact same production detection, scoring, XAI, and persistence pipeline as uploaded images, producing deterministic and explainable threat outputs consistent with configured threat-scoring rules.

---

### User Story 4 - SQLite Persistence & System-Wide Metrics Integration (Priority: P1)

As a command center auditor, I want every completed image analysis to be saved automatically to SQLite, so that new results immediately appear in the History audit log, Dashboard metrics, and Analytics trends.

**Why this priority**: Ensures data persistence and cross-page state synchronization (`architecture.md` Section 17 & 21).

**Independent Test**: Complete an image analysis run, navigate to History, Dashboard, and Analytics pages, and verify that the newly saved record is listed and reflected in system metrics.

**Acceptance Scenarios**:
1. **Given** a completed image analysis run, **When** processing finishes, **Then** `AnalysisRecord`, `DetectionRecord` list, and `ThreatAssessmentRecord` are saved automatically to SQLite via `IAnalysisRepository`.
2. **Given** saved analysis records, **When** navigating to 📁 History, 🏠 Dashboard, or 📊 Analytics, **Then** the new record appears immediately in recent activity tables and metric summary charts.

---

## 2. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST validate uploaded image files for format (`.jpg`, `.jpeg`, `.png`), readability, and size prior to pipeline execution.
- **FR-002**: The system MUST provide an abstract detection interface (`AbstractDetectionService`) in `src/domain/interfaces.py` that decouples UI rendering from concrete AI detection frameworks.
- **FR-003**: The initial detection implementation (`YoloDetectionService` in `src/infrastructure/services/yolo_detection.py`) MUST load YOLOv8 weights from `data/models/yolov8n.pt` (configured in `config/system_config.yaml`) without initiating runtime network downloads.
- **FR-004**: Detection output MUST return structured Data Transfer Objects (`DetectionResult`) containing `class_id`, `class_name`, `confidence`, `bbox` (`x_min`, `y_min`, `x_max`, `y_max`), and `detection_id`.
- **FR-005**: The system MUST annotate detected bounding boxes, class labels, and confidence percentages onto the output image and display both original and annotated images side-by-side on the Surveillance deck.
- **FR-006**: The system MUST display an object detection breakdown table listing class names, confidence scores, bounding box coordinates, and object count totals.
- **FR-007**: The system MUST calculate and display overall image inspection metrics including object counts, average confidence percentage, and processing execution latency in milliseconds.
- **FR-008**: The system MUST implement an `ImageSurveillanceService` application use case in `src/application/image_surveillance_service.py` orchestrating validation, detection, threat scoring, XAI rationale generation, and persistence.
- **FR-009**: `ThreatScoringService` MUST evaluate image-level contextual signals (detected object classes, counts, scenario metadata, confidence, and pre-existing zone-violation flags if available) to produce a 0.0–100.0 score mapped to `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`. Feature 002 MUST NOT implement restricted-zone polygon geometry, polygon calculations, or zone intersection detection.
- **FR-010**: Threat assessment MUST NOT assume an object class (e.g. `car`, `person`) is inherently dangerous without contextual signal aggregation.
- **FR-011**: `ExplainabilityService` MUST generate human-readable factor attributions (e.g., "+25.0 due to 3 vehicles in restricted zone") and natural language decision summaries explaining *why* the threat level was assigned.
- **FR-012**: The system MUST output recommended Standard Operating Procedure (SOP) operator action steps corresponding to the assigned threat level.
- **FR-013**: The system MUST automatically persist completed image analysis runs, individual object detections, and threat assessment records to the SQLite database via `AnalysisRepository` immediately after processing completes.
- **FR-014**: Persisted image analysis records MUST immediately be reflected in 📁 History tables, 🏠 Dashboard metrics, and 📊 Analytics charts without requiring application restart.
- **FR-015**: The system MUST include built-in offline demo image assets under `data/demo/` for:
  - Drone Normal Patrol (Low Threat)
  - Drone Traffic Density (Medium Threat)
  - Drone Restricted Area Intrusion (High Threat)
  - CCTV Entrance Patrol (Low Threat)
  - CCTV Parking Lot Activity (Medium Threat)
  - CCTV Unauthorized Perimeter Access (High/Critical Threat)
- **FR-016**: Built-in demo images MUST execute through the exact same production AI detection and threat scoring pipeline as user-uploaded files.
- **FR-017**: All AI model loading, image processing, and database operations MUST function 100% offline without external network or API calls.
- **FR-018**: The system MUST catch processing exceptions (invalid file, corrupt image, model loading error) and display user-friendly error banners on the Surveillance page.
- **FR-019**: The system MUST preserve the existing 7-page navigation structure and professional dark command center CSS theme.

---

### Key Entities

- **ImageAnalysisRequest**: DTO containing `source_type` (DEMO/UPLOAD), `platform` (DRONE/CCTV), `scenario_name` (optional), and `image_bytes_or_path`.
- **DetectionResult**: DTO containing `detection_id` (UUID), `class_id` (int), `class_name` (str), `confidence` (float), and `bbox` (`x_min`, `y_min`, `x_max`, `y_max`).
- **ThreatAssessmentResult**: DTO containing `threat_score` (float), `threat_level` (str), `factor_contributions` (List[Dict]), `xai_reason` (str), and `recommended_sop` (str).
- **ImageAnalysisResponse**: Complete pipeline response containing `analysis_id`, `original_image`, `annotated_image`, `detections` (List[DetectionResult]), `threat_assessment` (ThreatAssessmentResult), `processing_time_ms` (float), and `timestamp`.

---

## 3. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Object detection and bounding box annotation on a standard 1280x720 surveillance image complete in under **3.0 seconds** on the target local CPU environment, excluding one-time model loading. Processing execution latency MUST remain measurable and displayed in the UI.
- **SC-002**: 100% of built-in demo images (6 scenarios) execute through the production AI detection pipeline and display real bounding box annotations and threat scores offline.
- **SC-003**: 100% of completed image analysis runs persist successfully to SQLite and immediately appear in History audit logs upon page navigation.
- **SC-004**: Threat scoring engine correctly maps quantitative scores to all 4 threat levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with corresponding XAI rationale statements.
- **SC-005**: Invalid or corrupted upload files trigger actionable error messages without causing Streamlit page exceptions or application crashes.
- **SC-006**: Automated test suite (`pytest`) verifies image validation, detection service output, threat scoring math, XAI generation, repository persistence, and UI rendering with **100% test pass rate**.

---

## 4. Assumptions

- **Local Model Asset**: YOLOv8 weights file MUST already exist locally at `data/models/yolov8n.pt` before runtime (configurable via `config/system_config.yaml`). The application MUST NOT automatically download model weights during application startup or analysis execution.
- **Offline Hardware**: Target system possesses sufficient RAM (4GB+) and CPU resources for local PyTorch/YOLOv8 inference.
- **Scope Boundary**: Video processing, multi-object frame tracking, trajectory calculations, live RTSP camera feeds, and automated PDF report compilation are explicitly out of scope for Feature 002.

---

## 5. Non-Goals *(Explicit Exclusions)*

The following capabilities are **EXPLICITLY EXCLUDED** from Feature 002:
- ❌ Video file frame extraction and sequential video processing loops.
- ❌ Temporal multi-object tracking across video frames (SORT / ByteTRACK).
- ❌ Movement velocity and trajectory vector calculations.
- ❌ Live RTSP camera stream ingest and frame sampling.
- ❌ Real-time threat alert dispatch to external networks.
- ❌ Automated PDF report generation (reserved for later features).
