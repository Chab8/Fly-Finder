"""Upload validation and normalization.

Formats are detected from the file content (not the filename or the client-declared
content type). Output is an EXIF-stripped, orientation-corrected RGB JPEG, which also
removes GPS metadata from user photos.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field

import numpy as np
import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import ImageTooLargeError, InvalidImageError

pillow_heif.register_heif_opener()

# Pillow format name -> MIME type. HEIF covers both .heic and .heif files.
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "HEIF": "image/heic"}
MIN_SIDE_PX = 224
LOW_RESOLUTION_SIDE_PX = 480
MAX_PIXELS = 50_000_000  # decompression-bomb guard
TARGET_LONG_SIDE_PX = 1536
JPEG_QUALITY = 88
# Variance of the Laplacian on a 512px grayscale copy. Below this the photo is probably
# out of focus. Heuristic: tuned on a handful of samples, used only as a warning.
BLUR_THRESHOLD = 40.0


@dataclass(frozen=True)
class ProcessedImage:
    jpeg_bytes: bytes
    image: Image.Image
    width: int
    height: int
    original_format: str
    sha256: str
    sharpness: float
    warnings: list[str] = field(default_factory=list)

    mime_type: str = "image/jpeg"


def _sharpness(image: Image.Image) -> float:
    gray = image.convert("L")
    gray.thumbnail((512, 512))
    a = np.asarray(gray, dtype=np.float32)
    if a.shape[0] < 3 or a.shape[1] < 3:
        return 0.0
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def process_image(data: bytes, *, max_bytes: int) -> ProcessedImage:
    if not data:
        raise InvalidImageError("The uploaded file is empty.", code="empty_file")
    if len(data) > max_bytes:
        raise ImageTooLargeError(f"Image exceeds the {max_bytes // (1024 * 1024)} MB limit.")

    try:
        source = Image.open(io.BytesIO(data))
        fmt = source.format or ""
        if fmt not in ALLOWED_FORMATS:
            raise InvalidImageError(
                "Unsupported image format. Use JPEG, PNG, WEBP or HEIC.", code="unsupported_format",
                details={"detected_format": fmt or "unknown"},
            )
        if source.width * source.height > MAX_PIXELS:
            raise InvalidImageError("Image dimensions are too large.", code="image_dimensions_too_large")
        source.load()
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("The file is not a readable image.", code="unreadable_image") from exc

    image = _to_rgb(ImageOps.exif_transpose(source))
    if min(image.size) < MIN_SIDE_PX:
        raise InvalidImageError(
            f"Image is too small. The shortest side must be at least {MIN_SIDE_PX}px.", code="image_too_small",
            details={"width": image.width, "height": image.height},
        )

    warnings = []
    if min(image.size) < LOW_RESOLUTION_SIDE_PX:
        warnings.append("low_resolution")
    image.thumbnail((TARGET_LONG_SIDE_PX, TARGET_LONG_SIDE_PX), Image.Resampling.LANCZOS)
    sharpness = _sharpness(image)
    if sharpness < BLUR_THRESHOLD:
        warnings.append("possibly_blurry")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)  # no exif= -> metadata dropped
    jpeg = buffer.getvalue()
    return ProcessedImage(
        jpeg_bytes=jpeg, image=image, width=image.width, height=image.height, original_format=fmt,
        sha256=hashlib.sha256(data).hexdigest(), sharpness=sharpness, warnings=warnings,
    )
