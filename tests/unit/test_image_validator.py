"""Unit tests for ImageValidator service."""

import pytest
import io
from PIL import Image
from src.infrastructure.services.image_validator import ImageValidator
from src.core.exceptions import ImageValidationError


def test_image_validator_valid_png():
    # Create valid in-memory PNG image
    img = Image.new("RGB", (640, 480), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_bytes = buf.getvalue()

    out_bytes, (w, h) = ImageValidator.validate_image(valid_bytes)
    assert out_bytes == valid_bytes
    assert w == 640
    assert h == 480


def test_image_validator_valid_jpeg():
    # Create valid in-memory JPEG image
    img = Image.new("RGB", (1280, 720), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    valid_bytes = buf.getvalue()

    out_bytes, (w, h) = ImageValidator.validate_image(valid_bytes)
    assert out_bytes == valid_bytes
    assert w == 1280
    assert h == 720


def test_image_validator_empty_bytes():
    with pytest.raises(ImageValidationError):
        ImageValidator.validate_image(b"")


def test_image_validator_corrupt_header():
    corrupt_bytes = b"NOT_AN_IMAGE_HEADER_1234567890"
    with pytest.raises(ImageValidationError):
        ImageValidator.validate_image(corrupt_bytes)
