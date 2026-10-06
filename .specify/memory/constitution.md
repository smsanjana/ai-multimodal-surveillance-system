# Project Constitution

# AI-Based Multimodal Surveillance System for Threat Detection and Decision Support

> **Status:** Active & Mandatory  
> **Governance Framework:** SpecKit Compliance Standard  
> **Target System:** Professional AI-Powered Surveillance Command Center  

---

## 1. Project Vision & Purpose

The **AI-Based Multimodal Surveillance System for Threat Detection and Decision Support** is a mission-critical AI-powered Surveillance Command Center designed to assist security personnel in real-time surveillance monitoring, threat detection, movement tracking, threat assessment, explainable AI decision support, and operational workflow management.

The system is designed for high-stakes operational environments including **defense installations, border security, industrial facilities, airports, smart city hubs, and critical infrastructure control centers**. 

It must present itself as a unified, production-grade surveillance platform rather than a disconnected collection of standalone AI demonstrations. All future development shall proceed incrementally adhering strictly to **SpecKit** standards.

---

## 2. Core Architectural & System Principles

Every specification, module, and pull request generated for this project must strictly comply with the following architectural principles:

* **Modular Development:** System functions must be organized into decoupled, single-responsibility modules with clear interface boundaries.
* **Separation of Concerns:** Presentation, orchestration, domain business logic, data persistence, and AI inference must reside in distinct code layers.
* **Clean Architecture:** Inner layers (domain logic, entities, services) must not depend on outer layers (Streamlit UI, database adapters, external AI frameworks).
* **Dependency Injection (DI):** Services and repositories must accept dependencies via constructors or factories, enabling seamless mocking, testing, and service swapping.
* **Centralized Configuration:** All operational parameters, model paths, database URIs, UI defaults, and feature flags must be externalized in central configuration schemas.
* **Reusable Core Services:** Inference, scoring, logging, data access, and report generation must exist as shared service contracts consumable across any interface component.
* **Reusable UI Components:** Visual widgets (threat badges, metric cards, video player feeds, telemetry charts) must be encapsulated as reusable components.
* **Professional Documentation:** All public APIs, modules, data models, and workflow pipelines must maintain complete docstrings, architectural diagrams, and schema specifications.
* **Consistent Naming Conventions:** Snake_case for variables/functions, PascalCase for classes/interfaces, and UPPER_SNAKE_CASE for constants/configuration keys.
* **Maintainability & Extensibility:** Code must prioritize readability, explicit type hints, static analysis compliance, and open-closed extension patterns.

---

## 3. AI Engineering Principles

* **UI Independence:** AI models, inference logic, tracking algorithms, and scoring matrices must be entirely decoupled from UI components. They must be invokable via head-less Python APIs or background workers.
* **Zero UI Business Logic:** Streamlit scripts must only render state and capture user inputs. No object detection loops, feature extraction logic, or threat calculation math may reside in Streamlit page files.
* **Independent Domain Services:** The core capabilities must be partitioned into dedicated, single-purpose service modules:
  * `DetectionService`: Handles object detection, class filtering, and bounding box normalization.
  * `TrackingService`: Performs temporal object tracking, ID assignment, and trajectory analysis.
  * `MovementAnalysisService`: Evaluates speed, direction, perimeter violations, and anomalous movement patterns.
  * `ThreatScoringService`: Synthesizes detection and tracking metrics into deterministic threat scores.
  * `ExplainabilityService`: Computes feature attribution, confidence breakdowns, and natural language decision explanations.
  * `ReportingService`: Formats operational data into printable and exportable surveillance reports.
  * `AnalyticsService`: Aggregates historical metrics for visual trend analysis.
  * `AlertService`: Evaluates alert rules, dispatches notifications, and tracks acknowledgement lifecycles.
* **Explainable AI (XAI):** Every threat assessment, alert elevation, or anomaly flag must generate human-understandable reasoning explaining *why* the threat level was assigned (e.g., specific class presence, speed delta, zone restriction violation).
* **No Hardcoded Thresholds:** Confidence cutoffs, threat weights, speed thresholds, and alert trigger boundaries must be dynamically loaded from external configuration sources.

---

