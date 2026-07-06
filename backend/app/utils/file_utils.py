"""
file_utils.py — Stateless helpers for file validation.

These utilities are used by the document upload endpoint (Phase 2)
but are defined now so the validation contract is explicit and testable
independently of the upload route.
"""

import re
from typing import Optional


# Characters not allowed in stored filenames
_UNSAFE_FILENAME_RE = re.compile(r"[^\w\s\-.]")


def sanitize_filename(filename: str) -> str:
    """
    Strip path traversal sequences and non-alphanumeric characters from
    an uploaded filename, returning a safe basename.

    Example:
        sanitize_filename("../../etc/passwd")  → "etcpasswd"
        sanitize_filename("My Report (2024).pdf")  → "My_Report_2024.pdf"
    """
    # Drop any directory components (path traversal defence)
    basename = filename.replace("\\", "/").split("/")[-1]

    # Replace spaces with underscores, strip unsafe chars
    basename = basename.replace(" ", "_")
    basename = _UNSAFE_FILENAME_RE.sub("", basename)

    # Ensure we still have something left
    return basename or "unnamed_file"


def validate_mime_type(content_type: Optional[str], allowed: list[str]) -> bool:
    """
    Return True when content_type is in the allowed list.

    FastAPI surfaces the Content-Type of an UploadFile as file.content_type.
    Browsers sometimes append charset (e.g. 'text/plain; charset=utf-8'),
    so we compare only the base MIME type.
    """
    if not content_type:
        return False
    base_mime = content_type.split(";")[0].strip().lower()
    return base_mime in [m.lower() for m in allowed]


def validate_file_size(size_bytes: int, max_bytes: int) -> bool:
    """Return True when the file size is within the allowed limit."""
    return size_bytes <= max_bytes


def human_readable_bytes(size_bytes: int) -> str:
    """Format a byte count as a human-readable string (e.g. '4.2 MB')."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
