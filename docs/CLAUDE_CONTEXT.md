# Claude Context Guide & Repository Orientation

This document provides a technical overview of the **AI-Based Multimodal Surveillance System for Threat Detection and Decision Support** repository to assist with inspection, architectural review, and development planning.

---

## 1. Project Overview
- **Project Title**: AI-Based Multimodal Surveillance System for Threat Detection and Decision Support
- **Purpose**: Defensive, human-in-the-loop surveillance decision-support system designed for military perimeters, restricted zones, security access gates, and facility monitoring.
- **Key Capability**: Integrates YOLOv8 object detection on KIIT-MiTA military classes, video multi-object IoU tracking, trajectory/displacement analysis, evidence-based contextual threat scoring, Explainable AI (XAI) rationale generation, SQLite persistence, and human analyst audit workflows into a Streamlit intelligence workstation.

---

## 2. Architecture & Directory Structure
The repository follows Layered Domain-Driven Design (DDD):

```
src/
├── domain/                      # Core entities, value objects, interfaces, enums
│   ├── entities.py              # DetectionResult, VideoAnalysisResult, ThreatAssessmentResult, etc.
│   ├── interfaces.py            # Abstract service interfaces (IVideoSurveillanceService, etc.)
│   ├── enums.py                 # Platform, ThreatLevel, AnalystReviewStatus
│   └── exceptions.py            # Domain-specific exceptions
├── core/                        # Infrastructure wiring & core utilities
│   ├── di_container.py          # Central singleton DIContainer
│   ├── config.py                # ConfigurationService loading settings.json / env
│   ├── logger.py                # System logging setup
│   └── exceptions.py            # System level exceptions
├── application/                 # Use case application services
│   ├── image_surveillance_service.py     # Image analysis orchestrator
│   ├── video_surveillance_service.py     # Video analysis orchestrator (sampling, tracking)
│   ├── contextual_assessment_service.py  # Spatial zone & contextual assessment
│   └── analyst_review_service.py         # Human analyst review & audit history manager
├── infrastructure/              # Concrete service implementations & database
│   ├── services/
│   │   ├── yolo_detection.py             # YoloDetectionService wrapping Ultralytics YOLOv8
│   │   ├── iou_tracking.py               # IoUTrackingService for multi-object tracking
│   │   ├── threat_scoring.py             # ThreatScoringService (+5 / +65 / +20 evidence scoring)
│   │   ├── explainability.py             # ExplainabilityService generating XAI rationales & SOPs
│   │   ├── spatial_zone_evaluator.py     # Point-in-polygon ray-casting spatial evaluator
│   │   ├── video_processing.py           # OpenCV frame extraction & video validation
│   │   └── demo_manager.py               # Built-in offline demo scenario asset manager
│   └── database/
│       ├── database.py                   # SQLite DatabaseService connection manager
│       └── repositories.py               # AnalysisRepository, AnalystReviewRepository, etc.
└── ui/                          # Streamlit front-end presentation layer
    ├── app.py                   # Entrypoint launcher
    ├── pages/
    │   ├── dashboard.py         # Primary Workspace (Image & Video analysis intelligence UI)
    │   ├── analyst_review_page.py # Human Analyst Review & Audit History workstation
    │   └── system_health.py     # System health and diagnostic monitoring
    └── components/              # UI widgets, metrics, banners, and layout helpers
```

---

## 3. Important Source Files Reference
- `src/core/di_container.py`: DI container resolving all singletons and repositories.
- `src/application/image_surveillance_service.py`: Orchestrates single image processing pipeline.
- `src/application/video_surveillance_service.py`: Orchestrates video frame sampling, tracking, and threat assessment. Includes `process_video_analysis(request)` and `process_video(request)` alias.
- `src/infrastructure/services/yolo_detection.py`: Loads YOLO model lazily (`data/models/yolov8n_kiit_mita.pt`).
- `src/infrastructure/services/iou_tracking.py`: Implements IoU multi-object tracking across video frame samples.
- `src/infrastructure/services/threat_scoring.py`: Implements evidence-based threat scoring rules.
- `src/infrastructure/services/explainability.py`: Builds XAI natural language summary and SOP recommendations.
- `src/infrastructure/services/demo_manager.py`: Manages offline demo images (`DEMO_SCENARIOS`) and demo videos (`DEMO_VIDEO_SCENARIOS`).

