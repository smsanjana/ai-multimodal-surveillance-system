# Data Model & Schema Specification: Feature 003 — Military Object Detection Integration

**Feature**: [specs/003-military-object-detection/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)  
**Date**: 2026-09-13

---

## 1. Domain Entities & Value Objects

### 1.1 `BoundingBox` (Value Object)
Represents normalized or absolute 2D bounding box spatial coordinates.

```python
class BoundingBox:
    x_min: float  # Left coordinate (pixels)
    y_min: float  # Top coordinate (pixels)
    x_max: float  # Right coordinate (pixels)
    y_max: float  # Bottom coordinate (pixels)
```

### 1.2 `DetectionResult` (Domain Entity)
Encapsulates a single object detection observation returned by the military YOLO model.

```python
class DetectionResult:
    detection_id: str         # Unique UUID string
    class_id: int             # Class index (0 to 6)
    class_name: str           # Human-readable name ('Artilary', 'Missile', 'Radar', 'M. Rocket Launcher', 'Soldier', 'Tank', 'Vehicle')
    confidence: float         # Confidence score (0.0 to 1.0)
    bbox: BoundingBox         # Bounding box coordinates
```

### 1.3 `SurveillanceAnalysis` (Aggregate Root)
Encapsulates the complete surveillance analysis event, preserving dual image references (original and annotated), raw detections, threat evaluation, and audit metadata.

```python
class SurveillanceAnalysis:
    analysis_id: str                  # Unique analysis UUID
    image_path: str                   # Path to clean original input image
    annotated_image_path: str         # Path to rendered detection image with bounding boxes
    source_platform: str              # Platform metadata ('Drone' or 'CCTV')
    detections: List[DetectionResult] # List of detections meeting confidence threshold
    threat_level: str                 # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    threat_score: float               # Deterministic score (0.0 to 100.0)
    explanation: str                  # XAI natural language reasoning text
    created_at: str                   # ISO 8601 timestamp string
```

---

## 2. KIIT-MiTA Class Mapping Schema

The 7 supported military target categories map deterministically as follows:

| Class ID | Canonical Class Name | Display String | Category Description |
| :---: | :--- | :--- | :--- |
| `0` | `Artilary` | Artilary | Heavy towed/stationary field gun or howitzer |
| `1` | `Missile` | Missile | Guided missile system or transport unit |
| `2` | `Radar` | Radar | Surveillance/fire-control radar antenna platform |
| `3` | `M. Rocket Launcher` | M. Rocket Launcher | Multiple launch rocket system (MLRS) vehicle |
| `4` | `Soldier` | Soldier | Military personnel in field uniform |
| `5` | `Tank` | Tank | Armored tracked combat vehicle / MBT |
| `6` | `Vehicle` | Military Vehicle | Military truck, transport, or utility vehicle |

---

## 3. Database Schema & Persistence Contract

The existing SQLite database schema (`analyses` table) managed by `DatabaseService` stores JSON-serialized detection records and image paths. 

```sql
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    image_path TEXT NOT NULL,
    annotated_image_path TEXT,
    source_platform TEXT NOT NULL,
    threat_level TEXT NOT NULL,
    threat_score REAL NOT NULL,
    explanation TEXT NOT NULL,
    detections_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### Serialization Contract
* `detections_json`: JSON string encoding an array of detection objects:
  ```json
  [
    {
      "detection_id": "550e8400-e29b-41d4-a716-446655440000",
      "class_id": 5,
      "class_name": "Tank",
      "confidence": 0.8752,
      "bbox": {
        "x_min": 120.0,
        "y_min": 85.5,
        "x_max": 450.0,
        "y_max": 310.0
      }
    }
  ]
  ```
