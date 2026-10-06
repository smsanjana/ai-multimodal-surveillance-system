# Detection Service Interface Contract: Feature 003

**Feature**: [specs/003-military-object-detection/spec.md](file:///Users/sanjana/Documents/ai_p2/specs/003-military-object-detection/spec.md)  
**Module**: `src.domain.interfaces.AbstractDetectionService`  
**Implementation**: `src.infrastructure.services.yolo_detection.YoloDetectionService`

---

## 1. Abstract Service Contract

```python
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from src.domain.entities import DetectionResult

class AbstractDetectionService(ABC):

    @abstractmethod
    def detect(self, image: np.ndarray, confidence_threshold: Optional[float] = None) -> List[DetectionResult]:
        """
        Runs object detection on input numpy image (H, W, 3).
        
        :param image: Input image array (BGR or RGB).
        :param confidence_threshold: Optional threshold override (0.0 - 1.0).
        :return: List of DetectionResult items meeting or exceeding confidence threshold.
        :raises AnalysisProcessingError: On invalid input or inference failure.
        :raises ModelLoadError: If local weights file is missing or corrupt.
        """
        pass

    @abstractmethod
    def draw_annotations(self, image: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """
        Draws bounding box rectangles, labels, and confidence tags on a copy of the input image.
        
        :param image: Input image array (H, W, 3).
        :param detections: List of DetectionResult items to render.
        :return: Annotated image array copy (H, W, 3).
        """
        pass
```

---

## 2. Configuration Contract

```python
class ConfigurationContract:
    YOLO_MODEL_PATH: str = "data/models/yolov8n_kiit_mita.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
```
