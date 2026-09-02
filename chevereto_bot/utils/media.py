"""Pure-Python media type detection and validation."""

from __future__ import annotations

import mimetypes
from pathlib import Path

import filetype


def detect_media_info(
    content: bytes, hint_filename: str | None = None, hint_mime: str | None = None
) -> tuple[str, str]:
    """Detect MIME type and file extension without external C libraries.

    Returns:
        tuple[str, str]: (mime_type, file_extension_with_dot)
    """
    # 1. Try filetype sniffing (matches file signature/magic bytes)
    kind = filetype.guess(content)
    if kind is not None:
        ext = f".{kind.extension.lower()}"
        return kind.mime.lower(), ext

    # 2. Check hint_mime from Telegram (if reliable)
    if hint_mime and "/" in hint_mime:
        ext = mimetypes.guess_extension(hint_mime) or ""
        return hint_mime.lower(), ext.lower()

    # 3. Check filename extension
    if hint_filename:
        ext = Path(hint_filename).suffix.lower()
        guessed_mime, _ = mimetypes.guess_type(hint_filename)
        if guessed_mime:
            return guessed_mime.lower(), ext
        if ext:
            return "application/octet-stream", ext

    return "application/octet-stream", ".bin"


def is_media_allowed(
    mime: str,
    ext: str,
    allowed_mimes: set[str],
    allowed_formats: set[str],
) -> bool:
    """Validate whether the detected mime and extension are in the allowed lists."""
    ext_clean = ext.lower().strip()
    if not ext_clean.startswith(".") and ext_clean:
        ext_clean = f".{ext_clean}"

    # Normalize allowed formats with leading dots
    normalized_formats = {f if f.startswith(".") else f".{f}" for f in allowed_formats}

    # Match mime or extension
    mime_matched = mime.lower().strip() in {m.lower().strip() for m in allowed_mimes}
    ext_matched = ext_clean in {f.lower().strip() for f in normalized_formats}

    return mime_matched or ext_matched


def format_file_size(size_in_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_in_bytes) < 1024.0:
            return f"{size_in_bytes:3.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"
