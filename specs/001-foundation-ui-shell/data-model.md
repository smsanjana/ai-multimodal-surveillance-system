# Data Model & Schema Specification: Foundation and UI Shell

**Feature Identifier**: `specs/001-foundation-ui-shell`  
**Created**: 2026-09-13  
**Status**: Completed  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## 1. Relational Entities (SQLite Database)

### 1.1 `analyses` Table
Stores high-level metadata for every surveillance inspection session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `timestamp` | TEXT | NOT NULL | ISO-8601 UTC timestamp |
| `source_type` | TEXT | NOT NULL | `DEMO`, `UPLOAD`, or `LIVE` |
| `platform` | TEXT | NOT NULL | `DRONE` or `CCTV` |
| `media_type` | TEXT | NOT NULL | `IMAGE` or `VIDEO` |
| `scenario_name` | TEXT | NULLABLE | Scenario title if source is DEMO |
| `threat_score` | REAL | NOT NULL | Computed threat score (0.0 to 100.0) |
| `threat_level` | TEXT | NOT NULL | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `confidence_avg` | REAL | NOT NULL | Average object detection confidence (0.0 to 1.0) |
| `processing_time_ms` | REAL | NOT NULL | Pipeline execution duration in milliseconds |
| `status` | TEXT | NOT NULL | `COMPLETED`, `PENDING`, or `FAILED` |
| `artifact_path` | TEXT | NULLABLE | Relative path to annotated image/video artifact |

---

### 1.2 `detections` Table
Stores individual bounding box detections linked to an analysis session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `analysis_id` | TEXT | NOT NULL, FK(`analyses.id`) | Reference to parent analysis |
| `class_name` | TEXT | NOT NULL | Detected object class (e.g. `person`, `car`, `truck`) |
| `confidence` | REAL | NOT NULL | Detection confidence score (0.0 to 1.0) |
| `bbox_json` | TEXT | NOT NULL | Serialized JSON `{"x_min", "y_min", "x_max", "y_max"}` |
| `frame_index` | INTEGER | NULLABLE | Frame index for video inputs |

---

### 1.3 `threat_assessments` Table
Stores explainable AI (XAI) feature attribution and decision support SOPs.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `analysis_id` | TEXT | NOT NULL, FK(`analyses.id`) | Reference to parent analysis |
| `score` | REAL | NOT NULL | Calculated threat score (0.0 to 100.0) |
| `level` | TEXT | NOT NULL | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `xai_reason` | TEXT | NOT NULL | Human-readable explanation rationale |
| `recommended_sop` | TEXT | NOT NULL | Recommended standard operating procedure |

---

### 1.4 `alerts` Table
Stores operational security alerts generated from threat assessments.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `analysis_id` | TEXT | NOT NULL, FK(`analyses.id`) | Reference to parent analysis |
| `severity` | TEXT | NOT NULL | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `reason` | TEXT | NOT NULL | Trigger rationale summary |
| `status` | TEXT | NOT NULL | `UNACKNOWLEDGED`, `ACKNOWLEDGED`, or `RESOLVED` |
| `created_at` | TEXT | NOT NULL | ISO-8601 UTC timestamp |

---

### 1.5 `reports` Table
Stores audit records for generated incident summary reports.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `analysis_id` | TEXT | NOT NULL, FK(`analyses.id`) | Reference to parent analysis |
| `file_path` | TEXT | NOT NULL | Path to PDF/JSON artifact |
| `report_type` | TEXT | NOT NULL | `INCIDENT_SUMMARY`, `DAILY_AUDIT`, `FULL_EXPORT` |
| `generated_at` | TEXT | NOT NULL | ISO-8601 UTC timestamp |

---

### 1.6 `restricted_zones` Table
Stores configured polygon zones for spatial monitoring.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | UUID v4 string |
| `zone_name` | TEXT | NOT NULL | Name of zone (e.g. `Perimeter Alpha`) |
| `platform` | TEXT | NOT NULL | `DRONE` or `CCTV` |
| `polygon_json` | TEXT | NOT NULL | Serialized list of `[x, y]` vertices |
| `is_active` | INTEGER | NOT NULL DEFAULT 1 | 1 for active, 0 for inactive |

---

### 1.7 `settings` Table
Stores key-value application configuration defaults.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `key` | TEXT | PRIMARY KEY | Configuration key name |
| `value` | TEXT | NOT NULL | Configuration value string |
| `category` | TEXT | NOT NULL | `AI`, `VIDEO`, `THREAT`, `CAMERA`, `SYSTEM` |

---

## 2. Startup Seeding Data Specification

Upon initial startup, if `analyses` table contains 0 rows, `DatabaseService` executes idempotent insert statements seeding:
- 10 baseline `AnalysisRecord` entries representing historical drone/CCTV image and video runs across Low, Medium, High, and Critical threat levels.
- Associated `DetectionRecord`, `ThreatAssessmentRecord`, and `AlertRecord` entries.
- Initial system settings records (`model_path`, `confidence_threshold`, `threat_weights`, `theme`).
