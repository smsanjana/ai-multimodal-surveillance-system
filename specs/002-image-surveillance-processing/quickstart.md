# Quickstart & Validation Guide: Image Surveillance Processing

**Feature Identifier**: `specs/002-image-surveillance-processing`  
**Date**: 2026-09-13  
**Status**: Draft  

---

## 1. Prerequisites & Environment Setup

Ensure the virtual environment is activated and local model weights are present.

### Prerequisites Check
- Python 3.10+ virtual environment (`venv/`)
- Installed packages: `streamlit`, `ultralytics`, `torch`, `opencv-python`, `plotly`, `pydantic`, `pyyaml`
- Local model file: `data/models/yolov8n.pt` must exist locally (no automatic downloads)

### Model Weights Verification Command
```bash
python3 -c "import os; assert os.path.exists('data/models/yolov8n.pt'), 'Local model file data/models/yolov8n.pt missing!'"
```

---

## 2. Automated Test Verification

Run the test suite to verify unit logic for image validation, YOLO object detection, threat scoring, XAI explanations, repository persistence, and DI container resolution.

```bash
python -m pytest tests/ -v
```

### Expected Output
- All unit tests pass (`OK`).
- Test suite verifies `YoloDetectionService`, `ThreatScoringService`, `ExplainabilityService`, `ImageSurveillanceService`, and SQLite persistence.

---

## 3. Interactive UI Validation Scenarios

Launch the Streamlit Surveillance Command Center application:

```bash
venv/bin/streamlit run app.py
```

### Validation Scenario 1: Built-in Drone Demo Image Analysis
1. Navigate to 📡 **Surveillance** in the sidebar.
2. Select **Built-in Demo** under Step 1 (Choose Source).
3. Select **Drone** under Step 2 (Choose Platform).
4. Select **Image** under Step 3 (Choose Input Type).
5. Pick a scenario (e.g. `Drone High Threat Intrusion`) under Step 4.
6. Click **Run Surveillance Analysis**.
7. **Verification**:
   - Original and annotated images appear side-by-side.
   - Bounding boxes, class labels, and confidence tags overlay detected objects.
   - Processing latency is displayed in milliseconds and should remain below 3000 ms for a 1280x720 image on the target CPU, excluding one-time model loading.
   - Threat Level badge (e.g. `HIGH` 🟠) and score (0–100) render with XAI explanation.
   - SOP Recommended Actions render.

### Validation Scenario 2: Built-in CCTV Demo Image Analysis
1. Select **Built-in Demo** → **CCTV** → **Image** → `CCTV Unauthorized Access`.
2. Click **Run Surveillance Analysis**.
3. **Verification**:
   - Processed output renders with annotated bounding boxes and threat level badge.

### Validation Scenario 3: Custom User Image Upload
1. Select **Upload Media** → **Drone** or **CCTV** → **Image**.
2. Upload a standard `.jpg` or `.png` surveillance image.
3. Click **Run Surveillance Analysis**.
4. **Verification**:
   - Analysis executes successfully, bounding boxes and threat scores render.

### Validation Scenario 4: Cross-Page Data Persistence Sync
1. Complete any image analysis run on the Surveillance page.
2. Navigate to 📁 **History** page.
   - **Verification**: The newly processed analysis record is listed in the history table with matching timestamp, threat level, and metadata.
3. Navigate to 🏠 **Dashboard** page.
   - **Verification**: Today's analysis count and threat metrics reflect the newly persisted run.
4. Navigate to 📊 **Analytics** page.
   - **Verification**: Threat trend charts and object detection breakdown tables include data from the new run.
