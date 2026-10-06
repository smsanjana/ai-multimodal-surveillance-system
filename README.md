# AI-Based Multimodal Surveillance System for Threat Detection and Decision Support

## 1. Project Purpose
This project is a defensive, human-in-the-loop surveillance decision-support system designed for restricted military areas, border/perimeter sectors, security access gates, and controlled facilities. 

The core system pipeline integrates:
`SURVEILLANCE IMAGE/VIDEO` → `OBJECT DETECTION` → `OBJECT TRACKING` → `MOVEMENT / TRAJECTORY ANALYSIS` → `RESTRICTED-ZONE / BORDER CONTEXT` → `BEHAVIOR & INTRUSION ANALYSIS` → `EVIDENCE EXTRACTION` → `THREAT ASSESSMENT` → `EXPLAINABILITY` → `HUMAN ANALYST REVIEW`

---

## 2. Current Status Overview
- **YOLOv8 Military Object Detection**: `IMPLEMENTED`
- **Single Image Analysis Pipeline**: `IMPLEMENTED`
- **Video Analysis & Frame Sampling Pipeline**: `IMPLEMENTED`
- **Multi-Object IoU Tracking & Trajectory Calculation**: `IMPLEMENTED`
- **Evidence-Based Contextual Threat Scoring (+5 / +65 / +20)**: `IMPLEMENTED`
- **Explainable AI (XAI) Rationale & SOP Generator**: `IMPLEMENTED`
- **Human Analyst Review & Audit Log History**: `IMPLEMENTED`
- **Spatial Polygon Restricted Zone Boundary Monitoring**: `PARTIALLY IMPLEMENTED`
- **Real-Time Automated Camera Stream Ingestion**: `PLANNED`
- **Advanced Behavioral Intention Classification**: `PLANNED`

---

## 3. Technology Stack
- **Language**: Python 3.11
- **Computer Vision & Detection**: PyTorch, Ultralytics YOLOv8, OpenCV, NumPy
- **User Interface**: Streamlit
- **Persistence**: SQLite (via standard Python `sqlite3`), Repository Pattern
- **Testing**: PyTest (`pytest`)
- **Architecture**: Clean Architecture / Layered Domain-Driven Design (Domain, Application, Infrastructure, UI)

---

## 4. Repository Structure
```
ai_p2/
├── app.py                      # Root Streamlit app launcher
├── config/                     # System configuration defaults (settings.json)
├── data/
│   ├── demo/                   # Built-in offline demo image & video scenarios
│   │   ├── cctv/               # CCTV sample images and video feeds
│   │   └── drone/              # Drone aerial surveillance images and video feeds
│   ├── datasets/               # Dataset configuration files (.yml) & manifests
│   │   └── military/           # KIIT-MiTA dataset configuration definitions
│   └── models/                 # Model checkpoints (yolov8n_kiit_mita.pt)
├── docs/                       # Architecture documentation and Claude context guide
│   └── CLAUDE_CONTEXT.md       # Comprehensive context document for Claude
├── scratch/                    # Verification scripts & training benchmarks
├── specs/                      # Feature specifications & design artifacts
├── src/                        # Primary application source code
│   ├── application/            # Application layer services (Image, Video, Contextual, Analyst)
│   ├── core/                   # DI Container, Configuration, Logger, Exceptions
│   ├── domain/                 # Domain Entities, Interfaces, Enums
│   ├── infrastructure/         # YOLO, Tracking, Threat Scoring, XAI, Repositories, Database
│   └── ui/                     # Streamlit UI pages & components
└── tests/                      # PyTest unit & integration test suites
```

---

## 5. Dataset & Seven KIIT-MiTA Classes
The model is trained on the **KIIT-MiTA** (KIIT Military Target Analysis) dataset.
The system detects **7 military object classes**:
1. `Artilary`
2. `Missile`
3. `Radar`
4. `M. Rocket Launcher`
5. `Soldier`
6. `Tank`
7. `Vehicle`

Dataset configurations are stored under `data/datasets/military/KIIT-MiTA/KIIT-MiTA.yml` and `data/datasets/military/KIIT-MiTA_cleaned/KIIT-MiTA.yml`.

---

## 6. Model Information
- **Baseline Checkpoint**: `data/models/yolov8n_kiit_mita.pt` (YOLOv8 Nano trained on KIIT-MiTA)
- **Pretrained Checkpoints**: `yolov8n.pt`, `yolov8s.pt`
- **Experimental Runs**: `data/models/experiments/exp01_clean_yolov8n/` and `data/models/experiments/exp02_clean_yolov8s/`

---

## 7. Key Pipelines & Architecture

### Image Surveillance Pipeline (`IMPLEMENTED`)
Located in `src/application/image_surveillance_service.py`. Validates input images, runs YOLOv8 object detection, renders bounding boxes, evaluates contextual threat scoring, generates XAI rationale, and persists results to SQLite.

### Video Surveillance Pipeline (`IMPLEMENTED`)
Located in `src/application/video_surveillance_service.py`. Enforces max duration (120s), extracts sampled frames, tracks targets across frames using IoU tracking (`IoUTrackingService`), calculates movement state (STATIONARY/MOVING), displacement, and direction, extracts scenario context, and persists video analysis records.

### Multi-Object Tracking (`IMPLEMENTED`)
Located in `src/infrastructure/services/iou_tracking.py`. Uses Intersection-over-Union (IoU) spatial matching across sampled video frames to assign persistent track IDs, update target positions, calculate total pixel displacement, and determine trajectory direction (e.g. North, East).

### Threat Scoring Logic (`IMPLEMENTED`)
Located in `src/infrastructure/services/threat_scoring.py`. Implements evidence-based scoring:
- **Detections Present**: `+5.0` baseline observation points
- **Restricted Zone Violation (`zone_violation_flag`)**: `+65.0` points
- **Unauthorized Access Signal (`unauthorized_access_signal`)**: `+20.0` points
- **Bounded Range**: `0.0 - 100.0` points
- **Threat Levels**:
  - `< 25.0`: `LOW`
  - `25.0 - 49.9`: `MEDIUM`
  - `50.0 - 74.9`: `HIGH`
  - `>= 75.0`: `CRITICAL`

### Human Analyst Review & Audit (`IMPLEMENTED`)
Located in `src/application/analyst_review_service.py` and `src/infrastructure/database/repositories.py`. Tracks analyst review status (`PENDING_REVIEW`, `ACKNOWLEDGED`, `FALSE_POSITIVE`, `ESCALATED`, `VERIFIED_THREAT`), log notes, analyst IDs, and complete audit history transitions without mutating underlying AI detection threat scores.

---

## 8. Installation & Running

### Requirements
- Python 3.11+
- Virtual environment recommended (`venv`)

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Streamlit Application
```bash
streamlit run app.py
```
Or:
```bash
streamlit run src/ui/app.py
```

### Running Test Suite
```bash
PYTHONPATH=. pytest tests/
```

---

## 9. Known Limitations & Planned Areas
- **Spatial Polygon Ray-Casting**: Synthetic demo scenario metadata currently supplies zone violation signals for demo feeds; polygon point-in-polygon ray-casting evaluator is implemented in `src/infrastructure/services/spatial_zone_evaluator.py` but UI drawing of custom polygon coordinates on video streams is planned for future extension.
- **RTSP / Live Streaming**: System currently processes uploaded MP4/AVI videos and offline demo video feeds. Live RTSP/WebRTC stream ingestion is planned.
