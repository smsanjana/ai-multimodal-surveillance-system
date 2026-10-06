# Data Model: Feature 005 - Contextual Threat Assessment & Decision Support

**Feature Branch**: `005-contextual-threat-decision-support` | **Date**: 2026-09-28 | **Spec**: [specs/005-contextual-threat-decision-support/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/005-contextual-threat-decision-support/spec.md)

---

## 1. Core Domain Entities & DTOs

### `RestrictedZone` (Dataclass)
Represents a geometric spatial zone defined in normalized image-space float coordinates ($[0.0, 1.0]$ scale).

```python
@dataclass
class RestrictedZone:
    zone_id: str
    name: str
    platform: str  # "DRONE" or "CCTV"
    camera_id: Optional[str]  # e.g., "CAM_02_RESTRICTED_GATE"
    polygon_points: List[Tuple[float, float]]  # [(x1, y1), (x2, y2), ...] in normalized [0.0, 1.0] scale
    is_active: bool = True
```

### `ObservableEvent` (Dataclass)
Represents a verifiable physical behavior event derived from object tracking telemetry.

```python
@dataclass
class ObservableEvent:
    event_id: str
    track_id: int
    class_name: str
    event_type: str  # "ROUTINE_TRANSIT", "PERIMETER_APPROACH", "ZONE_ENTRY", "ZONE_TRANSIT", "STATIONARY_OBJECT_IN_ZONE"
    timestamp_sec: float
    description: str
    confidence_score: float
    is_uncertain: bool = False
```

### `SeparateContextualAssessment` (Dataclass)
Separate proposed spatial assessment presented alongside primary Feature 003 threat score without altering Feature 003 score logic.

```python
@dataclass
class SeparateContextualAssessment:
    analysis_id: str
    spatial_threat_score: float
    spatial_threat_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    computed_spatial_breach: bool
    scenario_metadata_signal: bool
    events: List[ObservableEvent]
    xai_reason: str
    recommended_sop: str
```

### `AnalystReviewRecord` (Dataclass)
Represents a human analyst's current review decision.

```python
@dataclass
class AnalystReviewRecord:
    id: str
    analysis_id: str
    review_status: str  # "PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"
    analyst_id: str  # Resolved from config (default "OPERATOR_01")
    notes: Optional[str]
    created_at: str
    updated_at: str
```

### `AnalystReviewHistoryRecord` (Dataclass)
Represents a audit log row of review decision state transitions.

```python
@dataclass
class AnalystReviewHistoryRecord:
    history_id: str
    review_id: str
    analysis_id: str
    from_status: str
    to_status: str
    analyst_id: str
    notes: Optional[str]
    timestamp: str
```

---

## 2. SQLite Database Schema Extension

Feature 005 adds two new tables `analyst_reviews` and `analyst_review_history` to SQLite without modifying past tables (`analyses`, `detections`, `alerts`, `reports`, `settings`):

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

CREATE INDEX IF NOT EXISTS idx_analyst_reviews_analysis_id ON analyst_reviews(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analyst_reviews_status ON analyst_reviews(review_status);

-- Audit Trail of Review Decision Transitions
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

CREATE INDEX IF NOT EXISTS idx_review_history_review_id ON analyst_review_history(review_id);
```

---

## 3. Score Preservation & Schema Integrity

1. **AI Threat Score Preserved**: `analyses.threat_score` stores the primary Feature 003 threat score ($0.0$–$100.0$) and is **NEVER** modified when an analyst submits a review decision (`FALSE_POSITIVE` or `ACKNOWLEDGED`).
2. **Review Transition History**: Every update to `analyst_reviews.review_status` inserts a record into `analyst_review_history`, recording `from_status`, `to_status`, `analyst_id`, `notes`, and `timestamp`.
3. **Cascade Deletion**: Deleting an analysis from `analyses` automatically deletes corresponding entries in `analyst_reviews` and `analyst_review_history`.
