# Interface Contracts: Image Surveillance Processing

**Feature Identifier**: `specs/002-image-surveillance-processing`  
**Date**: 2026-09-13  
**Status**: Draft  

---

## 1. Core Domain Interfaces (`src/domain/interfaces.py`)

### AbstractDetectionService
Decouples object detection model implementations from application and UI code.

```python
from abc import ABC, abstractmethod
from typing import List
import numpy as np
from src.domain.entities import DetectionResult

class AbstractDetectionService(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.25) -> List[DetectionResult]:
        """
        Executes object detection on an RGB/BGR image array.
        
        :param image: Input image as numpy array (H, W, C).
        :param confidence_threshold: Minimum confidence filter threshold.
        :return: List of structured DetectionResult DTOs.
        """
        pass
```

---

### AbstractThreatScoringService
Evaluates detection results and scenario metadata to compute a quantitative threat score and classification.

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.domain.entities import DetectionResult, ThreatAssessmentResult

class AbstractThreatScoringService(ABC):
    @abstractmethod
    def evaluate_threat(
        self, 
        detections: List[DetectionResult], 
        metadata: Dict[str, Any]
    ) -> ThreatAssessmentResult:
        """
        Evaluates detection results into a 0.0-100.0 score mapped to LOW, MEDIUM, HIGH, CRITICAL.
        
        :param detections: List of object detections.
        :param metadata: Input scenario metadata (platform, source_type, zone_violation_flag, etc.).
        :return: Structured ThreatAssessmentResult DTO.
        """
        pass
```

---

### AbstractExplainabilityService
Generates natural language rationale and factor contributions explaining the threat score.

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.domain.entities import DetectionResult, FactorContribution

class AbstractExplainabilityService(ABC):
    @abstractmethod
    def explain(
        self, 
        threat_score: float, 
        threat_level: str, 
        detections: List[DetectionResult], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates factor contributions, natural language explanation summary, and SOP recommendations.
        """
        pass
```

---

## 2. Application Layer Contract (`src/application/image_surveillance_service.py`)

### ImageSurveillanceService
High-level use case orchestrator consumed by presentation components (Streamlit pages).

```python
from src.domain.entities import ImageAnalysisRequest, ImageAnalysisResponse

class ImageSurveillanceService:
    def process_image(self, request: ImageAnalysisRequest) -> ImageAnalysisResponse:
        """
        Orchestrates full image processing pipeline:
        1. Validate input media
        2. Execute object detection
        3. Annotate bounding boxes onto image
        4. Calculate contextual threat score & level
        5. Generate XAI rationale and SOP recommendation
        6. Automatically persist record to SQLite
        7. Return structured ImageAnalysisResponse payload
        """
        pass
```

---

## 3. Repository Layer Interface (`src/domain/interfaces.py`)

### IAnalysisRepository
Provides persistence access for image analysis records and detections.

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IAnalysisRepository(ABC):
    @abstractmethod
    def save_analysis(self, analysis_data: Dict[str, Any], detections_data: List[Dict[str, Any]]) -> str:
        """
        Persists analysis record and associated detection items to SQLite database.
        Returns the generated analysis_id UUID.
        """
        pass
```
