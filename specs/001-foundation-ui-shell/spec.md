# Feature Specification: Foundation and UI Shell for the AI Surveillance Command Center

**Feature Identifier**: `specs/001-foundation-ui-shell`  
**Created**: 2026-09-13  
**Status**: Draft  
**Input**: `/speckit.specify Create Specification 1: Foundation and UI Shell for the AI Surveillance Command Center.`  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## Clarifications

### Session 2026-09-13
- Q: How should the placeholder data across the Dashboard, Analytics, History, and Settings pages be managed for Specification 1? → A: Seed realistic baseline mock records directly into the SQLite database on startup via DatabaseService so repositories serve consistent data across pages.

---

## 1. User Scenarios & Testing *(mandatory)*

### User Story 1 - Shell Navigation & Primary Operational Pages (Priority: P1)

As a security operator under high cognitive load, I want to seamlessly navigate between seven dedicated operational pages (Dashboard, Surveillance, Analytics, History, Reports, Settings, About) via a clean, dark-themed sidebar menu, so that I can inspect system status and access surveillance workflows quickly.

**Why this priority**: The UI Shell and top-level navigation establish the complete application layout and user interface architecture defined in `constitution.md` (Section 4) and `architecture.md` (Section 6). All future features depend on this foundation.

**Independent Test**: Can be verified independently by starting the Streamlit application and clicking through all 7 primary sidebar items to ensure each page renders without errors or visual degradation.

**Acceptance Scenarios**:
1. **Given** the application is started, **When** the user accesses the sidebar, **Then** exactly 7 primary navigation items are visible: 🏠 Dashboard, 📡 Surveillance, 📊 Analytics, 📁 History, 📄 Reports, ⚙ Settings, and ℹ About.
2. **Given** the user is on any page, **When** they click a navigation item in the sidebar, **Then** the main viewport immediately updates to show the selected page view without breaking state.
3. **Given** any page is displayed, **When** rendered, **Then** it uses a cohesive, modern dark command-center theme optimized for readability and low-light control rooms.

---

### User Story 2 - Executive Dashboard & Operational Status Overview (Priority: P1)

As a security command center supervisor, I want an executive Dashboard displaying key metric cards, visual trends, recent activity, and quick-action shortcuts, so that I can immediately monitor overall threat posture and trigger primary workflows.

**Why this priority**: Provides the primary landing view for operators and satisfies `architecture.md` Section 7 requirements for operational overview.

**Independent Test**: Can be tested independently by navigating to 🏠 Dashboard and verifying that all metric cards, trend charts, activity logs, and quick action buttons render with expected placeholder/demo structures.

**Acceptance Scenarios**:
1. **Given** the Dashboard page is open, **When** loaded, **Then** status metric cards display values for Current Threat, Active Alerts, Today's Analyses, Average Confidence, Average Processing Time, and Model/System Status.
2. **Given** the Dashboard page is open, **When** loaded, **Then** visual charts render placeholder plots for Threat Trend, Object/Vehicle Detection Trend, and Threat Severity Distribution using Plotly.
3. **Given** the Dashboard page is open, **When** the user clicks any Quick Action button (Complete Demonstration, Upload Media, View History, Generate Report), **Then** the application contextually transitions to the corresponding target workflow.

---

### User Story 3 - Unified Surveillance Guided Workflow Shell (Priority: P1)

As a surveillance operator, I want to use a single, unified Surveillance workspace with a step-by-step wizard to select input source, platform metadata, media format, and scenario/upload before launching analysis, so that I don't need to jump across segregated pages.

**Why this priority**: Implements the central mandate of `constitution.md` (Section 4 & 5) and `architecture.md` (Section 5 & 8) requiring ONE unified Surveillance deck instead of separate Image/Video/Drone/CCTV tools.

**Independent Test**: Can be tested by executing Steps 1 through 7 of the Surveillance wizard, selecting different combinations of source (Demo, Upload, Live), platform (Drone, CCTV), and input type (Image, Video), and verifying contextual control rendering and result placeholder stack display.

**Acceptance Scenarios**:
1. **Given** the Surveillance page is opened, **When** Step 1 is rendered, **Then** the operator can choose between "Built-in Demo", "Upload Media", and "Live Camera".
2. **Given** Step 1 is chosen, **When** Step 2 is rendered, **Then** the operator can toggle platform metadata between "Drone" and "CCTV".
3. **Given** Step 2 is chosen, **When** Step 3 is rendered, **Then** the operator can select media type between "Image" and "Video".
4. **Given** Step 3 is chosen, **When** Step 4 is rendered, **Then**:
   - If "Built-in Demo" was selected, a scenario picker dropdown is displayed.
   - If "Upload Media" was selected, a file uploader component is displayed.
   - If "Live Camera" was selected, a camera configuration UI placeholder is displayed.
