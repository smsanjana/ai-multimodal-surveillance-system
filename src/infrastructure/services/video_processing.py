"""Video Processing Service Module using OpenCV."""

import os
import math
import logging
from typing import Generator, Tuple, Optional, Union
import numpy as np
import cv2

from src.domain.interfaces import AbstractVideoProcessingService
from src.domain.entities import VideoMetadata
from src.core.exceptions import ValidationError, AnalysisProcessingError
from src.core.config import ConfigurationService

logger = logging.getLogger("SurveillanceSystem")


class VideoProcessingService(AbstractVideoProcessingService):
    """
    Handles OpenCV VideoCapture validation, metadata extraction, derived frame sampling,
    and temporary video file ingestion.
    """

    def __init__(self, max_duration_sec: float = ConfigurationService.MAX_VIDEO_DURATION_SECONDS):
        self.max_duration_sec = float(max_duration_sec)

    def validate_video(self, video_path: str) -> VideoMetadata:
        """
        Validates video file headers and extracts VideoMetadata DTO.
        Raises ValidationError if file is missing, unreadable, 0-frame, or exceeds max duration.
        """
        if not video_path or not os.path.exists(video_path):
            raise ValidationError(f"Video file path '{video_path}' does not exist.")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            raise ValidationError(f"Invalid or corrupted video file '{video_path}'. Unable to open video stream.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if total_frames <= 0 or width <= 0 or height <= 0:
            raise ValidationError(f"Video file '{video_path}' contains zero readable frames or invalid dimensions.")

        safe_fps = fps if fps > 0.0 else 25.0
        duration_sec = round(total_frames / safe_fps, 2)

        if duration_sec > self.max_duration_sec:
            raise ValidationError(
                f"Video duration ({duration_sec:.1f}s) exceeds maximum allowed limit of {self.max_duration_sec:.0f} seconds."
            )

        target_fps = ConfigurationService.VIDEO_TARGET_SAMPLE_FPS
        sample_step = max(1, int(round(safe_fps / target_fps)))
        sampled_frames = math.ceil(total_frames / sample_step)

        return VideoMetadata(
            file_path=video_path,
            duration_seconds=duration_sec,
            fps=safe_fps,
            total_frames=total_frames,
            sampled_frames=sampled_frames,
            width=width,
            height=height
        )

    def extract_sampled_frames(
        self, video_path: str, target_fps: float = ConfigurationService.VIDEO_TARGET_SAMPLE_FPS
    ) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """
        Derives sampling step from source video FPS targeting `target_fps` (default 5.0 FPS)
        and yields `(frame_index, timestamp_sec, frame_bgr)` for sampled frames.
        """
        metadata = self.validate_video(video_path)
        sample_step = max(1, int(round(metadata.fps / target_fps)))

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise AnalysisProcessingError(f"Failed to open video file for frame extraction: {video_path}")

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if frame_idx % sample_step == 0:
                    timestamp_sec = round(frame_idx / metadata.fps, 3)
                    yield (frame_idx, timestamp_sec, frame)

                frame_idx += 1
        finally:
            cap.release()

    def save_temp_upload(self, video_bytes: bytes, filename: str) -> str:
        """Saves raw uploaded video bytes to a temporary local file and returns its path."""
        if not video_bytes:
            raise ValidationError("Empty video payload uploaded.")

        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        safe_filename = os.path.basename(filename)
        temp_path = os.path.join(temp_dir, safe_filename)

        with open(temp_path, "wb") as f:
            f.write(video_bytes)

        return temp_path
