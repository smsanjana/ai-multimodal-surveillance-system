# Research & Design Decisions: Feature 003 — Military Object Detection Integration

**Feature**: [specs/003-military-object-detection/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)  
**Date**: 2026-09-13

---

## 1. Technical Context & Overview

Feature 003 integrates the fine-tuned **KIIT-MiTA YOLOv8n model** (`data/models/yolov8n_kiit_mita.pt`) into the AI Surveillance Command Center's existing image analysis pipeline.

### Target Objectives
1. Replace standard COCO detection weights (`yolov8n.pt`) with domain-specific military weights (`yolov8n_kiit_mita.pt`) for the surveillance workflow.
2. Support 7 military target classes: `Artilary`, `Missile`, `Radar`, `M. Rocket Launcher`, `Soldier`, `Tank`, `Vehicle`.
3. Provide externalized configuration for model path (`data/models/yolov8n_kiit_mita.pt`) and confidence threshold (`0.25`).
4. Display dual image outputs in the Surveillance UI (original clean image + annotated detection overlay).
5. Maintain strict decoupling between object detection observations and threat score evaluation.
6. Handle missing model weights or inference errors gracefully without showing stack traces in the UI.

---

## 2. Research & Key Decisions

### Decision 1: Model Loading & Singleton Cache Management
* **Option A**: Reload YOLO model on every incoming image request.
* **Option B**: Maintain a thread-safe singleton model instance keyed by `model_path` in `YoloDetectionService`.
* **Selected**: **Option B**.
* **Rationale**: Re-loading YOLO weights (~6MB) on every frame/image adds ~300-500ms latency per request. Storing a lazy singleton instance in memory provides $<10\text{ms}$ inference latency on local CPU/MPS while preserving offline performance.

### Decision 2: Centralized Model Configuration
* **Option A**: Hardcode `data/models/yolov8n_kiit_mita.pt` in `YoloDetectionService.__init__`.
* **Option B**: Externalize model path and default confidence threshold in `src/core/config.py` (`Config.YOLO_MODEL_PATH`, `Config.YOLO_CONF_THRESHOLD`), with `YoloDetectionService` reading from config or receiving via Dependency Injection.
* **Selected**: **Option B**.
* **Rationale**: Fully compliant with Project Constitution Principle 2 (Centralized Configuration) and Clean Architecture. Allows easy model swapping or path adjustment in settings without code changes.

### Decision 3: Dual-Image Preservation & UI Layout
* **Option A**: Overwrite original image with annotations only.
* **Option B**: Preserve both original image and annotated detection image in `SurveillanceAnalysis` domain entity, database schema, and UI render deck.
* **Selected**: **Option B**.
* **Rationale**: Fulfills FR-006 and User Story 1. Allows security operators to inspect raw un-annotated surveillance imagery alongside the AI detection overlay in side-by-side columns or tabbed views.

### Decision 4: Class Index & Label Mapping
* **Option A**: Hardcode custom class mapping dictionary in Python code.
* **Option B**: Consume `result.names` directly from the Ultralytics model instance metadata, falling back to a canonical 7-class list if names dict is missing.
* **Selected**: **Option B**.
* **Rationale**: The fine-tuned KIIT-MiTA `.pt` weights store the 7 class names (`0: Artilary`, `1: Missile`, `2: Radar`, `3: M. Rocket Launcher`, `4: Soldier`, `5: Tank`, `6: Vehicle`) inside the PyTorch state dict metadata. `result.names` automatically maps class IDs deterministically.

---

## 3. Risk Mitigation & Error Boundaries

| Risk | Mitigation Strategy |
| :--- | :--- |
| **Missing Model File (`yolov8n_kiit_mita.pt`)** | `YoloDetectionService._get_model()` checks `os.path.exists()` and raises `ModelLoadError`. UI catches `ModelLoadError` and presents a friendly alert banner without stack traces. |
| **Out-of-Memory / Inference Crash** | `YoloDetectionService.detect()` wraps model execution in `try-except` block and raises domain-specific `AnalysisProcessingError`. |
| **Low-Confidence Clutter** | Configurable confidence threshold (`0.25` default) filters out noisy detections prior to bounding box drawing and threat scoring. |
| **CCTV Imagery Misclassification** | Explicit UI/Spec disclaimer clarifying that KIIT-MiTA model is validated for drone imagery. Ground CCTV scenarios use appropriate thresholding and neutral evidence scoring. |
