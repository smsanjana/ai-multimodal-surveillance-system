# Feature Specification: Feature 005 - Contextual Threat Assessment & Decision Support

**Feature Branch**: `005-contextual-threat-decision-support`  
**Created**: 2026-09-28  
**Last Revised**: 2026-09-28  
**Status**: Draft (Revised with Approved Design Decisions)  
**Input**: User description: "Extend the existing image and video surveillance pipeline with explainable, evidence-based contextual assessment, normalized spatial zone evaluation, behavior event tracking, and human-reviewed decision support while strictly preserving Feature 003 threat-scoring rules."

---

## 1. Executive Summary & Core Objectives

Feature 005 extends the AI Surveillance Command Center beyond isolated object detection and basic tracking by introducing a **deterministic, evidence-based Contextual Assessment Engine** and a **Human Analyst Review Workflow**.

### Core Objectives
1. **Normalized Spatial Zone Monitoring**: Evaluate target bounding box centroids against normalized image-space geometric zones ($[0.0, 1.0]$ coordinate scale), explicitly distinguishing **computed spatial boundary-crossing events** from **configured scenario metadata flags**.
2. **Observable Event Analysis**: Categorize target behavior into verifiable observable events (`ZONE_ENTRY`, `ZONE_TRANSIT`, `STATIONARY_IN_ZONE`, `PERIMETER_APPROACH`, `ROUTINE_TRANSIT`) based strictly on image-space track movement without claiming to detect hostile intent or psychological state.
3. **Preservation of Feature 003 Threat Scoring Baseline**: Maintain the exact Feature 003 threat-scoring formula (Baseline 5.0; +65.0 for verified zone signal; +20.0 for unauthorized access signal; LOW < 25, MEDIUM 25–49, HIGH 50–74, CRITICAL $\ge 75$). Any new contextual score is presented as a **Separate Proposed Spatial Assessment**, never replacing or mutating the primary Feature 003 threat score.
4. **Transparent XAI Explainability**: Report only mathematical factors actually used by the approved scoring formula, explicitly excluding scenario titles, filenames, object classes, or movement speeds from threat point additions.
5. **Human Analyst Review & Audit Trail**: Equip security operators with a review workflow (`PENDING_REVIEW`, `ACKNOWLEDGED`, `FALSE_POSITIVE`, `ESCALATED`) backed by full revision history in SQLite (`analyst_reviews` and `analyst_review_history`), keeping human analyst decisions strictly separated from machine-generated observations.

---

## 2. User Scenarios & Testing

### User Story 1 - Normalized Spatial Zone Evaluation & Boundary Crossing (Priority: P1) 🎯 MVP

As a surveillance command deck operator, I want to define image-space restricted zones using normalized polygon coordinates $[0.0, 1.0]$ and evaluate target tracks against them, so that the system computes actual spatial boundary-crossing events independently of scenario titles or metadata flags.

**Why this priority**: Core foundation for contextual intelligence. Replaces metadata flag reliance with verifiable spatial point-in-polygon math between tracked object centroids and configured zone boundaries.

**Coordinate Definition**:
- **Normalized Coordinate Space**: Float values in range $[0.0, 1.0]$ where $(0.0, 0.0)$ represents top-left corner, $+X$ extends right $[0.0, 1.0]$, and $+Y$ extends down $[0.0, 1.0]$.
- **Resolution Mapping**: `pixel_x = int(norm_x * frame_width)`, `pixel_y = int(norm_y * frame_height)`.
- **Scope Limitation**: Normalized 2D frame regions represent image-space camera views and do **NOT** represent real-world geographic (GPS/GIS) coordinates.

**Independent Test**: Define a normalized spatial zone, process a video feed with target tracks, and verify that:
1. Object centroids intersecting the zone trigger a computed `ZONE_ENTRY` or `ZONE_TRANSIT` event.
2. The computed zone event is clearly distinguished in the UI from pre-configured scenario metadata flags (`zone_violation_flag`).
3. If no zone configuration is provided or polygon coordinates are missing, the system falls back safely to an open corridor routine assessment without error.

**Acceptance Scenarios**:
1. **Given** a normalized spatial zone boundary $Z$ and a tracked target $T_1$ whose centroid $(x, y)$ moves from outside $Z$ to inside $Z$, **When** spatial zone evaluation runs, **Then** the system logs a computed spatial `ZONE_ENTRY` event and presents a Separate Proposed Spatial Assessment.
2. **Given** a video processed without an active zone configuration, **When** analysis completes, **Then** the system classifies target movement as `ROUTINE_TRANSIT` and maintains baseline threat scoring without error.
3. **Given** a demo video with a configured `zone_violation_flag = True` metadata setting, **When** rendering analysis results, **Then** the UI explicitly displays `"Configured Scenario Metadata Signal: YES"` alongside `"Computed Spatial Boundary Crossing: [DETECTED / NOT DETECTED]"`, keeping the two concepts distinct.

