"""
IntelliPrint Nexus — Input Validation & Sanitization Layer
======================================================
Centralized validation for all user inputs, file uploads, print options,
and database parameters.  Every entry point into the system should call
the appropriate validator before processing.

Design principles:
- Raise ``ValidationError`` on failure (never return None silently)
- Validate early — before any DB query or file I/O
- Never expose internal paths or DB details in error messages
- All functions are pure (no side effects) and testable

Usage::

    from smartcore.validators import validate_username, validate_email

    validate_username(username)   # raises ValidationError if invalid
    validate_email(email)         # raises ValidationError if invalid
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Optional, Tuple

from smartcore.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    PathTraversalError,
    ValidationError,
)

# ── Configuration (inline to avoid circular import at module load time) ────
_USERNAME_MIN = 3
_USERNAME_MAX = 50
_PASSWORD_MIN = 6
_PASSWORD_MAX = 128
_EMAIL_MAX = 120
_MAX_UPLOAD_MB = 50.0
_ALLOWED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp")
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
# RFC 5322 simplified — covers 99.9 % of real addresses
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


# ── Username ───────────────────────────────────────────────────────────────


def validate_username(username: str) -> str:
    """
    Validate and normalise a username.

    Rules:
    - Must be a non-empty string
    - Length: 3–50 characters
    - Allowed chars: letters, digits, ``_``, ``-``, ``.``

    Returns the stripped username.
    Raises ``ValidationError`` on failure.
    """
    if not isinstance(username, str):
        raise ValidationError("Username must be a string.", field="username")
    username = username.strip()
    if len(username) < _USERNAME_MIN:
        raise ValidationError(
            f"Username must be at least {_USERNAME_MIN} characters.",
            field="username", code="USERNAME_TOO_SHORT",
        )
    if len(username) > _USERNAME_MAX:
        raise ValidationError(
            f"Username must not exceed {_USERNAME_MAX} characters.",
            field="username", code="USERNAME_TOO_LONG",
        )
    if not _USERNAME_RE.match(username):
        raise ValidationError(
            "Username may only contain letters, digits, underscores, hyphens, and dots.",
            field="username", code="USERNAME_INVALID_CHARS",
        )
    return username


# ── Email ──────────────────────────────────────────────────────────────────


def validate_email(email: str) -> str:
    """
    Validate and normalise an email address.

    Returns the stripped, lowercased email.
    Raises ``ValidationError`` on failure.
    """
    if not isinstance(email, str):
        raise ValidationError("Email must be a string.", field="email")
    email = email.strip().lower()
    if not email:
        raise ValidationError("Email address is required.", field="email", code="EMAIL_REQUIRED")
    if len(email) > _EMAIL_MAX:
        raise ValidationError(
            f"Email must not exceed {_EMAIL_MAX} characters.",
            field="email", code="EMAIL_TOO_LONG",
        )
    if not _EMAIL_RE.match(email):
        raise ValidationError("Invalid email address format.", field="email", code="EMAIL_INVALID")
    return email


# ── Password ───────────────────────────────────────────────────────────────


def validate_password(password: str) -> str:
    """
    Validate password strength.

    Rules:
    - Minimum 6 characters (configurable)
    - Maximum 128 characters
    - Must not be blank

    Returns the original password (unhashed).
    Raises ``ValidationError`` on failure.
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string.", field="password")
    if len(password) < _PASSWORD_MIN:
        raise ValidationError(
            f"Password must be at least {_PASSWORD_MIN} characters.",
            field="password", code="PASSWORD_TOO_SHORT",
        )
    if len(password) > _PASSWORD_MAX:
        raise ValidationError(
            f"Password must not exceed {_PASSWORD_MAX} characters.",
            field="password", code="PASSWORD_TOO_LONG",
        )
    return password


# ── File uploads ───────────────────────────────────────────────────────────


def validate_file_extension(filename: str) -> str:
    """
    Ensure the filename has an allowed extension.

    Returns the lowercase extension (e.g. ``".pdf"``).
    Raises ``InvalidFileTypeError`` on failure.
    """
    if not filename:
        raise InvalidFileTypeError(allowed=_ALLOWED_EXTENSIONS)
    ext = os.path.splitext(filename.lower())[1]
    if ext not in _ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(allowed=_ALLOWED_EXTENSIONS)
    return ext


