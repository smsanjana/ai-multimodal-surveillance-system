# Service Contracts: Feature 005 - Contextual Threat Assessment & Decision Support

**Feature Branch**: `005-contextual-threat-decision-support` | **Date**: 2026-09-28 | **Spec**: [specs/005-contextual-threat-decision-support/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/005-contextual-threat-decision-support/spec.md)

---

## 1. `ISpatialZoneEvaluator` Contract

```python
from abc import ABC, abstractmethod
from typing import List, Tuple
from src.domain.entities import RestrictedZone, BoundingBox

class ISpatialZoneEvaluator(ABC):
    """Abstract interface for normalized spatial zone geometry evaluation."""

    @abstractmethod
    def convert_normalized_polygon_to_pixels(
        self, polygon_norm: List[Tuple[float, float]], width: int, height: int
    ) -> List[Tuple[int, int]]:
        """Converts normalized float polygon [0.0, 1.0] to frame pixel coordinates."""
        pass

    @abstractmethod
    def is_centroid_in_zone(
        self, centroid_norm: Tuple[float, float], zone: RestrictedZone
    ) -> bool:
        """Evaluates whether normalized centroid (x, y) intersects zone (polygon boundary inclusive)."""
        pass
```

---

## 2. `IContextualAssessmentService` Contract

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities import (
    DetectionResult, TrackRecord, RestrictedZone, SeparateContextualAssessment
)

class IContextualAssessmentService(ABC):
    """Abstract interface for Spatial Zone & Observable Behavior Event Service."""

    @abstractmethod
    def evaluate_spatial_context(
        self,
        analysis_id: str,
        detections: List[DetectionResult],
        tracks: List[TrackRecord],
        platform: str,
        zones: Optional[List[RestrictedZone]] = None,
        scenario_metadata_signal: bool = False
    ) -> SeparateContextualAssessment:
        """
        Orchestrates spatial zone evaluation:
        1. Evaluates target centroids against normalized spatial zones [0.0, 1.0].
        2. Computes spatial boundary crossing events.
        3. Classifies observable behavior events (ZONE_ENTRY, ZONE_TRANSIT, ROUTINE_TRANSIT).
        4. Formats Separate Proposed Spatial Assessment without mutating primary Feature 003 score.
        """
        pass
```

---

## 3. `IAnalystReviewRepository` Contract

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities import AnalystReviewRecord, AnalystReviewHistoryRecord

class IAnalystReviewRepository(ABC):
    """Abstract repository interface for SQLite persistence of analyst reviews and history."""

    @abstractmethod
    def save_review(
        self, review: AnalystReviewRecord, history_entry: AnalystReviewHistoryRecord
    ) -> AnalystReviewRecord:
        """Persists or updates an analyst review record and appends a transition history row in SQLite."""
        pass

    @abstractmethod
    def get_review_by_analysis_id(self, analysis_id: str) -> Optional[AnalystReviewRecord]:
        """Retrieves analyst review record for analysis_id, returning None if unreviewed."""
        pass

    @abstractmethod
    def get_review_history(self, review_id: str) -> List[AnalystReviewHistoryRecord]:
        """Retrieves full transition history for a review ID."""
        pass
```

---

## 4. `IAnalystReviewService` Contract

```python
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities import AnalystReviewRecord

class IAnalystReviewService(ABC):
    """Abstract application service interface for human analyst review workflow."""

    @abstractmethod
    def submit_review(
        self,
        analysis_id: str,
        review_status: str,  # PENDING_REVIEW, ACKNOWLEDGED, FALSE_POSITIVE, ESCALATED
        analyst_id: Optional[str] = None,  # Resolves from config if None
        notes: Optional[str] = None
    ) -> AnalystReviewRecord:
        """Submits human analyst review decision and logs audit transition in SQLite."""
        pass
```