---

### User Story 2 - Observable Event Analysis & Threat Explainability (Priority: P2)

As a security intelligence analyst, I want the system to analyze target trajectories and categorize observable movement events into transparent, evidence-based behavior classifications with XAI explanations, so that I can review actionable decision support without unverified claims of intent.

**Why this priority**: Ensures strict alignment with defense safety standards by presenting observable physical facts (`MOVING`, `STATIONARY`, `ZONE_ENTRY`, `PERIMETER_APPROACH`) rather than speculative intent or uncalibrated physical speed.

**Independent Test**: Process a video feed containing stationary and moving military assets; verify that the system categorizes observable events, outputs step-by-step threat score breakdowns using only approved Feature 003 factors, and provides applicable SOP recommendations.

**Acceptance Scenarios**:
1. **Given** a military vehicle (`Tank` or `M. Rocket Launcher`) stationary inside a restricted zone, **When** behavior analysis runs, **Then** the system assigns the event type `STATIONARY_OBJECT_IN_ZONE` and notes sustained spatial presence in the XAI rationale.
2. **Given** low-confidence or fragmented tracks (due to occlusion), **When** evaluating behavior events, **Then** the system tags the event with an `UNCERTAIN_TRACK` quality flag.
3. **Given** any analysis result, **When** generating the XAI explanation, **Then** the rationale lists ONLY factors used in the approved formula (Surveillance Baseline Observation +5.0, Verified Restricted Zone Signal +65.0, Verified Unauthorized Access Signal +20.0) and explicitly excludes scenario titles, filenames, object classes, or movement speeds from threat point additions.

---

### User Story 3 - Configurable Analyst ID, Review Lifecycle & Audit Trail (Priority: P3)

As a senior security supervisor, I want analysts to inspect, acknowledge, re-classify (`FALSE_POSITIVE`), or escalate machine-generated assessments using a configurable Analyst ID, and persist these decisions and full transition histories in SQLite, so that human command authority is maintained and audit trail integrity is preserved.

**Why this priority**: Fulfills human-in-the-loop decision support requirements, enabling operational oversight, false-positive tagging, and compliance auditing.

**Analyst ID Configuration**:
- Configured via `src/core/config.py` (`analyst.default_id`, default `"OPERATOR_01"`).
- Documented as an unauthenticated demo fallback. Production authentication and RBAC are explicitly out of scope.

**False-Positive Review & Score Preservation**:
- Marking an assessment as `FALSE_POSITIVE` updates the review record status in SQLite (`analyst_reviews`) and displays the `FALSE_POSITIVE` status tag in the UI.
- The original machine-generated assessment, detection coordinates, and AI threat score ($70.0/100$) are **100% preserved and NEVER overwritten or recalculated**.
- Machine observations, machine threat score, and analyst review decisions remain strictly separated fields in data models and UI displays.

**Review State Lifecycle & Audit Trail**:
- **Permitted Status Transitions**: `PENDING_REVIEW` $\rightarrow$ `ACKNOWLEDGED`, `PENDING_REVIEW` $\rightarrow$ `FALSE_POSITIVE`, `PENDING_REVIEW` $\rightarrow$ `ESCALATED`, `ACKNOWLEDGED` $\rightarrow$ `FALSE_POSITIVE`, `FALSE_POSITIVE` $\rightarrow$ `ACKNOWLEDGED`, `FALSE_POSITIVE` $\rightarrow$ `ESCALATED`.
- **Transition History**: Every status change creates a record in `analyst_review_history` (`history_id`, `review_id`, `analysis_id`, `from_status`, `to_status`, `analyst_id`, `notes`, `updated_at`).

**Independent Test**: Navigate to an analysis record in the UI, submit an analyst review decision (`FALSE_POSITIVE` with operator notes), refresh the application, and verify that the original AI score remains unchanged, the review status displays `FALSE_POSITIVE`, and the transition is recorded in `analyst_review_history`.

---

## 3. Out-of-Scope Declarations

To preserve project boundaries, the following are explicitly **OUT OF SCOPE** for Feature 005:
- **Hostile-Intent Detection**: Automated inference of human psychological state, hostile motivation, or future aggressive actions.
- **Autonomous Response / Weapon Control**: Automated dispatch of kinetic responses, countermeasures, or weapon targeting.
- **Real-World Geographic Coordinates**: GIS/GPS mapping or real-world physical coordinate transformation.
- **Production Authentication / RBAC**: Multi-tenant user login, SSO, or role-based access control (Analyst ID is a configurable configuration parameter defaulting to `"OPERATOR_01"`).
- **YOLO Retraining**: Re-tuning YOLOv8 weights or modifying fine-tuned KIIT-MiTA model parameters.
- **Modification of Feature 003 Threat Scoring Baseline**: Changing the baseline +5.0 score, +65.0 zone addition, +20.0 unauthorized access addition, or threat level boundaries (LOW < 25, MEDIUM 25–49, HIGH 50–74, CRITICAL $\ge 75$).