5. **Given** Step 4 is completed, **When** the operator clicks "Run Analysis" (Step 5), **Then** a structured results area (Step 6) renders containing placeholders for Original Input, Processed Media, Detection Result, Detected Objects Table, Threat Score, Threat Level, Confidence, Processing Time, Explainable AI Reason, and Recommended Actions (SOP), along with "Save to History" and "Generate Report" action triggers (Step 7).

---

### User Story 4 - Analytics, History, Reports, Settings, & About Shells (Priority: P2)

As a security auditor or system administrator, I want dedicated pages for historical analytics, event search, report management, system configuration, and project documentation, so that I can manage system operations effectively.

**Why this priority**: Completes the full application shell and ensures all secondary navigation destinations exist and follow Clean Architecture standards (`architecture.md` Sections 16, 17, 18, 19, 20).

**Independent Test**: Navigate to Analytics, History, Reports, Settings, and About pages independently and verify correct rendering of tables, filter controls, form fields, and documentation panels.

**Acceptance Scenarios**:
1. **Given** the 📊 Analytics page, **When** rendered, **Then** placeholder charts for threat trends, threat distribution, vehicle counts, confidence, performance, and regional comparison are displayed.
2. **Given** the 📁 History page, **When** rendered, **Then** a searchable/filterable audit log table displays placeholder analysis records formatted with timestamp, platform, input type, threat score, threat level, processing time, and alert status.
3. **Given** the 📄 Reports page, **When** rendered, **Then** controls for history record selection, report type picker, preview panel, and "Generate Report" button are visible.
4. **Given** the ⚙ Settings page, **When** rendered, **Then** tabbed sections for Detection Model, Confidence Threshold, Threat Thresholds, Camera Settings, Database Settings, and Theme/Display Settings display interactive form controls.
5. **Given** the ℹ About page, **When** rendered, **Then** comprehensive documentation covering project title, objectives, system overview, architecture, tech stack, and future roadmap is displayed.

---

### User Story 5 - Infrastructure Foundation & Service Container (Priority: P1)

As a developer, I want centralized configuration management, structured logging, dependency injection, SQLite database initialization, centralized error handling, and demo directory structures established, so that future AI capabilities can be plugged in cleanly.

**Why this priority**: Enforces Clean Architecture (`architecture.md` Section 2 & 22) and foundation requirements (Section 9 & 21).

**Independent Test**: Execute unit tests verifying that `ConfigurationService`, `DatabaseService`, `DIContainer`, `Logger`, and error handlers initialize correctly, SQLite tables are created, and demo directories exist.

**Acceptance Scenarios**:
1. **Given** application startup, **When** `DIContainer` initializes, **Then** configuration files are loaded, structured logging is started, and SQLite database schema tables are created.
2. **Given** project initialization, **When** filesystem is inspected, **Then** `data/demo/drone/images`, `data/demo/drone/videos`, `data/demo/cctv/images`, and `data/demo/cctv/videos` exist.
3. **Given** backend initialization, **When** database tables are created, **Then** tables for `analyses`, `detections`, `threat_assessments`, `alerts`, `reports`, `restricted_zones`, and `settings` are created in SQLite.

---

## 2. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement a single-page Streamlit application shell with primary navigation containing ONLY: Dashboard, Surveillance, Analytics, History, Reports, Settings, and About.
- **FR-002**: Presentation code MUST reside in UI rendering modules and MUST NOT contain domain business logic or direct database operations.
- **FR-003**: The UI MUST enforce a dark-themed, professional surveillance command center aesthetic using custom CSS/Streamlit styling.
- **FR-004**: The system MUST provide reusable UI components for navigation, metric cards, status indicators, threat level badges, buttons, result panels, tables, charts, alert banners, section headers, and empty/loading/error states.
- **FR-005**: The Dashboard MUST render 6 metric cards, 3 Plotly visualization panels, a recent activity table, and 4 quick action triggers.
- **FR-006**: The Surveillance page MUST implement ONE unified step-by-step workflow with progressive disclosure across Source (Demo/Upload/Live), Platform (Drone/CCTV), Input Type (Image/Video), Input Selection, Analysis Execution, and Results Rendering.
- **FR-007**: The Surveillance results area MUST render structured visual containers for Original Input, Processed Output, Detection Summary, Object List, Threat Score/Level, Confidence, Processing Time, XAI Explanation, SOP Recommended Actions, Save to History, and Generate Report.
- **FR-008**: Clicking "Run Analysis" in this specification MUST NOT invoke real object detection or video models, but MUST display a clear notice indicating that live AI inference will be introduced in subsequent specifications.
- **FR-009**: The Analytics page MUST display structured visual containers and charts for threat distribution, threat trends, object counts, confidence, performance metrics, and regional comparisons.
- **FR-010**: The History page MUST provide a searchable and filterable table displaying analysis event records containing timestamp, platform, input type, threat score, threat level, confidence, processing time, and alert status.
- **FR-011**: The Reports page MUST provide a UI shell containing analysis selection, report type selection, report preview area, and a "Generate Report" action button.
- **FR-012**: The Settings page MUST provide centralized configuration forms for AI Model settings, Confidence Thresholds, Threat Weights/Thresholds, Camera Sources, Database Settings, and Theme/Display Settings.
- **FR-013**: The About page MUST document project goals, system architecture, technology stack, workflow diagrams, and future capability roadmaps.
- **FR-014**: The system MUST initialize centralized YAML configuration management (`ConfigurationService`), structured logging (`Logger`), dependency injection container (`DIContainer`), and centralized exception handling (`ExceptionHandler`).
- **FR-015**: The system MUST initialize an SQLite database using repository abstractions and create baseline schema tables for analyses, detections, threat assessments, alerts, reports, restricted zones, and settings.
- **FR-016**: The system MUST establish the local directory hierarchy for demo assets:
  - `data/demo/drone/images`
  - `data/demo/drone/videos`
  - `data/demo/cctv/images`
  - `data/demo/cctv/videos`
