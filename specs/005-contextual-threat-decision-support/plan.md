# Implementation Plan: Feature 005 - Contextual Threat Assessment & Decision Support

**Branch**: `005-contextual-threat-decision-support` | **Date**: 2026-09-28 | **Spec**: [specs/005-contextual-threat-decision-support/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/005-contextual-threat-decision-support/spec.md)

---

## 1. High-Level Technical Architecture

Feature 005 introduces a modular **Spatial Zone Evaluator**, **Contextual Assessment Service**, and **Analyst Review Repository** to the existing Clean Architecture framework while preserving 100% of Feature 003 threat scoring logic:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Streamlit UI Deck (src/ui/)                       │
│  Surveillance Deck │ History Page │ Analytics Page │ Analyst Review Modal│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    Application Services (src/application/)             │
│   ImageSurveillanceService  │  VideoSurveillanceService                 │
│   ContextualAssessmentService (NEW) │ AnalystReviewService (NEW)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                   Domain Interfaces & Entities (src/domain/)            │
│   RestrictedZone  │ ObservableEvent │ SeparateContextualAssessment      │
│   AnalystReviewRecord │ AnalystReviewHistoryRecord │ IAnalystReviewRepo │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                 Infrastructure & Persistence (src/infrastructure/)      │
│   SpatialZoneEvaluator │ ThreatScoringService (Preserved 100% Baseline) │
│   ExplainabilityService │ AnalystReviewRepository (SQLite Tables)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown & Data Models

### Core Domain Entities (`src/domain/entities.py`)
- **`RestrictedZone`**: Normalized image-space zone configuration ($[0.0, 1.0]$ float scale: `zone_id`, `name`, `platform`, `camera_id`, `polygon_points`, `is_active`).
- **`ObservableEvent`**: Verifiable spatial/temporal behavior event (`event_id`, `track_id`, `class_name`, `event_type`, `timestamp_sec`, `description`, `confidence_score`, `is_uncertain`).
- **`SeparateContextualAssessment`**: Separate proposed spatial assessment presented alongside primary Feature 003 score (`spatial_score`, `spatial_level`, `computed_spatial_breach`, `events`).
- **`AnalystReviewRecord`**: Human analyst review record (`id`, `analysis_id`, `review_status`, `analyst_id`, `notes`, `created_at`, `updated_at`).
- **`AnalystReviewHistoryRecord`**: Review decision transition log (`history_id`, `review_id`, `analysis_id`, `from_status`, `to_status`, `analyst_id`, `notes`, `timestamp`).

### Domain Interfaces (`src/domain/interfaces.py`)
- **`ISpatialZoneEvaluator`**: Interface for normalized point-in-polygon geometry and resolution mapping.
- **`IContextualAssessmentService`**: Interface for observable behavior classification and separate spatial assessment generation.
- **`IAnalystReviewRepository`**: Abstract repository interface for SQLite persistence of `analyst_reviews` and `analyst_review_history`.
- **`IAnalystReviewService`**: Abstract application service interface for analyst review status transitions and audit logging.

### Infrastructure & Persistence (`src/infrastructure/`)
- **`SpatialZoneEvaluator`** (`src/infrastructure/services/spatial_zone_evaluator.py`): Pure Python / OpenCV point-in-polygon math (`cv2.pointPolygonTest` $\ge 0$) converting $[0.0, 1.0]$ normalized coordinates to image pixels.
- **`AnalystReviewRepository`** (`src/infrastructure/database/repositories.py`): Implements SQLite persistence for `analyst_reviews` and `analyst_review_history` tables.

### Application Services (`src/application/`)
- **`ContextualAssessmentService`** (`src/application/contextual_assessment_service.py`): Evaluates spatial zone intersections, classifies observable events (`ZONE_ENTRY`, `ZONE_TRANSIT`, `ROUTINE_TRANSIT`), and formats a Separate Proposed Spatial Assessment without mutating the primary Feature 003 threat score.
- **`AnalystReviewService`** (`src/application/analyst_review_service.py`): Manages analyst decision lifecycle, resolving default Analyst ID from `ConfigurationService` (`analyst.default_id`, default `"OPERATOR_01"`).

