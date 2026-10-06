"""Centralized Configuration Service module."""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigurationService:
    """Loads and manages application configuration parameters from YAML files."""

    YOLO_MODEL_PATH: str = "data/models/yolov8n_kiit_mita.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    VIDEO_TARGET_SAMPLE_FPS: float = 5.0
    MAX_VIDEO_DURATION_SECONDS: int = 120
    TRACKER_IOU_THRESHOLD: float = 0.30
    TRACKER_MAX_MISSED_FRAMES: int = 2
    MOVEMENT_PIXEL_THRESHOLD: float = 15.0
    DEFAULT_ANALYST_ID: str = "OPERATOR_01"

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(Path(__file__).parent.parent.parent / "config" / "system_config.yaml")
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reloads configuration from the YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """Gets a configuration parameter by dot-separated path (e.g. 'ai.confidence_threshold')."""
        keys = key_path.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def get_all(self) -> Dict[str, Any]:
        """Returns the full raw configuration dictionary."""
        return self._config