def validate_file_size(size_bytes: int, max_mb: float = _MAX_UPLOAD_MB) -> None:
    """
    Ensure a file does not exceed the allowed size.

    Raises ``FileTooLargeError`` on failure.
    """
    max_bytes = int(max_mb * 1024 * 1024)
    if size_bytes > max_bytes:
        raise FileTooLargeError(max_mb=max_mb)


def validate_filename_safe(filename: str) -> str:
    """
    Return a filesystem-safe version of the filename.

    Strips directory components and removes characters that could
    be used for path traversal or shell injection.
    """
    # Strip directory traversal
    basename = os.path.basename(filename)
    # Remove characters outside ASCII printable range that are not safe
    safe = re.sub(r"[^\w\-_\. ]", "_", basename)
    safe = safe.strip(". ")
    if not safe:
        safe = "document"
    return safe


# ── Path traversal ─────────────────────────────────────────────────────────


def validate_path_within(path: str, base_dir: str) -> str:
    """
    Ensure ``path`` resolves within ``base_dir``.

    Returns the absolute resolved path.
    Raises ``PathTraversalError`` if the path escapes the base directory.
    """
    try:
        abs_base = os.path.realpath(os.path.abspath(base_dir))
        abs_path = os.path.realpath(os.path.abspath(path))
        if not abs_path.startswith(abs_base + os.sep) and abs_path != abs_base:
            raise PathTraversalError()
        return abs_path
    except PathTraversalError:
        raise
    except Exception:
        raise PathTraversalError()


# ── String sanitization ────────────────────────────────────────────────────


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Remove control characters and excessive whitespace.
    Truncates to ``max_length`` characters.
    Does NOT strip HTML — use a dedicated library for that if needed.
    """
    if not isinstance(value, str):
        return ""
    # Remove null bytes and other control chars (keep newlines/tabs)
    cleaned = "".join(
        ch for ch in value
        if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t", "\r")
    )
    return cleaned[:max_length].strip()


# ── Numeric ranges ─────────────────────────────────────────────────────────


def validate_int_range(value: Any, lo: int, hi: int, name: str = "value") -> int:
    """
    Ensure ``value`` is an integer within [lo, hi].

    Returns the validated integer.
    Raises ``ValidationError`` on failure.
    """
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be an integer.", field=name)
    if not (lo <= v <= hi):
        raise ValidationError(
            f"{name} must be between {lo} and {hi}.",
            field=name, code="OUT_OF_RANGE",
        )
    return v


def validate_positive_float(value: Any, name: str = "value") -> float:
    """
    Ensure ``value`` is a positive (> 0) float.
    Raises ``ValidationError`` on failure.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number.", field=name)
    if v <= 0:
        raise ValidationError(f"{name} must be greater than zero.", field=name)
    return v


# ── Print job options ──────────────────────────────────────────────────────


def validate_print_options(
    copies: int,
    color_mode: str,
    paper_size: str,
    priority: str,
    page_range: Optional[str] = None,
) -> Tuple[int, str, str, str, Optional[str]]:
    """
    Validate and normalise all print job configuration options.

    Returns ``(copies, color_mode, paper_size, priority, page_range)``.
    Raises ``ValidationError`` on any invalid option.
    """
    copies = validate_int_range(copies, 1, 100, "copies")

    color_mode = str(color_mode).strip()
    if color_mode not in ("BW", "Color"):
        raise ValidationError("Color mode must be 'BW' or 'Color'.", field="color_mode")

    paper_size = str(paper_size).strip().upper()
    if paper_size not in ("A4", "A3", "LETTER"):
        raise ValidationError("Paper size must be A4, A3, or Letter.", field="paper_size")

    priority = str(priority).strip()
    if priority not in ("Normal", "High", "Urgent", "Priority"):
        raise ValidationError("Priority must be Normal, High, or Urgent.", field="priority")

    if page_range is not None:
        page_range = str(page_range).strip()
        if page_range.lower() in ("", "all"):
            page_range = "All"
        elif not re.match(r"^\d+(-\d+)?(,\d+(-\d+)?)*$", page_range):
            raise ValidationError(
                "Page range must be in format '1-5' or '1,3,5-8'.",
                field="page_range",
            )

    return copies, color_mode, paper_size, priority, page_range


# ── Admin / ID validation ──────────────────────────────────────────────────


def validate_positive_id(value: Any, name: str = "id") -> int:
    """Return a positive integer ID. Raises ``ValidationError`` if invalid."""
    return validate_int_range(value, 1, 2_147_483_647, name)