---

## 4. Edge Cases & Failure Modes

- **Invalid Zone Polygon**: Coordinates $< 3$ points or outside $[0.0, 1.0]$ bounds are rejected cleanly with a validation error banner.
- **Points on Polygon Boundary**: Points lying exactly on polygon boundary edges are evaluated as inside the zone (`cv2.pointPolygonTest` $\ge 0$).
- **Missing Zone Configuration**: System defaults to full-frame unrestricted monitoring, treating all movement as `ROUTINE_TRANSIT` with baseline scoring.
- **Fragmented / Interrupted Tracks**: Missed detections across frames are tagged with `UNCERTAIN_TRACK` quality flags; events require minimum 2 continuous detections to trigger high-priority alerts.
- **Analyst Decision Change**: Updating a prior review decision appends a row to `analyst_review_history` and updates `analyst_reviews.review_status` without mutating `analyses.threat_score`.

---

## 5. Functional Requirements

- **FR-001**: System MUST implement a `SpatialZoneEvaluator` service that evaluates target bounding box centroids against normalized image-space polygons (`RestrictedZone`) defined in range $[0.0, 1.0]$.
- **FR-002**: System MUST convert normalized polygon coordinates $[0.0, 1.0]$ to frame pixels using `pixel_x = int(norm_x * width)` and `pixel_y = int(norm_y * height)`.
- **FR-003**: System MUST evaluate points on polygon edges as inside the zone (`cv2.pointPolygonTest` $\ge 0$).
- **FR-004**: System MUST associate zone configurations with specific platform (`DRONE` or `CCTV`) and camera URI endpoint.
- **FR-005**: System MUST compute spatial boundary-crossing events by calculating polygon intersection with object centroids, explicitly distinguishing computed spatial boundary events from pre-configured scenario metadata flags (`zone_violation_flag`).
- **FR-006**: System MUST preserve Feature 003 threat-scoring rules and numerical thresholds without modification (Baseline 5.0 for detections present; +65.0 for verified restricted zone signal; +20.0 for unauthorized access signal; LOW < 25, MEDIUM 25–49, HIGH 50–74, CRITICAL $\ge 75$).
- **FR-007**: System MUST present any new contextual score as a **Separate Proposed Spatial Assessment**, clearly identified alongside and NEVER replacing the primary Feature 003 threat score.
- **FR-008**: System MUST classify observable behavior into standardized event types: `ROUTINE_TRANSIT`, `PERIMETER_APPROACH`, `ZONE_ENTRY`, `ZONE_TRANSIT`, and `STATIONARY_OBJECT_IN_ZONE`.
- **FR-009**: System MUST generate XAI explanations reporting ONLY mathematical factors used in the approved Feature 003 formula, explicitly excluding scenario titles, filenames, object classes, or movement speeds from threat point additions.
- **FR-010**: System MUST resolve default Analyst ID from Configuration Service (`analyst.default_id`, default `"OPERATOR_01"`).
- **FR-011**: System MUST implement a human analyst review workflow supporting four review states: `PENDING_REVIEW`, `ACKNOWLEDGED`, `FALSE_POSITIVE`, and `ESCALATED`.
- **FR-012**: System MUST persist human analyst review decisions in `analyst_reviews` and log decision transitions in `analyst_review_history`, preserving raw machine-generated analysis records (`analyses.threat_score`) without mutation.
- **FR-013**: System MUST update History and Analytics UI pages to display analyst review status badges, operator notes, and transition audit history.

---

## 6. Non-Functional Requirements & System Constraints

- **NFR-001 (Performance)**: Spatial zone evaluation and contextual assessment MUST execute in under `50.0 ms` per video analysis pass.
- **NFR-002 (Clean Architecture)**: Service components MUST adhere strictly to Clean Architecture layering (`Domain` entities & interfaces, `Application` orchestrators, `Infrastructure` services & repositories, `UI` deck).
- **NFR-003 (Offline-First Persistence)**: All zone configurations, contextual assessments, analyst reviews, and review histories MUST operate completely offline using local SQLite storage (`data/surveillance.db`).
- **NFR-004 (Backward Compatibility)**: Existing Features 001–004 schemas, API contracts, threat scoring rules, and test suites (51/51 passing) MUST remain 100% functional without regressions.