## 4. User Interface & Operator Experience Principles

The user interface represents an operational command deck used by security operators under high cognitive load.

* **Operator-Focused Simplicity:** UI layouts must be uncluttered, clean, visually intuitive, and free from non-essential decorations.
* **Minimalist Navigation:** The application must strictly use the following single-level primary navigation structure:
  * 🏠 **Dashboard** — Executive metrics, active alert summary, live status feeds.
  * 📡 **Surveillance** — Primary operational deck for image, video, and live stream threat monitoring.
  * 📊 **Analytics** — Historical threat trends, spatial heatmaps, and system performance metrics.
  * 📁 **History** — Searchable repository of past events, audit logs, and saved feeds.
  * 📄 **Reports** — Threat summary report generator and export manager (PDF/CSV/JSON).
  * ⚙ **Settings** — Threshold configuration, model selections, system rules, and UI preferences.
  * ℹ **About** — System versioning, architecture documentation, and system health status.
* **Streamlined Workflows:** Duplicate pages, redundant sub-menus, and fragmented workflows are prohibited.
* **Unified Surveillance Interface:** All input sources (static images, recorded videos, RTSP/Webcam live feeds) must be handled within a single, unified Surveillance workspace rather than segregated tools.
* **Professional Dark Theme:** The interface must use a consistent dark color palette suited for low-light control rooms, maximizing visual contrast for video feeds and alert indicators.
* **Readability Over Complexity:** High visual hierarchy, crisp typography, and unambiguous color coding (Green = Low, Yellow = Medium, Orange = High, Red = Critical) must take precedence over visual novelty.

---

## 5. Unified Surveillance Workflow Architecture

All surveillance processing pipelines across image, video, and stream modalities must adhere strictly to the standardized sequential workflow:

```
[Input Source] (Image / Video / Live Stream)
      ↓
[Preprocessing] (Resize, Normalize, Frame Extraction)
      ↓
[Object Detection] (YOLOv8 Inference, Bounding Box Extraction)
      ↓
[Movement Analysis] (Velocity, Trajectory, Restricted Zone Crossing)
      ↓
[Tracking] (Multi-Object Tracking, Bounding Box Persistence)
      ↓
[Threat Scoring] (Heuristic & AI Threat Level Calculation)
      ↓
[Explainable AI] (Explanation Generation, Visual Saliency, Audit Log)
      ↓
[Decision Support] (Action Recommendations, Standard Operating Procedures)
      ↓
[History] (Database Persistence of Event & Telemetry)
      ↓
[Reports] (Automated Incident Summaries)
      ↓
[Alerts] (Real-time Operator Dispatch & Trigger Handling)
      ↓
[Dashboard] (Aggregated Real-Time Operator Overview)
```

No feature implementation may bypass steps or construct alternate isolated pipelines.

---

## 6. Offline & Demonstration Philosophy

* **Full Offline Autonomy:** The application must be 100% functional without requiring active internet connectivity. All dependencies, models, and assets must be bundled locally.
* **Built-in Demo Scenarios:** The project must include pre-packaged test datasets and scenarios covering diverse surveillance modalities:
  * **Drone Images & Drone Videos** (Aerial reconnaissance, wide-area monitoring)
  * **CCTV Images & CCTV Videos** (Fixed perimeter, entry point monitoring)
* **Threat Spectrum Representation:** Demo datasets must provide test scenarios corresponding to all four threat classification levels:
  * 🟢 **Low Threat** — Routine background activity, authorized personnel.
  * 🟡 **Medium Threat** — Loitering, minor boundary approach.
  * 🟠 **High Threat** — Unattended object, fence scaling, unauthorized vehicle entry.
  * 🔴 **Critical Threat** — Armed breach, rapid intrusion into high-security zones.
* **Demonstration Reliability:** Demo mode must allow instant switching between scenarios during presentations, code reviews, and stakeholder evaluations.

---

## 7. Software Quality & Testing Standards

Every feature specification must mandate software quality mechanisms prior to code approval:

