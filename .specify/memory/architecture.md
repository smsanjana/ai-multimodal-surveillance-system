# Technical Architecture Specification

# AI-Based Multimodal Surveillance System for Threat Detection and Decision Support

> **Document Type:** Project-Wide System Architecture Specification  
> **Governance:** Compliant with [`constitution.md`](file:///Users/sanjana/Documents/ai_p2/constitution.md)  
> **Lifecycle Standard:** SpecKit Architectural Blueprint  

---

## 1. Project Vision & Capability Scope

The **AI-Based Multimodal Surveillance System for Threat Detection and Decision Support** is designed as a unified, enterprise-grade AI Surveillance Command Center. It provides real-time and offline analysis of surveillance imagery and video streams, automated object detection, multi-object tracking, spatial movement analysis, restricted-zone monitoring, multi-factor threat scoring, explainable AI (XAI) decision explanations, and actionable operational decision support.

The system is architected as an integrated, production-grade surveillance platform serving defense, border security, industrial facilities, airports, smart cities, and critical infrastructure monitoring.

```
+-----------------------------------------------------------------------------------+
|                            SURVEILLANCE COMMAND CENTER                            |
+-----------------------------------------------------------------------------------+
|  [Image Analysis]  [Video Analysis]  [Live Streams]   [Drone Feeds]   [CCTV Feeds]|
+-----------------------------------------------------------------------------------+
|                     SHARED REUSABLE INTELLIGENCE PIPELINE ENGINE                  |
|  Detection | Tracking | Zone Analysis | Threat Scoring | XAI | Decision Support   |
+-----------------------------------------------------------------------------------+
|                     CORE PLATFORM & OPERATIONAL SERVICES                          |
|  Alerts Manager | Analytics Engine | History Store | Report Engine | Demo Manager |
+-----------------------------------------------------------------------------------+
```

### Core System Capabilities
- **Multimodal Inputs:** Image, Video, and Live Camera Streams (RTSP/Webcam).
- **Platform Agnostic:** Metadata-aware processing for Drone aerial feeds and CCTV fixed-angle perimeter feeds.
- **Computer Vision Pipeline:** YOLOv8 Object Detection, Multi-Object Tracking, Trajectory & Velocity Analysis.
- **Perimeter & Security Intelligence:** Polygon Restricted-Zone Intrusion Monitoring.
- **Decision Intelligence:** Multi-Factor Threat Level Scoring (LOW, MEDIUM, HIGH, CRITICAL), Explainable AI (XAI) feature attribution, and Standard Operating Procedure (SOP) Decision Support.
- **Operational Management:** Real-Time Alerts, Analytics & Trends, Searchable Audit History, PDF/JSON Report Generation, and Built-In Offline Demo Scenarios.

---

## 2. Architectural Style: Modular Clean Architecture

The project strictly follows **Clean Architecture** principles and **Separation of Concerns**. The system is decoupled into five explicit horizontal layers.

```
+-----------------------------------------------------------------------------------+
| 1. PRESENTATION LAYER (Streamlit Pages, Reusable UI Components, Renderers)       |
+-----------------------------------------------------------------------------------+
                                       │ (Calls Use Cases / Services)
                                       ▼
+-----------------------------------------------------------------------------------+
| 2. APPLICATION LAYER (Orchestrators, Workflows, Use Cases, DTOs)                  |
+-----------------------------------------------------------------------------------+
                                       │ (Manipulates Domain Entities & Interfaces)
                                       ▼
+-----------------------------------------------------------------------------------+
| 3. DOMAIN LAYER (Entities, Value Objects, Threat Rules, Domain Contracts)         |
+-----------------------------------------------------------------------------------+
                                       ▲ (Implements Domain Interfaces)
                                       │
+-----------------------------------------------------------------------------------+
| 4. INFRASTRUCTURE LAYER (YOLOv8 Adapter, OpenCV Video, DI Container, Logging)    |
+-----------------------------------------------------------------------------------+
                                       │
                                       ▼
+-----------------------------------------------------------------------------------+
| 5. DATA / PERSISTENCE LAYER (SQLite Database, Repositories, File Storage)          |
+-----------------------------------------------------------------------------------+
```

### Strict Scoping & Isolation Rules
1. **Presentation Layer (Streamlit):** Responsible strictly for rendering UI elements, capturing user inputs, and rendering view state. **Zero business logic, detection loops, or scoring math may exist inside Streamlit page files.**
2. **Application Layer:** Orchestrates the flow of data between UI and Domain Services using Data Transfer Objects (DTOs).
3. **Domain Layer:** Pure Python enterprise business logic (threat formulas, zone intersection math, entity models). Entirely independent of UI frameworks, database adapters, and AI libraries.
4. **Infrastructure Layer:** Implements concrete services (e.g., `YoloDetectionService`, `OpenCVVideoProcessor`). All external dependencies are hidden behind abstract interfaces.
5. **Persistence Layer:** Database access via the Repository Pattern using SQLite. Raw SQL commands are encapsulated within repository classes.

---

## 3. High-Level System Processing Flow

Every input processed by the system follows a standardized sequential flow. Stage execution is adaptive based on input modality (e.g., still images skip temporal tracking).

```
  [Input Source] (Upload / Live / Demo)
        │
        ▼
  [Input Validation] (Format, Resolution, Integrity Check)
        │
        ▼
  [Preprocessing] (Resizing, Normalization, Frame Extraction)
        │
        ▼
  [Object Detection] (Bounding Boxes, Class Labels, Confidence Scores)
        │
        ▼
  [Object Tracking] (Track ID Assignment, Centroid Persistence) ── (Videos / Streams)
        │
        ▼
  [Movement Analysis] (Velocity, Direction, Trajectory Vectors) ── (Videos / Streams)
        │
        ▼
  [Restricted Zone Analysis] (Polygon Intersection, Entry / Exit Events)
        │
        ▼
  [Threat Scoring] (Multi-factor Matrix -> LOW | MEDIUM | HIGH | CRITICAL)
        │
        ▼
  [Explainable AI (XAI)] (Feature Attribution, Natural Language Rationale)
        │
        ▼
  [Decision Support] (SOP Recommendations, Recommended Action Protocols)
        │
        ▼
  [Persistence & Audit Log] (SQLite Event Records & Artifact Storage)
        │
        ├─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
  [Analytics Engine]       [Alert Manager]          [Report Engine]
```

---

## 4. Input Source & Platform Architecture

The input layer unifies diverse input sources and operational platform metadata into a common data pipeline.

### Input Modes
1. **Built-in Demo Mode:** Pre-loaded local scenarios for offline demonstrations and deterministic testing.
2. **User Upload Mode:** Interactive file upload supporting static images (`.jpg`, `.png`) and video files (`.mp4`, `.avi`, `.mov`).
3. **Live Camera Mode:** Real-time stream ingest via RTSP endpoints, Webcams, or IP Camera networks.

### Platform Metadata Abstraction
Drone and CCTV are treated as **contextual platform metadata** attached to the input source, rather than separate AI pipelines.
- **Drone Metadata:** Indicates high-angle aerial perspective, wide field of view, potential camera movement, and thermal/optical parameters.
- **CCTV Metadata:** Indicates fixed perimeter viewpoint, known spatial geometry, and static camera mounting.

```python
class InputContext:
    source_type: InputSourceType  # DEMO, UPLOAD, LIVE
    media_type: MediaType        # IMAGE, VIDEO
    platform: PlatformType        # DRONE, CCTV
    source_path_or_uri: str
    metadata: Dict[str, Any]
```

---

## 5. Surveillance UI Architecture & Guided Workflow

The application implements **ONE single, unified Surveillance workspace** (`pages/surveillance.py`) featuring a guided, progressive workflow. Segregated pages like "Video Detection" or "Drone Analysis" are strictly prohibited.

### Guided Operator Workflow Steps

```
Step 1: Choose Source ─────► [ Built-in Demo | Upload Media | Live Camera ]
        │
        ▼
Step 2: Choose Platform ───► [ Drone | CCTV ]
        │
        ▼
Step 3: Choose Input Type ─► [ Image | Video ]
        │
        ▼
Step 4: Select Input ──────► [ Demo Scenario Picker OR File Uploader OR Camera Config ]
        │
        ▼
Step 5: Run Analysis ──────► [ Trigger Shared Pipeline Engine ]
        │
        ▼
Step 6: View Results ──────► [ Render Progressive Analysis Outputs ]
        │
        ▼
Step 7: Actions & Export ──► [ Save Analysis | Dispatch Alert | Generate PDF Report ]
```

### Progressive UI Disclosure
Controls are rendered contextually based on active wizard selections to prevent UI clutter and reduce operator cognitive load.

---

## 6. Global Navigation Structure

The system enforces a minimal, single-level primary sidebar navigation structure:

```
🏠 Dashboard    ────── Executive Overview & Quick Actions
📡 Surveillance ────── Unified Interactive Analysis Command Deck
📊 Analytics   ────── Historical Trends & Spatial Heatmaps
📁 History     ────── Audit Log & Searchable Event Records
📄 Reports     ────── Report Generator & PDF Exporter
⚙ Settings    ────── Central System & AI Model Configuration
ℹ About       ────── Version Info, System Health & Docs
```

No sub-navigation or extra top-level items are permitted unless formally added via constitution amendment.

---

## 7. Dashboard Architecture

The **Dashboard** serves as an operational executive control panel. It consumes data exclusively through domain services and repository interfaces.

```
+-----------------------------------------------------------------------------------+
| OPERATIONAL STATUS METRIC CARDS                                                   |
| [ Current Threat ]  [ Active Alerts ]  [ Today's Analyses ]  [ Avg Confidence ]   |
+-----------------------------------------------------------------------------------+
| VISUALIZATION PANELS                                                              |
| [ Threat Trend (Plotly) ]  [ Detection Breakdown ]  [ Threat Distribution (Pie) ] |
+-----------------------------------------------------------------------------------+
| OPERATIONAL ACTIVITY & QUICK ACTIONS                                              |
| [ Recent Audit Log Table ]              [ Quick Actions: Run Demo | Upload ]     |
+-----------------------------------------------------------------------------------+
```

- **Metric Cards:** Display real-time system metrics computed by `AnalyticsService` and `AlertService`.
- **Plotly Visualizations:** Dynamic charts for threat trends over time, class detection frequency, and threat severity distribution.
- **Quick Action Triggers:** One-click shortcuts navigating operators directly to specific Surveillance workflow setups.

---

## 8. Surveillance Results Architecture

Results display follows a progressive vertical stack within the Surveillance page after pipeline completion:

```
1. Original Input Media ────── Static Image / Video Player with Source Info
        │
        ▼
2. Processed Media Output ──── Annotated Frame / Rendered Video with Bounding Boxes & Trajectories
        │
        ▼
3. Detection Summary ──────── Detected Class Counts, Confidence Badges, Object Table
        │
        ▼
4. Threat Assessment Panel ── Threat Level Badge (LOW/MED/HIGH/CRIT) & Quantitative Score
        │
        ▼
5. Explainable AI (XAI) ───── Contributing Factors & Natural Language Decision Rationale
        │
        ▼
6. Decision Support (SOP) ──── Recommended Action Plan & Escalation Checklist
        │
        ▼
7. Export & Save Actions ───── [ Save to History ]  [ Generate Incident PDF ]  [ Raise Alert ]
```

---

## 9. Threat Intelligence Architecture

Threat assessment is encapsulated entirely inside `ThreatScoringService`. Threat scoring is deterministic, multi-factor, and fully configurable.

### Multi-Signal Threat Matrix
Threat score $T \in [0, 100]$ is computed using weighted signals:

$$T = w_{\text{class}} \cdot S_{\text{class}} + w_{\text{count}} \cdot S_{\text{count}} + w_{\text{zone}} \cdot S_{\text{zone}} + w_{\text{motion}} \cdot S_{\text{motion}} + w_{\text{density}} \cdot S_{\text{density}}$$

Where:
- $S_{\text{class}}$: Base weight of detected object classes (e.g., person, heavy vehicle, weapon).
- $S_{\text{count}}$: Aggregated object density score.
- $S_{\text{zone}}$: Severity weight of active restricted-zone intrusions.
- $S_{\text{motion}}$: Velocity anomaly and movement trajectory score.
- $S_{\text{density}}$: Spatial crowding index.

### Classification Threshold Mapping
- `0 - 24`: 🟢 **LOW** (Normal activity)
- `25 - 49`: 🟡 **MEDIUM** (Loitering, minor approach)
- `50 - 74`: 🟠 **HIGH** (Restricted area violation, heavy vehicle entry)
- `75 - 100`: 🔴 **CRITICAL** (High-speed perimeter breach, critical asset threat)

### Explainable AI (XAI) Rationale Engine
`ExplainabilityService` maps score components into human-readable explanations:

```python
class ThreatExplanation:
    overall_threat_level: ThreatLevel  # LOW, MEDIUM, HIGH, CRITICAL
    final_score: float                # 0.0 - 100.0
    primary_factors: List[FactorContribution]
    natural_language_summary: str     # e.g., "HIGH threat assigned due to 2 vehicles intruding Zone Alpha at high speed."
```

---

## 10. Restricted Zone Architecture

Perimeter breach monitoring is managed by `RestrictedZoneService`.

```
  [ Polygon Zone Definition ] ── (Coordinates: [(x1,y1), (x2,y2), ...])
               │
               ▼
  [ Point-in-Polygon Check ] ── (Evaluates bounding box bottom-center / centroid)
               │
               ▼
  [ Spatial Events Generated ]
   ├── ZoneEntryEvent  (Object ID enters polygon)
   ├── ZoneExitEvent   (Object ID leaves polygon)
   └── ZoneLoiterEvent (Object ID remains in polygon > threshold T)
```

- Completely independent of UI logic.
- Configurable zone geometry per camera/demo scenario.
- Works identically across static images and video tracking sequences.

---

## 11. Object Detection Architecture

`DetectionService` encapsulates object detection model inference behind an abstract interface:

```python
class AbstractDetectionService(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray, confidence_threshold: float) -> List[DetectionResult]:
        pass
```

### Decoupled Result Schema
The application layer never interacts directly with YOLOv8 PyTorch/Numpy objects. It consumes standardized Data Transfer Objects:

```python
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

class DetectionResult:
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    frame_index: Optional[int] = None
```

- Initial implementation uses **Ultralytics YOLOv8**.
- Pluggable design allows future integration of RT-DETR, Faster R-CNN, or custom ONNX models without modifying downstream code.

---

## 12. Video Processing Architecture

Video processing is decoupled from object detection via `VideoProcessingService`.

### Reusable Pipeline Components
- **`VideoLoader`:** Memory-efficient stream/file reader using OpenCV `VideoCapture`.
- **`FrameSampler`:** Implements frame skipping (`sample_rate=N`) to optimize processing latency.
- **`VideoAnnotator`:** Draws bounding boxes, IDs, trajectories, and zone overlays onto output frames.
- **`VideoWriter`:** Encodes annotated frames into H.264/MP4 format using OpenCV `VideoWriter`.

```
[ Video File / Stream ] ──► [ FrameSampler (Skip N Frames) ] ──► [ Batch Detection ]
                                                                        │
[ Encoded MP4 Output ] ◄── [ VideoWriter ] ◄── [ VideoAnnotator ] ◄─────┘
```

---

## 13. Tracking Architecture

Multi-object tracking across video frames is decoupled into `TrackingService`.

```python
class TrackedObject:
    track_id: int
    class_name: str
    centroid_history: List[Tuple[int, int]]
    velocity: float
    trajectory_vector: Tuple[float, float]
    current_bbox: BoundingBox
```

- Associates detected objects across sequential frames (using ByteTRACK / SORT algorithms).
- Computes spatial trajectory vectors, loitering duration, and movement speeds.
- Interfaces seamlessly with `MovementAnalysisService` and `RestrictedZoneService`.

---

## 14. Built-in Demo Scenario Architecture

To ensure 100% offline demonstration capability, the system includes a pre-packaged **Demo Scenario Manager** consuming structured local assets:

### Demo File Structure
```
data/
└── demo/
    ├── drone/
    │   ├── images/
    │   └── videos/
    └── cctv/
        ├── images/
        └── videos/
```

### Scenario Metadata Schema (`demo_manifest.json`)
```json
{
  "scenario_id": "drone_img_01",
  "platform": "DRONE",
  "media_type": "IMAGE",
  "title": "Highway Perimeter Security Patrol",
  "description": "Aerial surveillance over main logistics highway.",
  "file_path": "data/demo/drone/images/highway_patrol.jpg",
  "expected_threat_category": "MEDIUM"
}
```

> [!NOTE]
> `expected_threat_category` is demonstration metadata for display; actual threat evaluation is always computed live by `ThreatScoringService`.

---

## 15. Auto Demo Workflow Architecture

The application provides an automated "Complete Demonstration" mode (`AutoDemoService`).

```
▶ [ Launch Auto Demo ]
       │
       ├─► 1. Run Drone Image Scenario  ──► Update Pipeline & Log Result
       ├─► 2. Run Drone Video Scenario  ──► Update Pipeline & Log Result
       ├─► 3. Run CCTV Image Scenario   ──► Update Pipeline & Log Result
       └─► 4. Run CCTV Video Scenario   ──► Update Pipeline & Log Result
       │
       ▼
   [ Batch Update History, Analytics & Alert Feeds ]
```

Auto Demo executes the **exact production analysis services** sequentially, guaranteeing authentic, un-mocked demonstration outputs.

---

## 16. Analytics Architecture

`AnalyticsService` aggregates historical inspection data persisted in the database to drive analytics dashboards.

### Aggregated Analytics Capabilities
- **Threat Level Distribution:** Proportion of LOW, MEDIUM, HIGH, and CRITICAL threats.
- **Temporal Threat Trends:** Daily/Hourly threat incident frequencies.
- **Class Detection Statistics:** Most frequently identified object categories.
- **Platform Performance:** Average inference latency, FPS, and confidence metrics.

Analytics queries run against SQLite indices, avoiding memory-bound Streamlit state accumulations.

---

## 17. History & Audit Logging Architecture

All completed surveillance runs are automatically persisted to the database by `HistoryService`.

### History Event Record Schema
- `analysis_id` (UUID Primary Key)
- `timestamp` (ISO-8601 Datetime)
- `input_source_type` (DEMO / UPLOAD / LIVE)
- `platform` (DRONE / CCTV)
- `media_type` (IMAGE / VIDEO)
- `scenario_name` (Optional string)
- `detected_classes_json` (Serialized object breakdown)
- `threat_score` (Float)
- `threat_level` (LOW / MEDIUM / HIGH / CRITICAL)
- `processing_time_ms` (Float)
- `alert_generated` (Boolean)
- `media_artifact_path` (Relative file path)

The History page provides filtering by platform, media type, date range, and threat level.

---

## 18. Alert Management Architecture

Real-time alert dispatch is managed by `AlertService`.

```
[ Threat Assessment / Zone Violation ]
                  │
                  ▼
   Check Configured Alert Rules
   (e.g., Threat Level >= HIGH OR Zone Violation == True)
                  │
                  ▼
         Generate Alert Record
   (Severity, Reason, Timestamp, Status="UNACKNOWLEDGED")
                  │
                  ▼
   Broadcast to UI Alert Banner & Persist to Database
```

Alert statuses (`UNACKNOWLEDGED`, `ACKNOWLEDGED`, `RESOLVED`) can be updated directly by operators in the UI.

---

## 19. Report Generation Architecture

`ReportService` formats structured analysis records into official surveillance PDF incident reports.

### Report Content Layout
1. **Header:** Incident Title, System Timestamp, Security Classification.
2. **Metadata Table:** Source Platform, Media Type, Operator ID.
3. **Key Visual Artifacts:** Input frame and annotated detection snapshot.
4. **Findings & Detections:** Detailed breakdown of detected objects and confidence.
5. **Threat Intelligence & XAI:** Threat Level badge, score breakdown, and XAI textual rationale.
6. **Restricted Zone Audit:** Log of perimeter entry/exit events.
7. **Action Plan (SOP):** Recommended operator procedures.

Report generation runs independently of Streamlit using ReportLab/WeasyPrint backend abstractions.

---

## 20. Centralized Configuration Architecture

All system configuration is managed centrally via `ConfigurationService` backed by YAML configuration files and environment variables. Hardcoded thresholds are strictly prohibited.

```yaml
# config/system_config.yaml
ai:
  model_path: "models/yolov8n.pt"
  confidence_threshold: 0.45
  iou_threshold: 0.50

video:
  sample_frame_rate: 5
  max_processing_duration_sec: 120

threat:
  weights:
    class_score: 0.30
    count_score: 0.20
    zone_violation: 0.35
    motion_speed: 0.15
  thresholds:
    medium: 25.0
    high: 50.0
    critical: 75.0

database:
  db_path: "data/surveillance.db"

logging:
  level: "INFO"
  log_file: "logs/surveillance.log"
```

---

## 21. Database Architecture & Schema Design

Data persistence uses **SQLite** encapsulated behind the Repository Pattern. Raw SQL queries are barred from presentation layers.

```
+-------------------+       +-------------------+       +-------------------+
|    analyses       |       |    detections     |       |      alerts       |
+-------------------+       +-------------------+       +-------------------+
| id (PK)           |<──┐   | id (PK)           |       | id (PK)           |
| timestamp         |   └───| analysis_id (FK)  |   ┌───| analysis_id (FK)  |
| input_source      |       | class_name        |   │   | severity          |
| platform          |       | confidence        |   │   | reason            |
| media_type        |       | bbox_json         |   │   | status            |
| threat_score      |       +-------------------+   │   +-------------------+
| threat_level      |                               │
| processing_ms     |       +-------------------+   │   +-------------------+
| artifact_path     |       |  zone_violations  |   │   |     reports       |
+-------------------+       +-------------------+   │   +-------------------+
        │                   | id (PK)           |   │   | id (PK)           |
        └──────────────────>| analysis_id (FK)  |   └───| analysis_id (FK)  |
                            | zone_name         |       | report_path       |
                            | object_id         |       | generated_at      |
                            +-------------------+       +-------------------+
```

---

## 22. Dependency Injection Container

Services are managed by a central **Dependency Injection (DI) Container** (`core/di_container.py`), providing clean decoupling and seamless test mocking.

```python
class DIContainer:
    _detection_service: Optional[AbstractDetectionService] = None
    _threat_service: Optional[AbstractThreatScoringService] = None
    # ... registration and lazy initialization factory methods
```

### Injected Core Services
1. `DetectionService`
2. `PreprocessingService`
3. `VideoProcessingService`
4. `TrackingService`
5. `MovementAnalysisService`
6. `RestrictedZoneService`
7. `ThreatScoringService`
8. `ExplainabilityService`
9. `DecisionSupportService`
10. `AnalyticsService`
11. `HistoryService`
12. `AlertService`
13. `ReportService`

UI scripts resolve dependencies through the container rather than directly constructing concrete classes.

---

## 23. Error Handling Architecture

Centralized exception handling (`core/exceptions.py`) maps backend errors to user-friendly UI error banners while preserving detailed technical logs.

```
[ System Exception Occurs ]
           │
           ▼
[ Core Exception Handler ]
           ├─► 1. Write Detailed Stack Trace & Payload to Structured Log File
           └─► 2. Raise Standardized Domain Exception (e.g., InvalidMediaError)
                       │
                       ▼
            [ Streamlit UI Error Boundary ]
            Render Clean, Actionable Alert Box (Zero raw tracebacks exposed)
```

---

## 24. Logging Architecture

Logging utilizes Python's `logging` framework configured in standard JSON or structured text format.

### Logged Operational Events
- System initialization & DI container setup
- Model loading duration & weight verification
- Input validation failures & file ingest events
- Inference execution time, FPS, and frame counts
- Database transaction commits & repository failures
- Threat level elevation & alert dispatch
- Incident report generation status

---

## 25. Externalized Configuration Management

- Zero hardcoded filesystem paths, model weights, or score thresholds.
- Configuration loaded dynamically on startup from `config/system_config.yaml`.
- Environment variable overrides supported for deployments (`SURVEILLANCE_ENV=production`).

---

## 26. Performance & Resource Optimization

1. **Model Singleton:** YOLOv8 model weights loaded once into memory lazily; instance shared across all detection calls.
2. **Duplicated Inference Prevention:** Frames are detected once per pipeline execution; downstream services consume shared detection results.
3. **Configurable Frame Skipping:** Processing skips $N$ frames during video analysis to maintain high real-time throughput.
4. **Generator-Based Stream Processing:** Video frames are processed iteratively as streams, keeping RAM usage capped.

---

## 27. Testing Strategy & Architecture

Every future SpecKit task must deliver corresponding tests within `tests/`.

```
tests/
├── unit/            # Pure domain logic tests (Threat math, Zone math)
├── services/        # Isolated service tests with mocked dependencies
├── repository/      # Database repository tests using in-memory SQLite
├── integration/     # End-to-end pipeline tests using local demo data
└── ui/             # Streamlit visual & state test stubs
```

- **Offline Independence:** Tests must execute 100% offline without network connections.
- **Deterministic Integration Testing:** Local demo scenarios serve as fixture datasets for integration suites.

---

## 28. Offline-First Requirement

- The system operates entirely without internet access.
- All AI model weights (`.pt`), demo assets, JavaScript dependencies (Plotly offline), and fonts are stored locally in the codebase repository.
- External API calls are strictly forbidden in core processing workflows.

---

## 29. Security & Data Integrity Standards

1. **Input File Validation:** MIME-type and extension validation for uploaded files before disk write.
2. **Path Traversal Protection:** File access restricted strictly to designated project subdirectories (`data/`, `temp/`).
3. **Sanitized Output:** Filenames and user input sanitization to prevent injection vulnerabilities.
4. **Secret Management:** Sensitive keys or environment variables loaded via `.env` files, excluded from source control.

---

## 30. System Extensibility

The architecture provides explicit abstraction interfaces to accommodate future enhancements without breaking changes:
- **New Detection Models:** Implement `AbstractDetectionService` (e.g., `ONNXDetectionService`).
- **New Trackers:** Implement `AbstractTrackingService` (e.g., `DeepSortTrackingService`).
- **New Input Modalities:** Add stream readers to `VideoProcessingService` (e.g., thermal sensor streams).
- **Cloud Database Migration:** Swap SQLite repository implementations for PostgreSQL/MySQL repositories.

---

## 31. SpecKit Governance & Compliance

Every future code contribution must be executed strictly through the **SpecKit Governance Cycle**:

$$\text{/specify} \longrightarrow \text{/clarify} \longrightarrow \text{/plan} \longrightarrow \text{/tasks} \longrightarrow \text{/implement}$$

> [!IMPORTANT]
> **Dual Architectural Compliance:** Every feature specification must explicitly verify compliance with both [`constitution.md`](file:///Users/sanjana/Documents/ai_p2/constitution.md) and [`architecture.md`](file:///Users/sanjana/Documents/ai_p2/architecture.md). Code modifications contradicting these documents will be rejected.

---

## 32. Architectural Decision Priority

When making technical or design trade-offs, all development must prioritize decisions using the following strict hierarchy:

1. **Correctness:** Accurately implement domain logic, detection handling, and threat calculations.
2. **Maintainability:** Clean code structure, explicit typing, and strict separation of concerns.
3. **Clear User Experience:** Intuitive operator workflow, minimal navigation, dark theme UI.
4. **Testability:** Decoupled interfaces, complete unit and integration test coverage.
5. **Performance:** Efficient memory usage, frame skipping, model reuse.
6. **Extensibility:** Pluggable interfaces for future AI models and sensor modalities.
