# Implementation Plan: Image Surveillance Processing

**Branch**: `002-image-surveillance-processing` | **Date**: 2026-09-13 | **Spec**: [spec.md](file:///Users/sanjana/Documents/ai_p2/specs/002-image-surveillance-processing/spec.md)

**Input**: Feature specification from `specs/002-image-surveillance-processing/spec.md`

## Summary

Upgrade the Surveillance command deck from foundation UI placeholders to production computer vision image analysis. The feature implements offline object detection using local YOLOv8 weights (`data/models/yolov8n.pt`), image bounding box annotation, multi-signal contextual threat scoring (0–100 mapped to LOW, MEDIUM, HIGH, CRITICAL), Explainable AI (XAI) rationale generation, Standard Operating Procedure (SOP) recommended actions, built-in offline Drone and CCTV demo scenarios, and automatic SQLite persistence with cross-page metric synchronization (History, Dashboard, Analytics).

---

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Streamlit (1.63.0), Ultralytics YOLOv8, PyTorch, OpenCV (`opencv-python`), Plotly (7.0.0), Pydantic (2.13.5), PyYAML  
**Storage**: SQLite database via existing `DatabaseService` and Repository pattern  
**Testing**: `pytest` test suite (`python -m pytest tests/ -v`)  
**Target Platform**: Local macOS / Linux CPU control-room workstations (100% offline capable)  
**Project Type**: Streamlit Web Application / AI Command Center  
**Performance Goals**: Image object detection, threat scoring, XAI, and annotation complete in under **3.0 seconds** per 1280x720 frame on local CPU (excluding initial model load).  
**Constraints**: 100% offline execution; local model weights at `data/models/yolov8n.pt` (no auto downloads); no video processing, temporal tracking, RTSP streams, or restricted-zone polygon calculations in Feature 002.  
**Scale/Scope**: 6 built-in demo image scenarios (Drone & CCTV); single/uploaded surveillance image processing.  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Clean Architecture Scoping**: UI presentation code (`pages/surveillance.py`) delegates processing exclusively to `ImageSurveillanceService` and DI Container services. No detection loops or threat math in Streamlit files.
- [x] **AI Engineering Decoupling**: `AbstractDetectionService` hides `ultralytics` implementation details behind DTO interface contracts (`DetectionResult`).
- [x] **Explainable AI (XAI)**: `ExplainabilityService` generates itemized factor attributions and natural language rationale for every assigned threat level.
- [x] **Full Offline Autonomy**: Pre-loaded model weights (`data/models/yolov8n.pt`) and local demo assets (`data/demo/`) ensure 0 external network requests.
- [x] **Automatic Persistence**: Completed runs automatically save to SQLite via `IAnalysisRepository` and sync across Dashboard, History, and Analytics.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-image-surveillance-processing/
├── plan.md              # Implementation Plan (this file)
├── research.md          # Technical decisions and rationale
├── data-model.md        # Entities, DTOs, SQLite schemas, state transitions
├── quickstart.md        # End-to-end runnable validation guide
├── contracts/           # Domain & Application service contracts
│   └── image_surveillance_contract.md
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── config.py              # YAML configuration loader
│   ├── database.py            # SQLite schema initialization
│   ├── di_container.py        # Dependency Injection Container
│   ├── exceptions.py          # Centralized domain exceptions
│   └── logger.py              # Structured logging
├── domain/
│   ├── entities.py            # DTOs (DetectionResult, ThreatAssessmentResult, etc.)
│   └── interfaces.py          # Domain contracts (AbstractDetectionService, etc.)
├── application/
│   └── image_surveillance_service.py # Image surveillance use case orchestrator
├── infrastructure/
│   ├── database/
│   │   └── repositories.py    # SQLite repository persistence
│   └── services/
│       ├── yolo_detection.py  # AbstractDetectionService implementation
│       ├── threat_scoring.py  # AbstractThreatScoringService implementation
│       ├── explainability.py  # AbstractExplainabilityService implementation
│       └── demo_manager.py    # Offline demo scenario asset manager
└── ui/
    ├── components.py          # Reusable UI widgets
    ├── styles.py              # Dark theme CSS styling
    └── pages/
        ├── surveillance.py    # Unified Surveillance Command Deck (modified by Feature 002)
        ├── dashboard.py       # Executive Dashboard metrics
        ├── analytics.py       # Analytics trend charts
        ├── history.py         # Searchable audit log
        ├── reports.py         # Reports page (retained from Feature 001)
        ├── settings.py        # Settings page (retained from Feature 001)
        └── about.py           # About page (retained from Feature 001)
```

**Structure Decision**: Clean Architecture single project structure with decoupled Presentation (`src/ui`), Application (`src/application`), Domain (`src/domain`), Infrastructure (`src/infrastructure`), and Core (`src/core`) layers. Feature 002 modifies `pages/surveillance.py` and adds supporting backend image-processing services while preserving all existing Feature 001 UI pages (`reports.py`, `settings.py`, `about.py`).

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| *None* | *All decisions strictly adhere to constitution.md and architecture.md* | *N/A* |