* **Comprehensive Logging:** Structured logging (using Python's `logging` module) with configurable log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) across all backend services.
* **Robust Error Handling:** Explicit exception handling with user-friendly error boundaries in UI and actionable trace logs in backend services.
* **Data Validation:** Strict input validation for file uploads, stream URIs, configuration values, and API payloads using Pydantic or type contracts.
* **Unit Testing:** Comprehensive test coverage for services, utility functions, scoring algorithms, and data access layers (`pytest`).
* **Integration Testing:** Verification of end-to-end processing pipelines (Input → Detection → Scoring → Persistence).
* **Performance Monitoring:** Telemetry tracking inference speed (FPS), latency, memory footprint, and CPU/GPU usage.
* **Code Quality & Style:** Mandatory type hints, flake8/black code formatting compliance, and zero reduction in overall code readability.

---

## 8. Performance & Resource Principles

* **Reusable Models:** Machine learning models (YOLOv8 weights, tracking models) must be loaded into memory lazily or at system startup as singletons to eliminate per-request reloading overhead.
* **Eliminate Duplicated Inference:** Frames and images must undergo object detection once per cycle; downstream modules (tracking, scoring, UI visualization) must consume shared inference results.
* **Efficient Memory Allocation:** Video processing pipelines must process frames using generators or sliding buffers to prevent out-of-memory errors during long stream playback.
* **Scalable Architecture:** Code must be structured to accommodate future hardware acceleration (CUDA/Metal), multi-threading, or asynchronous queue workers without requiring architectural rewrites.

---

## 9. Approved Technology Stack

The project must strictly stick to the standard technology choices unless a formal constitution amendment is executed:

| Domain | Standard Technology |
| :--- | :--- |
| **Primary Language** | Python 3.10+ |
| **User Interface** | Streamlit |
| **Computer Vision & AI** | OpenCV, Ultralytics YOLOv8 |
| **Data Visualization** | Plotly |
| **Database & Persistence** | SQLite |
| **Architecture Patterns** | Clean Architecture, Dependency Injection (DI) |
| **Configuration** | YAML / Environment Variables / Pydantic Settings |
| **Testing Framework** | Pytest |

---

## 10. SpecKit Development Lifecycle Governance

All future project iterations must strictly implement features through the **SpecKit Governance Cycle**:

$$\text{Specification} \longrightarrow \text{Clarification} \longrightarrow \text{Planning} \longrightarrow \text{Task Decomposition} \longrightarrow \text{Implementation}$$

1. **`/specify`:** Define formal feature specification documents in `.speckit/` specifying requirements, user stories, and acceptance criteria.
2. **`/clarify`:** Resolve ambiguities, edge cases, missing requirements, and constraints.
3. **`/plan`:** Create technical implementation plans detailing module contracts, data schemas, dependency diagrams, and UI wireframes.
4. **`/tasks`:** Break down implementation plans into discrete, verifiable development tasks.
5. **`/implement`:** Execute code writing, unit testing, documentation, and verification.

> [!IMPORTANT]
> **Constitution Supremacy:** No specification, implementation plan, or pull request may contradict or violate any principle set forth in this document. Any proposed deviation requires an explicit revision to `constitution.md`.

---

## 11. Long-Term Capability Checklist

The finalized production system must achieve and maintain full operational support for the following core capabilities:

- [ ] **Image Surveillance Processing** (Single & Batch Image Analysis)
- [ ] **Video Surveillance Processing** (Recorded File Analysis & Annotations)
- [ ] **Live Camera Feed Surveillance** (RTSP, Webcams, Network Cameras)
- [ ] **Real-time Object Detection** (Class Identification, Bounding Box Rendering)
- [ ] **Multi-Object Tracking** (Trajectory, Velocity, Spatial Telemetry)
- [ ] **Automated Threat Assessment** (Multi-factor Threat Level Scoring)
- [ ] **Explainable AI Engine** (Visual & Textual Decision Attribution)
- [ ] **Operator Decision Support** (Recommended Actions & Escalation Protocols)
- [ ] **Analytics Engine** (Interactive Plotly Dashboards & Trend Reports)
- [ ] **History & Event Audit Manager** (Searchable Event Records & Telemetry Logs)
- [ ] **Report Generator** (Incident Reports & Summary Exports)
- [ ] **Alert Management Engine** (Real-Time Operator Notifications & Trigger Log)