- **FR-017**: The `DatabaseService` MUST automatically seed realistic baseline mock records for analyses, detections, threat assessments, alerts, reports, and settings into the SQLite database during startup initialization.

---

### Key Entities *(include if feature involves data)*

- **AnalysisRecord**: Represents a completed surveillance analysis event. Attributes: `id` (UUID), `timestamp` (ISO-8601), `source_type` (DEMO/UPLOAD/LIVE), `platform` (DRONE/CCTV), `media_type` (IMAGE/VIDEO), `threat_score` (float), `threat_level` (LOW/MEDIUM/HIGH/CRITICAL), `confidence_avg` (float), `processing_time_ms` (float), `status` (string).
- **DetectionRecord**: Represents individual detected objects. Attributes: `id` (UUID), `analysis_id` (FK), `class_name` (string), `confidence` (float), `bbox_json` (string).
- **ThreatAssessmentRecord**: Represents threat scoring details. Attributes: `id` (UUID), `analysis_id` (FK), `score` (float), `level` (string), `xai_reason` (string), `recommended_sop` (string).
- **AlertRecord**: Represents generated security alerts. Attributes: `id` (UUID), `analysis_id` (FK), `severity` (string), `reason` (string), `status` (UNACKNOWLEDGED/ACKNOWLEDGED/RESOLVED).
- **ReportRecord**: Represents generated PDF/JSON reports. Attributes: `id` (UUID), `analysis_id` (FK), `file_path` (string), `generated_at` (timestamp).
- **SystemSettings**: Represents application configuration parameters. Attributes: `key` (string), `value` (string), `category` (string).

---

## 3. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The application starts successfully and renders the default Dashboard page without noticeable delay under normal local execution.
- **SC-002**: 100% of the 7 primary navigation pages (Dashboard, Surveillance, Analytics, History, Reports, Settings, About) render without Python exceptions or layout glitches.
- **SC-003**: Navigation between primary pages responds promptly without visible UI freezing under normal local execution.
- **SC-004**: The Surveillance wizard permits selection of all combinations of Source (3), Platform (2), and Media Type (2) smoothly with contextual state updates.
- **SC-005**: All SQLite tables (`analyses`, `detections`, `threat_assessments`, `alerts`, `reports`, `restricted_zones`, `settings`) are created upon initial startup.
- **SC-006**: Automated test suite (`pytest`) verifies application startup, page rendering, configuration loading, DI container initialization, and database creation with **100% test pass rate**.

---

## 4. Assumptions

- **Target Environment**: Local workstation running Python 3.10+ with Streamlit, OpenCV, Plotly, Pytest, and SQLite installed.
- **Offline Autonomy**: Application runs 100% offline without network calls.
- **AI Scope Exclusion**: AI model weight loading (YOLOv8 inference), OpenCV video frame loops, tracking algorithms, and actual PDF rendering are explicitly out of scope for Specification 1 and reserved for subsequent specifications.
- **Demo Assets**: Demo directories are created empty in Specification 1; media assets will be populated in subsequent features.

---

## 5. Non-Goals *(Explicit Exclusions)*

The following capabilities are **EXPLICITLY EXCLUDED** from Specification 1 and will be specified in future iterations:
- ❌ Actual YOLOv8 object detection inference.
- ❌ Actual OpenCV video frame extraction and stream processing loops.
- ❌ Multi-object tracking (SORT/ByteTRACK).
- ❌ Spatial movement analysis and trajectory calculations.
- ❌ Polygon restricted-zone intersection math.
- ❌ Real-time dynamic threat scoring algorithms.
- ❌ Explainable AI saliency/attribution calculation logic.
- ❌ Automated PDF file generation engine.
- ❌ Real-time camera RTSP ingest and streaming.
- ❌ Automated threat-triggered alert dispatch.
