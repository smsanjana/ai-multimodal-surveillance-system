"""Centralized Application Exception Definitions & Handling."""

import logging
from typing import Tuple

logger = logging.getLogger("SurveillanceSystem")


class SurveillanceBaseException(Exception):
    """Base exception class for the Surveillance System."""
    def __init__(self, message: str, user_message: str = "An unexpected system error occurred."):
        super().__init__(message)
        self.message = message
        self.user_message = user_message


class ConfigurationError(SurveillanceBaseException):
    """Raised when configuration file parsing or parameter retrieval fails."""
    def __init__(self, message: str):
        super().__init__(message, user_message="Configuration parameter could not be loaded.")


class DatabaseError(SurveillanceBaseException):
    """Raised when SQLite operations fail."""
    def __init__(self, message: str):
        super().__init__(message, user_message="Database operation failed. Please check system logs.")


class RepositoryError(SurveillanceBaseException):
    """Raised when repository data access fails."""
    def __init__(self, message: str):
        super().__init__(message, user_message="Failed to retrieve operational data.")


class InvalidInputError(SurveillanceBaseException):
    """Raised when input media or configuration validation fails."""
    def __init__(self, message: str):
        super().__init__(message, user_message="The provided input source or setting is invalid.")


class ValidationError(InvalidInputError):
    """Raised when general input validation (e.g. video duration, format) fails."""
    def __init__(self, message: str):
        super().__init__(message)
        self.user_message = message


class ImageValidationError(SurveillanceBaseException):
    """Raised when image file validation fails (corrupt headers, wrong format, size limit)."""
    def __init__(self, message: str):
        super().__init__(message, user_message="Invalid image file. Please upload a valid JPG or PNG image.")


class ModelLoadError(SurveillanceBaseException):
    """Raised when model weights file missing or model loading fails."""
    def __init__(self, message: str):
        super().__init__(message, user_message="AI Model weights could not be loaded. Verify local model asset path.")


class AnalysisProcessingError(SurveillanceBaseException):
    """Raised when an error occurs during detection, scoring, or persistence pipeline."""
    def __init__(self, message: str):
        super().__init__(message, user_message="An error occurred while processing surveillance analysis.")



class ExceptionHandler:
    """Utility class to log backend errors and produce clean user messages."""

    @staticmethod
    def handle_exception(exc: Exception) -> Tuple[str, str]:
        """Logs detailed technical exception traceback and returns (technical_msg, user_friendly_msg)."""
        if isinstance(exc, SurveillanceBaseException):
            logger.error("Domain Exception [%s]: %s", exc.__class__.__name__, exc.message)
            return exc.message, exc.user_message

        logger.exception("Unhandled System Exception: %s", str(exc))
        return str(exc), "An internal system error occurred. Operations logged for administrator review."
