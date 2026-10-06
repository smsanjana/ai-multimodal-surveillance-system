# Implementation Plan: Feature 003 — Military Object Detection Integration (Revised)

**Branch**: `003-military-object-detection` | **Date**: 2026-09-13 (Updated: 2026-09-13) | **Spec**: [spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)

**Input**: Feature specification from `specs/003-military-object-detection/spec.md`

## Summary

Feature 003 replaces the pre-trained COCO object detector (`data/models/yolov8n.pt`) with the domain-specific fine-tuned **KIIT-MiTA military object detector** (`data/models/yolov8n_kiit_mita.pt`). It enables automated detection, bounding box rendering, confidence tagging, and structured class mapping for 7 military target classes (`Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`). 

The model path (`YOLO_MODEL_PATH = "data/models/yolov8n_kiit_mita.pt"`) and confidence threshold (`YOLO_CONFIDENCE_THRESHOLD = 0.25`) are externalized through `src/core/config.py` as defaults, allowing overrides via environment variables or configuration settings without modifying application/domain code.

The Surveillance result view is updated to preserve and display both clean original and annotated detection images side-by-side. Fast unit tests use mocked/stubbed detector behavior, while a dedicated end-to-end integration test verifies real model inference on a built-in military demo image.

---

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Ultralytics YOLOv8, PyTorch, OpenCV (`cv2`), Streamlit, Pydantic, SQLite  
**Storage**: SQLite (`analyses` table via `DatabaseService`), Local disk for model weights and annotated image artifacts  
**Testing**: Pytest (`tests/`) — Fast mocked unit tests + 1 real model integration test  
**Target Platform**: macOS (Apple Silicon MPS / CPU) / Linux  
**Project Type**: Streamlit Desktop / Web Surveillance Application  
**Performance Goals**: $< 50\text{ms}$ inference per image on Apple Silicon MPS/CPU  
**Constraints**: 100% offline local model execution, no model downloading at runtime, zero UI stack traces on missing model errors, single unified 7-page navigation  
**Scale/Scope**: Single & batch surveillance image processing across Drone & CCTV modalities  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Modular Development & Clean Architecture**: Presentation (`ui/`), Application (`application/`), Domain (`domain/`), Infrastructure (`infrastructure/`) strictly segregated.
- [x] **Separation of Concerns & Zero UI Business Logic**: Detection execution remains in `YoloDetectionService` infrastructure service; Streamlit scripts strictly render state.
- [x] **Centralized Configuration**: Model path (`YOLO_MODEL_PATH = "data/models/yolov8n_kiit_mita.pt"`) and confidence threshold (`YOLO_CONFIDENCE_THRESHOLD = 0.25`) externalized in `src/core/config.py` with override capability.
- [x] **Offline Autonomy**: Local weight file loading with zero network calls.
- [x] **7-Page Navigation Preservation**: Dashboard, Surveillance, Analytics, History, Reports, Settings, About fully preserved.
- [x] **Threat Assessment Neutrality**: Object class identity alone does not dictate `HIGH` or `CRITICAL` threat level.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-military-object-detection/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 research & design decisions
├── data-model.md        # Phase 1 data models & schema
├── quickstart.md        # Phase 1 validation & quickstart guide
└── contracts/
    └── detection_service_contract.md # Detection service interface contract
```

### Source Code Layout

```text
src/
├── core/
│   ├── config.py              # Add YOLO_MODEL_PATH & YOLO_CONFIDENCE_THRESHOLD config settings with override support
│   ├── di_container.py        # DI container wiring for YoloDetectionService with Config parameters
│   └── exceptions.py          # ModelLoadError, AnalysisProcessingError definitions
├── domain/
│   ├── entities.py            # BoundingBox, DetectionResult, SurveillanceAnalysis
│   └── interfaces.py          # AbstractDetectionService interface
├── infrastructure/
│   └── services/
│       ├── yolo_detection.py  # YoloDetectionService (KIIT-MiTA weights, 7 classes)
│       └── demo_manager.py    # Drone demo scenarios configuration
├── application/
│   └── image_surveillance_service.py # ImageSurveillanceService orchestration
└── ui/
    └── pages/
        ├── surveillance.py    # Surveillance page (Dual-image display: Original + Annotated)
        └── dashboard.py, analytics.py, history.py, reports.py, settings.py, about.py

tests/
├── unit/
│   └── test_yolo_detection.py # Fast unit tests with mocked/stubbed YOLO detector
└── integration/
    └── test_pipeline.py       # Real integration test with actual yolov8n_kiit_mita.pt model
```

**Structure Decision**: Single project clean architecture directory structure under `src/` and `tests/`.

---

## Testing Strategy

1. **Fast Mocked Unit Tests** (`tests/unit/test_yolo_detection.py`):
   - Use `unittest.mock` / stubs to mock `ultralytics.YOLO`.
   - Test class ID ($0-6$) to class-name mapping (`Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`).
   - Test confidence threshold filtering (`0.25`).
   - Test missing model file handling (`ModelLoadError`).
   - Test invalid/corrupt model handling.
   - Test inference execution error handling (`AnalysisProcessingError`).
   - Test OpenCV annotation bounding box rendering.

2. **Real Integration Test** (`tests/integration/test_pipeline.py`):
   - At least one test loads the actual `data/models/yolov8n_kiit_mita.pt` model weights.
   - Processes a real built-in military drone image.
   - Verifies end-to-end pipeline execution: Detection $\to$ Neutral Threat Assessment $\to$ SQLite Persistence.
