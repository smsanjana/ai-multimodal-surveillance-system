"""Unit tests for VideoProcessingService."""

import pytest
import os
import tempfile
import numpy as np
import cv2

from src.infrastructure.services.video_processing import VideoProcessingService
from src.core.exceptions import ValidationError, AnalysisProcessingError


@pytest.fixture
def video_service():
    return VideoProcessingService(max_duration_sec=120.0)


@pytest.fixture
def temp_sample_video():
    """Generates a temporary valid 2-second MP4 video file at 25 FPS (50 frames)."""
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    h, w = 720, 1280
    fps = 25.0
    num_frames = 50
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))

    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))

    for i in range(num_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)
        cv2.circle(frame, (100 + i * 5, 200), 20, (0, 255, 0), -1)
        out.write(frame)

    out.release()
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_long_video():
    """Generates a temporary header-valid video metadata object simulating >120s video."""
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    h, w = 100, 100
    fps = 10.0
    num_frames = 1300  # 130 seconds > 120s limit
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))

    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))

    for i in range(num_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        out.write(frame)

    out.release()
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_validate_video_success(video_service, temp_sample_video):
    metadata = video_service.validate_video(temp_sample_video)
    assert metadata.file_path == temp_sample_video
    assert metadata.duration_seconds == 2.0
    assert metadata.fps == 25.0
    assert metadata.total_frames == 50
    assert metadata.sampled_frames == 10  # 25 FPS targeting 5 FPS = 1 frame every 5 frames = 10 frames
    assert metadata.width == 1280
    assert metadata.height == 720


def test_validate_video_missing_file(video_service):
    with pytest.raises(ValidationError) as excinfo:
        video_service.validate_video("non_existent_video.mp4")
    assert "does not exist" in str(excinfo.value)


def test_validate_video_exceeds_max_duration(video_service, temp_long_video):
    with pytest.raises(ValidationError) as excinfo:
        video_service.validate_video(temp_long_video)
    assert "exceeds maximum allowed limit of 120 seconds" in str(excinfo.value)


def test_extract_sampled_frames(video_service, temp_sample_video):
    frames = list(video_service.extract_sampled_frames(temp_sample_video, target_fps=5.0))
    # 50 total frames at 25 FPS -> step = 5 -> sampled frames at idx 0, 5, 10, 15, 20, 25, 30, 35, 40, 45
    assert len(frames) == 10
    frame_idx, timestamp_sec, frame_bgr = frames[0]
    assert frame_idx == 0
    assert timestamp_sec == 0.0
    assert isinstance(frame_bgr, np.ndarray)
    assert frame_bgr.shape == (720, 1280, 3)


def test_save_temp_upload(video_service):
    raw_bytes = b"dummy_video_content"
    temp_path = video_service.save_temp_upload(raw_bytes, "test_upload.mp4")
    assert os.path.exists(temp_path)
    with open(temp_path, "rb") as f:
        assert f.read() == raw_bytes
    os.remove(temp_path)
