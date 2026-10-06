"""Structured Logging Module."""

import logging
from pathlib import Path
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configures structured logger with console and optional file handlers."""
    logger = logging.getLogger("SurveillanceSystem")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger  # Already initialized

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
