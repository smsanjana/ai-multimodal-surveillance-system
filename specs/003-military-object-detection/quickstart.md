# Quickstart & Validation Guide: Feature 003 — Military Object Detection Integration (Revised)

**Feature**: [specs/003-military-object-detection/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)  
**Date**: 2026-09-13 (Updated: 2026-09-13)

---

## 1. Environment & Prerequisites

1. **Local Model Weights**:
   Verify that fine-tuned weights file `yolov8n_kiit_mita.pt` exists in `data/models/`:
   ```bash
   ls -lh data/models/yolov8n_kiit_mita.pt
   ```
   *Expected*: `yolov8n_kiit_mita.pt` (~6.2 MB). Default path configured via `Config.YOLO_MODEL_PATH`.

2. **Dependencies**:
   Ensure virtual environment is activated and required packages (`ultralytics`, `torch`, `opencv-python`, `pytest`, `streamlit`) are installed.

---

## 2. Automated Test Verification

### Fast Mocked Unit Tests
Unit tests use mocked YOLO detector stubs for high-speed execution without model weight dependencies:
```bash
pytest tests/unit/test_yolo_detection.py -v
```
*Validates*:
- Class ID to class-name mapping ($0-6$)
- Confidence threshold filtering (`0.25` default)
- Missing model file error handling (`ModelLoadError`)
- Invalid/corrupt model error handling
- Inference failure handling (`AnalysisProcessingError`)
- Annotation drawing logic

### Real Model Integration Test
Integration test loads the actual `data/models/yolov8n_kiit_mita.pt` weights and processes a real military drone image:
```bash
pytest tests/integration/test_pipeline.py -v
```
*Validates*:
- Real YOLO model initialization from `Config.YOLO_MODEL_PATH`
- End-to-end detection, neutral threat scoring, and SQLite persistence

---

## 3. Manual Verification Steps

1. **Launch Streamlit App**:
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Surveillance Page**:
   - Select **Surveillance** from the left navigation bar.

3. **Execute Military Drone Scenario**:
   - Choose a Drone scenario (e.g. `Drone Restricted Area Intrusion` or `Drone Normal Highway Patrol`).
   - Click **Run Analysis**.

4. **Verify Dual-Image Display**:
   - Confirm that both the **Original Input Image** and the **Annotated Detection Result Image** (with bounding boxes, military target class labels like `Tank`, `Missile`, `Soldier`, and confidence percentages) are displayed.

5. **Verify Persistence & Navigation**:
   - Navigate to **History** and verify the analysis is recorded with metadata and detection JSON.
   - Verify all 7 navigation pages (**Dashboard**, **Surveillance**, **Analytics**, **History**, **Reports**, **Settings**, **About**) continue functioning cleanly.
