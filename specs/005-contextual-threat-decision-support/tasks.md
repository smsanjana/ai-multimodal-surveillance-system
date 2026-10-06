# Implementation Tasks: Feature 005 - Contextual Threat Assessment & Decision Support

**Branch**: `005-contextual-threat-decision-support` | **Date**: 2026-09-28 | **Spec**: [specs/005-contextual-threat-decision-support/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/005-contextual-threat-decision-support/spec.md) | **Plan**: [specs/005-contextual-threat-decision-support/plan.md](file:///Users/sanjana/Documents/ai_p2/specs/005-contextual-threat-decision-support/plan.md)

---

## Phase 1: Setup, Configuration & Data Model Extension

**Purpose**: Core domain entities, contracts, DTOs, Analyst ID config parameter, and SQLite database schema extensions.

- [ ] T001 [P] Add Analyst ID configuration parameter (`analyst.default_id: "OPERATOR_01"`) in `config/system_config.yaml` and getter method in `src/core/config.py`
- [ ] T002 [P] Add Feature 005 domain entities (`RestrictedZone`, `ObservableEvent`, `SeparateContextualAssessment`, `AnalystReviewRecord`, `AnalystReviewHistoryRecord`) in `src/domain/entities.py`
- [ ] T003 [P] Add abstract interfaces (`ISpatialZoneEvaluator`, `IContextualAssessmentService`, `IAnalystReviewRepository`, `IAnalystReviewService`) in `src/domain/interfaces.py`
- [ ] T004 Update SQLite schema in `src/core/database.py` to add `analyst_reviews` and `analyst_review_history` tables with foreign keys to `analyses(id)` without altering existing tables
- [ ] T005 Implement `AnalystReviewRepository` in `src/infrastructure/database/repositories.py` for SQLite CRUD operations and transition history logging

---

## Phase 2: User Story 1 - Normalized Spatial Zone Evaluation (Priority: P1) 🎯 MVP

**Purpose**: Implement normalized $[0.0, 1.0]$ spatial zone point-in-polygon math and compute spatial boundary crossings separately from scenario metadata flags.

### Unit Tests for User Story 1
- [ ] T006 [P] Unit test for `SpatialZoneEvaluator` in `tests/unit/test_spatial_zone_evaluator.py` (normalized $[0.0, 1.0]$ mapping, pixel conversion, boundary edge cases, invalid polygon rejection)
- [ ] T007 [P] Unit test for missing zone fallback in `tests/unit/test_contextual_assessment_service.py` (ensures open corridor fallback without errors)

### Implementation for User Story 1
- [ ] T008 Implement `SpatialZoneEvaluator` in `src/infrastructure/services/spatial_zone_evaluator.py` using OpenCV `cv2.pointPolygonTest` $\ge 0$ converting normalized coordinates to frame pixels
- [ ] T009 Implement `ContextualAssessmentService` in `src/application/contextual_assessment_service.py` evaluating normalized zone intersections and generating a Separate Proposed Spatial Assessment without modifying primary Feature 003 threat score
- [ ] T010 Register `SpatialZoneEvaluator` and `ContextualAssessmentService` in `src/core/di_container.py`
- [ ] T011 Update Surveillance UI in `src/ui/pages/surveillance.py` to display Spatial Zone & Computed Boundary Crossing card, explicitly separating computed spatial events from scenario metadata flags

---

## Phase 3: User Story 2 - Observable Event Analysis & Feature 003 XAI Preservation (Priority: P2)

**Purpose**: Categorize target behavior into verifiable observable events (`ZONE_ENTRY`, `ZONE_TRANSIT`, `STATIONARY_IN_ZONE`, `ROUTINE_TRANSIT`) and generate transparent XAI explanations using ONLY approved Feature 003 factors.

### Unit Tests for User Story 2
- [ ] T012 [P] Unit test for observable event classification and Feature 003 score preservation in `tests/unit/test_contextual_assessment_service.py` (verifying score baseline +5, +65 zone signal, +20 unauthorized signal, LOW < 25, MEDIUM 25-49, HIGH 50-74, CRITICAL >= 75)

### Implementation for User Story 2
- [ ] T013 Extend `ContextualAssessmentService` in `src/application/contextual_assessment_service.py` to classify target trajectories into `ObservableEvent` objects
- [ ] T014 Update `ExplainabilityService` in `src/infrastructure/services/explainability.py` to format step-by-step mathematical score breakdowns using ONLY approved Feature 003 factors
- [ ] T015 Update Surveillance UI deck in `src/ui/pages/surveillance.py` to render Observable Behavior Event timeline and XAI rationale breakdown

---

## Phase 4: User Story 3 - Human Analyst Review & Audit History Lifecycle (Priority: P3)

**Purpose**: Provide security analysts with an interactive review workflow (`PENDING_REVIEW`, `ACKNOWLEDGED`, `FALSE_POSITIVE`, `ESCALATED`) backed by transition audit logs in SQLite.

### Unit Tests for User Story 3
- [ ] T016 [P] Unit test for `AnalystReviewRepository` & `AnalystReviewService` in `tests/unit/test_analyst_review.py` (testing review status transitions, Analyst ID fallback, score preservation on `FALSE_POSITIVE`, and transition history logging)

### Implementation for User Story 3
- [ ] T017 Implement `AnalystReviewService` in `src/application/analyst_review_service.py` managing analyst decision lifecycle and resolving default Analyst ID from config
- [ ] T018 Register `AnalystReviewRepository` and `AnalystReviewService` in `src/core/di_container.py`
- [ ] T019 Add Analyst Review modal and status badge in `src/ui/pages/surveillance.py` and `src/ui/pages/history.py`
- [ ] T020 Update Analytics page in `src/ui/pages/analytics.py` to render Analyst Review metrics (Acknowledged vs False Positive ratio)

---

## Phase 5: End-to-End Integration & Regression Verification

**Purpose**: Execute comprehensive integration tests and full regression test suite verification.

- [ ] T021 Author integration test in `tests/integration/test_contextual_threat_pipeline.py` (verifying end-to-end pipeline: video ingestion -> YOLO detection -> IoU tracking -> spatial zone evaluation -> Feature 003 threat score preservation -> analyst review submission & history audit)
- [ ] T022 Run full regression test suite (`pytest tests/ -v`) to confirm 100% pass rate across Feature 001 through Feature 005
