import io

import pillow_heif
import pytest
from PIL import Image

from app.core.errors import ImageTooLargeError, InvalidImageError
from app.services.images.processing import TARGET_LONG_SIDE_PX, process_image
from tests.conftest import make_image_bytes

MB = 1024 * 1024


def test_jpeg_is_normalized_and_resized():
    result = process_image(make_image_bytes(size=(4000, 3000)), max_bytes=20 * MB)
    assert max(result.width, result.height) == TARGET_LONG_SIDE_PX
    assert Image.open(io.BytesIO(result.jpeg_bytes)).format == "JPEG"
    assert result.original_format == "JPEG"
    assert len(result.sha256) == 64


@pytest.mark.parametrize("fmt", ["PNG", "WEBP"])
def test_png_and_webp_accepted(fmt):
    assert process_image(make_image_bytes(fmt), max_bytes=20 * MB).original_format == fmt


def test_png_with_alpha_is_flattened_to_rgb():
    result = process_image(make_image_bytes("PNG", mode="RGBA"), max_bytes=20 * MB)
    assert result.image.mode == "RGB"


def test_heic_accepted_and_converted_to_jpeg():
    image = Image.open(io.BytesIO(make_image_bytes()))
    buffer = io.BytesIO()
    pillow_heif.from_pillow(image).save(buffer, quality=80)
    result = process_image(buffer.getvalue(), max_bytes=20 * MB)
    assert result.original_format == "HEIF"
    assert Image.open(io.BytesIO(result.jpeg_bytes)).format == "JPEG"


def test_unsupported_format_rejected_by_content_not_extension():
    with pytest.raises(InvalidImageError) as exc:
        process_image(make_image_bytes("GIF"), max_bytes=20 * MB)
    assert exc.value.code == "unsupported_format"


def test_non_image_bytes_rejected():
    with pytest.raises(InvalidImageError) as exc:
        process_image(b"%PDF-1.7 not an image" * 50, max_bytes=20 * MB)
    assert exc.value.code == "unreadable_image"


def test_empty_file_rejected():
    with pytest.raises(InvalidImageError) as exc:
        process_image(b"", max_bytes=MB)
    assert exc.value.code == "empty_file"


def test_too_large_rejected():
    with pytest.raises(ImageTooLargeError):
        process_image(make_image_bytes(size=(2000, 2000)), max_bytes=1000)


def test_too_small_rejected():
    with pytest.raises(InvalidImageError) as exc:
        process_image(make_image_bytes(size=(100, 100)), max_bytes=MB)
    assert exc.value.code == "image_too_small"


def test_low_resolution_and_blur_warnings():
    result = process_image(make_image_bytes(size=(300, 300), flat=True), max_bytes=MB)
    assert "low_resolution" in result.warnings
    assert "possibly_blurry" in result.warnings


def test_sharp_image_has_no_blur_warning():
    assert "possibly_blurry" not in process_image(make_image_bytes(), max_bytes=20 * MB).warnings


def test_exif_metadata_including_gps_is_removed():
    image = Image.open(io.BytesIO(make_image_bytes()))
    exif = Image.Exif()
    exif[0x8825] = {2: (34.0, 36.0, 0.0)}  # GPSInfo
    exif[0x010F] = "PhoneMaker"
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    assert Image.open(io.BytesIO(buffer.getvalue())).getexif()
    result = process_image(buffer.getvalue(), max_bytes=20 * MB)
    assert not Image.open(io.BytesIO(result.jpeg_bytes)).getexif()


def test_exif_orientation_applied():
    image = Image.open(io.BytesIO(make_image_bytes(size=(800, 400))))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    result = process_image(buffer.getvalue(), max_bytes=20 * MB)
    assert result.height > result.width
