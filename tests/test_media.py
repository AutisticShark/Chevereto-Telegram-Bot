"""Tests for media type detection and utility functions."""

from __future__ import annotations

from chevereto_bot.utils.media import detect_media_info, format_file_size, is_media_allowed

PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"  # noqa: E501
JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
GIF_HEADER = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def test_detect_media_png():
    mime, ext = detect_media_info(PNG_HEADER, hint_filename="photo.unknown")
    assert mime == "image/png"
    assert ext == ".png"


def test_detect_media_jpeg():
    mime, ext = detect_media_info(JPEG_HEADER)
    assert mime == "image/jpeg"
    assert ext == ".jpg"


def test_detect_media_gif():
    mime, ext = detect_media_info(GIF_HEADER)
    assert mime == "image/gif"
    assert ext == ".gif"


def test_detect_media_fallback_from_hint():
    # Random bytes without known magic bytes
    random_bytes = b"just some text data not an image"
    mime, ext = detect_media_info(
        random_bytes, hint_filename="document.webp", hint_mime="image/webp"
    )
    assert mime == "image/webp"
    assert ext == ".webp"


def test_is_media_allowed():
    allowed_mimes = {"image/jpeg", "image/png", "video/mp4"}
    allowed_formats = {".jpg", ".jpeg", ".png", ".mp4"}

    assert is_media_allowed("image/png", ".png", allowed_mimes, allowed_formats) is True
    assert is_media_allowed("image/jpeg", ".jpg", allowed_mimes, allowed_formats) is True
    assert is_media_allowed("video/mp4", ".mp4", allowed_mimes, allowed_formats) is True
    assert is_media_allowed("application/pdf", ".pdf", allowed_mimes, allowed_formats) is False
    assert (
        is_media_allowed("application/x-msdownload", ".exe", allowed_mimes, allowed_formats)
        is False
    )


def test_format_file_size():
    assert format_file_size(500) == "500.0 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(1048576 * 5) == "5.0 MB"
    assert format_file_size(1073741824 * 2) == "2.0 GB"