---

## 4. Detection Pipeline
- **Model Checkpoint**: `data/models/yolov8n_kiit_mita.pt` (YOLOv8 Nano trained on KIIT-MiTA).
- **Target Classes (7 Military Classes)**:
  1. `Artilary`
  2. `Missile`
  3. `Radar`
  4. `M. Rocket Launcher`
  5. `Soldier`
  6. `Tank`
  7. `Vehicle`
- **Default Confidence Threshold**: `0.25`

---

## 5. Video Pipeline & Tracking
- **Validation**: Enforces maximum video duration of 120 seconds (`VideoProcessingService`).
- **Frame Sampling**: Extracts frames at specified target FPS (`target_sample_fps=5`).
- **IoU Tracking (`IoUTrackingService`)**:
  - Computes Intersection-over-Union (IoU) between bounding boxes in frame $t$ and active tracks from frame $t-1$.
  - Assigns persistent `track_id` numbers.
  - Updates total pixel displacement across frames.
  - Classifies movement state: `STATIONARY` if displacement $< 15\text{px}$, `MOVING` if displacement $\ge 15\text{px}$.
  - Determines cardinal trajectory direction (North, South, East, West, etc.).

---

## 6. Threat Scoring Formula (`src/infrastructure/services/threat_scoring.py`)
The threat score is calculated based on verified contextual evidence:
1. **Detections Present**: `+5.0` baseline observation points. (Zero detections = `0.0`).
2. **Restricted Zone Violation Signal (`zone_violation_flag`)**: `+65.0` points.
3. **Unauthorized Access Breach Signal (`unauthorized_access_signal`)**: `+20.0` points.
4. **Final Score Calculation**: $S = \min(100.0, \max(0.0, S_{\text{base}} + S_{\text{zone}} + S_{\text{access}}))$

### Threat Level Boundaries:
- `0.0 - 24.9`: `LOW`
- `25.0 - 49.9`: `MEDIUM`
- `50.0 - 74.9`: `HIGH`
- `75.0 - 100.0`: `CRITICAL`

*Note: Object class identity alone (e.g. Tank vs Soldier) does NOT add arbitrary threat score deltas in this baseline model to prevent false alarms during routine military patrols.*

---

## 7. Persistence & Human Analyst Review
- **Database**: SQLite database stored at `data/surveillance.db`.
- **Tables**: `analyses`, `alerts`, `analyst_reviews`, `review_audit_history`, `system_settings`.
- **Analyst Workflow**: Analyst can transition review status (`PENDING_REVIEW` → `ACKNOWLEDGED` → `VERIFIED_THREAT` / `FALSE_POSITIVE` / `ESCALATED`) with notes. Review status changes are tracked in audit history without modifying the original AI threat score.

---

## 8. Test Suite & Verification Status
- **Test Command**: `PYTHONPATH=. pytest tests/`
- **Results**: 65 out of 65 tests passing cleanly across unit, integration, and UI tests.
- **Test Coverage**: Covers DIContainer, Repositories, Database, Image Pipeline, Video Pipeline, IoU Tracking, Spatial Zone Evaluation, Threat Scoring, Explainability, Analyst Review, and UI rendering.

---

## 9. Important Design Decisions & Files Not To Modify Without Care
- `src/domain/interfaces.py`: Core domain interfaces; keep `process_video` alias intact.
- `src/infrastructure/services/threat_scoring.py`: Baseline evidence formula must be preserved unless explicitly tasked to evolve threat rules.
- `data/models/yolov8n_kiit_mita.pt`: Verified baseline YOLO model weights.

---

## 10. Recommended Areas for Future Rebuild / Enhancement
1. **Interactive Spatial Zone Polygon Drawer**: Allow operators to draw custom 2D polygon zones directly on Streamlit video frames.
2. **Live RTSP Stream Processing**: Add async streaming worker threads for RTSP / CCTV live camera feeds.
3. **Behavioral Anomaly & Heatmap Analytics**: Integrate movement trajectory heatmaps and velocity vector anomaly detection.
