"""Image Validation Service for validating uploaded image files."""

import io
from typing import Union, Tuple
from PIL import Image, ImageOps
from src.core.exceptions import ImageValidationError

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/pjpeg"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


class ImageValidator:
    """Validates raw image bytes or file paths for integrity, format, and dimensions."""

    @staticmethod
    def validate_image(image_input: Union[bytes, str]) -> Tuple[bytes, Tuple[int, int]]:
        """
        Validates an image payload or file path.

        :param image_input: Image binary bytes or local filesystem path string.
        :return: Tuple of (validated_image_bytes, (width, height)).
        :raises ImageValidationError: If validation fails.
        """
        if not image_input:
            raise ImageValidationError("Empty image payload provided.")

        image_bytes: bytes
        if isinstance(image_input, str):
            try:
                with open(image_input, "rb") as f:
                    image_bytes = f.read()
            except Exception as e:
                raise ImageValidationError(f"Could not read image file from path '{image_input}': {e}")
        elif isinstance(image_input, bytes):
            image_bytes = image_input
        else:
            raise ImageValidationError("Unsupported input type for image validation.")

        if len(image_bytes) == 0:
            raise ImageValidationError("Image payload is 0 bytes.")

        if len(image_bytes) > MAX_FILE_SIZE_BYTES:
            raise ImageValidationError(f"Image payload size ({len(image_bytes)} bytes) exceeds max limit of {MAX_FILE_SIZE_BYTES} bytes.")

        # Header signature validation
        if not (image_bytes.startswith(b"\xff\xd8\xff") or image_bytes.startswith(b"\x89PNG\r\n\x1a\n")):
            raise ImageValidationError("File header does not match a valid JPEG or PNG image signature.")

        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img.verify()
        except Exception as e:
            raise ImageValidationError(f"Corrupt or unreadable image file: {e}")

        # Re-open for metadata extraction as verify() clears buffers
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            width, height = pil_img.size
            if width <= 0 or height <= 0:
                raise ImageValidationError(f"Invalid image dimensions ({width}x{height}).")
            return image_bytes, (width, height)
        except ImageValidationError:
            raise
        except Exception as e:
            raise ImageValidationError(f"Failed to inspect image dimensions: {e}")