### Database Schema Updates (`src/core/database.py`)
Add SQLite tables `analyst_reviews` and `analyst_review_history`:
```sql
-- Main Analyst Review Table
CREATE TABLE IF NOT EXISTS analyst_reviews (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL UNIQUE,
    review_status TEXT NOT NULL CHECK (review_status IN ('PENDING_REVIEW', 'ACKNOWLEDGED', 'FALSE_POSITIVE', 'ESCALATED')),
    analyst_id TEXT NOT NULL DEFAULT 'OPERATOR_01',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

-- Audit History of Review State Transitions
CREATE TABLE IF NOT EXISTS analyst_review_history (
    history_id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    analysis_id TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    analyst_id TEXT NOT NULL,
    notes TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (review_id) REFERENCES analyst_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);
```

### Dependency Injection (`src/core/di_container.py`)
Register new services:
- `SpatialZoneEvaluator`
- `AnalystReviewRepository`
- `ContextualAssessmentService`
- `AnalystReviewService`

---

## 3. Preservation of Feature 003 Baseline & Score Independence

1. **Feature 003 Formula Unchanged**:
   $$\text{Threat Score} = \min\left(100.0, \Delta_{\text{baseline}} + \Delta_{\text{zone\_signal}} + \Delta_{\text{unauth\_signal}}\right)$$
   Where:
   - $\Delta_{\text{baseline}} = +5.0$ when detections present ($0.0$ if zero detections).
   - $\Delta_{\text{zone\_signal}} = +65.0$ when explicit zone violation signal is true ($0.0$ if false/absent).
   - $\Delta_{\text{unauth\_signal}} = +20.0$ when unauthorized access signal is true ($0.0$ if false/absent).
   - Thresholds: LOW $< 25.0$, MEDIUM $25.0$–$49.9$, HIGH $50.0$–$74.9$, CRITICAL $\ge 75.0$.
2. **No Points for Class, Count, or Movement**: Object classes, counts, crowding density, and movement speed NEVER contribute numerical threat points to Feature 003 score.
3. **Score Separation**: Any spatial score calculated from computed centroid zone intersection is formatted as a **Separate Proposed Spatial Assessment** and displayed independently in the UI.

---

## 4. Verification Plan

### Automated Unit & Integration Tests (`tests/`)
- `tests/unit/test_spatial_zone_evaluator.py`: Normalized coordinate mapping $[0.0, 1.0]$, point-in-polygon edge cases, invalid polygon rejection.
- `tests/unit/test_contextual_assessment_service.py`: Observable event classification, missing zone fallback, score separation guarantee.
- `tests/unit/test_analyst_review_repository.py`: SQLite persistence for `analyst_reviews` and `analyst_review_history` tables.
- `tests/unit/test_analyst_review_service.py`: Decision transitions (`PENDING_REVIEW` $\rightarrow$ `FALSE_POSITIVE` $\rightarrow$ `ACKNOWLEDGED`) and Analyst ID configuration fallback (`OPERATOR_01`).
- `tests/integration/test_contextual_threat_pipeline.py`: End-to-end test verifying video ingestion $\rightarrow$ YOLO detection $\rightarrow$ IoU tracking $\rightarrow$ spatial zone evaluation $\rightarrow$ Feature 003 threat score preservation $\rightarrow$ analyst review submission.

### Manual Verification Steps
1. Verify in UI that spatial zone boundary crossing displays as `"Computed Spatial Boundary Crossing"` distinct from `"Configured Scenario Metadata Signal"`.
2. Submit a `FALSE_POSITIVE` analyst review in UI, refresh application, and confirm that `analyses.threat_score` remains unchanged while review status displays `FALSE_POSITIVE`.
3. Check SQLite database to confirm audit trail row logged in `analyst_review_history`.
