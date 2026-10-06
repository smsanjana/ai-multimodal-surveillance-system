# Research & Technical Decisions: Image Surveillance Processing

**Feature Identifier**: `specs/002-image-surveillance-processing`  
**Date**: 2026-09-13  
**Status**: Completed  

---

## 1. Object Detection Framework & Offline Model Asset Management

### Decision
Implement `YoloDetectionService` inside `src/infrastructure/services/yolo_detection.py` extending `AbstractDetectionService` (`src/domain/interfaces.py`). The service loads weights lazily from `data/models/yolov8n.pt` as configured in `config/system_config.yaml`.

### Rationale
- **Clean Architecture Isolation**: The UI and application layers consume `AbstractDetectionService` and `DetectionResult` DTOs, preventing direct coupling to `ultralytics` or PyTorch data types.
- **Offline Autonomy**: Weights file MUST exist locally at `data/models/yolov8n.pt`. Model initialization disables network checks (`weights_only=True` / local path enforcement) to guarantee 100% offline execution.
- **Performance**: Object detection latency will be measured on the target local CPU environment, with an acceptance target of under 3.0 seconds per 1280x720 image, excluding one-time model loading (**SC-001**).

### Alternatives Considered
- **Direct YOLO calls in Streamlit (`st.file_uploader`)**: Rejected due to explicit prohibition in `constitution.md` (Zero UI business logic) and `architecture.md` (Clean Architecture layer boundaries).
- **Auto-downloading weights via Ultralytics API**: Rejected due to user-requested correction requiring strictly offline local assets.

---

## 2. Multi-Signal Contextual Threat Scoring Engine

### Decision
Implement `ThreatScoringService` in `src/infrastructure/services/threat_scoring.py`. The engine evaluates detected object classes, object counts, spatial density, scenario metadata (Drone vs CCTV, location context), and pre-existing zone-violation flags (if present) into a 0.0–100.0 score mapped to 4 threat levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### Rationale
- **Contextual Intelligence**: Per `constitution.md` Section 3 and `architecture.md` Section 9, threat scoring must aggregate contextual signals rather than marking any single object class (e.g., `car` or `person`) inherently dangerous.
- **Deterministic Math**: Formulates threat scores repeatably and explainably:
  $$T = \min\left(100.0, \sum w_{\text{class}} \cdot C_{\text{class}} + w_{\text{count}} \cdot N + w_{\text{context}} \cdot S_{\text{meta}}\right)$$
- **Scope Boundary Compliance**: Feature 002 excludes polygon geometric calculations for restricted zones. If a zone flag is provided in the input metadata, `ThreatScoringService` applies its configured signal weight without executing polygon math.

### Alternatives Considered
- **Hardcoded class-to-threat map (e.g. Person = HIGH)**: Rejected because routine perimeter monitoring includes authorized personnel and vehicles.
- **Real-time polygon point-in-polygon math**: Postponed to video/zone monitoring feature per user specifications.

---

## 3. Explainable AI (XAI) & SOP Recommendation Engine

### Decision
Implement `ExplainabilityService` in `src/infrastructure/services/explainability.py`. It decomposes the threat score into itemized factor contributions (e.g., `+25.0 due to 4 vehicles detected in high-density cluster`), generates natural language decision summaries, and matches threat levels to Standard Operating Procedure (SOP) action items.

### Rationale
- **Operator Decision Support**: In high-stakes command center environments, security personnel need immediate clarity on *why* an alert was elevated.
- **Standardized SOP Mapping**:
  - `LOW`: Continue routine automated perimeter sweep. Log event to audit history.
  - `MEDIUM`: Monitor subject area. Increase frame sampling and maintain visual tracking.
  - `HIGH`: Alert site duty supervisor. Verify object identity and dispatch nearest mobile unit.
  - `CRITICAL`: Immediately escalate to the designated security supervisor, verify the event, restrict access if authorized by site policy, and follow the organization's emergency response procedure.

### Alternatives Considered
- **Black-box neural network threat classifier**: Rejected due to lack of explainability, failing `constitution.md` requirements.

---

## 4. Built-in Offline Demo Asset Management

### Decision
Organize built-in demo image assets in `data/demo/` structured by platform (`drone/`, `cctv/`) and threat scenarios (`low_threat/`, `medium_threat/`, `high_threat/`). `DemoManager` loads these local files and passes them through the exact production `ImageSurveillanceService` application pipeline.

### Rationale
- **Authentic Pipeline Execution**: Guarantees that built-in demo scenarios test real detection, scoring, XAI, and database persistence rather than returning hardcoded mock UI responses.
- **Offline Reliability**: Satisfies `constitution.md` Section 6 and `architecture.md` Section 14 for internet-free demonstration readiness.

---

## 5. Application Layer Use Case & SQLite Persistence

### Decision
Create `ImageSurveillanceService` in `src/application/image_surveillance_service.py`. It coordinates input validation, object detection, threat scoring, XAI generation, image bounding box annotation, and automatic persistence to SQLite via `IAnalysisRepository` and the existing `DatabaseService`.

### Rationale
- **Use Case Orchestration**: Keeps presentation components (Streamlit pages) lightweight (view rendering only) while backend services remain single-responsibility modules.
- **Automatic Persistence**: Per user requirements, completed analyses persist automatically upon completion so that History, Dashboard, and Analytics reflect new records immediately upon page navigation.
