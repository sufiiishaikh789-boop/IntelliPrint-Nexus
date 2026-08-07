"""
IntelliPrint Nexus — Typed Exception Hierarchy
==========================================
Provides a structured exception hierarchy so that catch blocks can be
as specific as needed without catching unintended errors.

All SmartPrint exceptions carry:
- ``message``  — user-friendly string
- ``detail``   — developer diagnostic (may be empty)
- ``code``     — machine-readable error code (e.g. "DB_LOCKED")

Usage::

    from smartcore.exceptions import DatabaseError, ValidationError

    raise DatabaseError("Database is locked", code="DB_LOCKED")

    try:
        ...
    except SmartPrintError as exc:
        response = exc.to_dict()
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ── Base ───────────────────────────────────────────────────────────────────


class SmartPrintError(Exception):
    """Base class for all IntelliPrint Nexus application exceptions."""

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        detail: str = "",
        code: str = "UNKNOWN_ERROR",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of this error."""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }

    def user_message(self) -> str:
        """Return a safe, user-facing message (no stack traces)."""
        return self.message


# ── Database exceptions ────────────────────────────────────────────────────


class DatabaseError(SmartPrintError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "A database error occurred.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "DB_ERROR")
        super().__init__(message, **kwargs)


class DatabaseLockError(DatabaseError):
    """Raised when SQLite returns 'database is locked'."""

    def __init__(self, message: str = "Database is temporarily busy. Please retry.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "DB_LOCKED")
        super().__init__(message, **kwargs)


class RecordNotFoundError(DatabaseError):
    """Raised when a required record does not exist."""

    def __init__(self, entity: str = "Record", entity_id: Any = None, **kwargs: Any) -> None:
        id_str = f" (id={entity_id})" if entity_id is not None else ""
        kwargs.setdefault("code", "RECORD_NOT_FOUND")
        super().__init__(f"{entity}{id_str} not found.", **kwargs)


class DuplicateRecordError(DatabaseError):
    """Raised when a unique constraint would be violated."""

    def __init__(self, message: str = "A duplicate record already exists.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "DUPLICATE_RECORD")
        super().__init__(message, **kwargs)


# ── Authentication / authorisation exceptions ──────────────────────────────


class AuthError(SmartPrintError):
    """Base class for authentication failures."""

    def __init__(self, message: str = "Authentication failed.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "AUTH_ERROR")
        super().__init__(message, **kwargs)


class InvalidCredentialsError(AuthError):
    """Raised when username or password is incorrect."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("code", "INVALID_CREDENTIALS")
        super().__init__("Invalid username or password.", **kwargs)


class AccountSuspendedError(AuthError):
    """Raised when a suspended account attempts to log in."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("code", "ACCOUNT_SUSPENDED")
        super().__init__("Your account has been suspended. Contact support.", **kwargs)


class PermissionDeniedError(AuthError):
    """Raised when an authenticated user lacks required permissions."""

    def __init__(self, action: str = "perform this action", **kwargs: Any) -> None:
        kwargs.setdefault("code", "PERMISSION_DENIED")
        super().__init__(f"You do not have permission to {action}.", **kwargs)


# ── Validation exceptions ──────────────────────────────────────────────────


class ValidationError(SmartPrintError):
    """Raised when user input fails validation rules."""

    def __init__(self, message: str = "Input validation failed.", *, field: str = "", **kwargs: Any) -> None:
        kwargs.setdefault("code", "VALIDATION_ERROR")
        self.field = field
        super().__init__(message, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        if self.field:
            d["field"] = self.field
        return d


class FileTooLargeError(ValidationError):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, max_mb: float = 50.0, **kwargs: Any) -> None:
        kwargs.setdefault("code", "FILE_TOO_LARGE")
        super().__init__(f"File exceeds maximum allowed size of {max_mb} MB.", field="file", **kwargs)


class InvalidFileTypeError(ValidationError):
    """Raised when an uploaded file has a disallowed extension or MIME type."""

    def __init__(self, allowed: tuple = (), **kwargs: Any) -> None:
        kwargs.setdefault("code", "INVALID_FILE_TYPE")
        allowed_str = ", ".join(allowed) if allowed else "PDF, PNG, JPG"
        super().__init__(f"File type not allowed. Accepted: {allowed_str}.", field="file", **kwargs)


# ── Printer exceptions ─────────────────────────────────────────────────────


class PrinterError(SmartPrintError):
    """Base class for printer-related failures."""

    def __init__(self, message: str = "A printer error occurred.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "PRINTER_ERROR")
        super().__init__(message, **kwargs)


class PrinterOfflineError(PrinterError):
    """Raised when the target printer is offline or unreachable."""

    def __init__(self, printer_name: str = "Printer", **kwargs: Any) -> None:
        kwargs.setdefault("code", "PRINTER_OFFLINE")
        super().__init__(f"{printer_name} is currently offline.", **kwargs)


class NoPrinterAvailableError(PrinterError):
    """Raised when no suitable printer is online."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("code", "NO_PRINTER_AVAILABLE")
        super().__init__("No printers are currently available. Please try again later.", **kwargs)


# ── Queue exceptions ───────────────────────────────────────────────────────


class QueueError(SmartPrintError):
    """Base class for queue engine failures."""

    def __init__(self, message: str = "A queue error occurred.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "QUEUE_ERROR")
        super().__init__(message, **kwargs)


class JobNotCancellableError(QueueError):
    """Raised when attempting to cancel a job that cannot be cancelled."""

    def __init__(self, status: str = "", **kwargs: Any) -> None:
        kwargs.setdefault("code", "JOB_NOT_CANCELLABLE")
        status_str = f" (current status: {status})" if status else ""
        super().__init__(
            f"This job cannot be cancelled{status_str}. "
            "Cancellation is only allowed before printing starts.",
            **kwargs,
        )


class MaxRetriesExceededError(QueueError):
    """Raised when a job has been retried too many times."""

    def __init__(self, job_id: Any = None, **kwargs: Any) -> None:
        kwargs.setdefault("code", "MAX_RETRIES_EXCEEDED")
        job_str = f" Job {job_id}" if job_id else ""
        super().__init__(f"{job_str} failed after maximum retries.", **kwargs)


# ── AI exceptions ──────────────────────────────────────────────────────────


class AIError(SmartPrintError):
    """Base class for AI / ML engine failures."""

    def __init__(self, message: str = "AI processing error.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "AI_ERROR")
        super().__init__(message, **kwargs)


class ModelNotLoadedError(AIError):
    """Raised when an AI model cannot be loaded."""

    def __init__(self, model_name: str = "Model", **kwargs: Any) -> None:
        kwargs.setdefault("code", "MODEL_NOT_LOADED")
        super().__init__(f"{model_name} could not be loaded. Using fallback heuristics.", **kwargs)


class InferenceTimeoutError(AIError):
    """Raised when an AI inference call exceeds the configured timeout."""

    def __init__(self, timeout_s: float = 15.0, **kwargs: Any) -> None:
        kwargs.setdefault("code", "INFERENCE_TIMEOUT")
        super().__init__(f"AI inference timed out after {timeout_s:.0f}s.", **kwargs)


# ── Payment exceptions ─────────────────────────────────────────────────────


class PaymentError(SmartPrintError):
    """Base class for payment engine failures."""

    def __init__(self, message: str = "A payment error occurred.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "PAYMENT_ERROR")
        super().__init__(message, **kwargs)


class PaymentAmountMismatchError(PaymentError):
    """Raised when the charged amount doesn't match the expected cost."""

    def __init__(self, expected: float, received: float, **kwargs: Any) -> None:
        kwargs.setdefault("code", "AMOUNT_MISMATCH")
        super().__init__(
            f"Payment amount mismatch: expected ₹{expected:.2f}, received ₹{received:.2f}.",
            **kwargs,
        )


class DuplicatePaymentError(PaymentError):
    """Raised when a payment for a job already exists."""

    def __init__(self, job_id: Any = None, **kwargs: Any) -> None:
        kwargs.setdefault("code", "DUPLICATE_PAYMENT")
        job_str = f" for job {job_id}" if job_id else ""
        super().__init__(f"A payment{job_str} already exists.", **kwargs)


# ── File exceptions ────────────────────────────────────────────────────────


class FileError(SmartPrintError):
    """Base class for file system failures."""

    def __init__(self, message: str = "A file system error occurred.", **kwargs: Any) -> None:
        kwargs.setdefault("code", "FILE_ERROR")
        super().__init__(message, **kwargs)


class PathTraversalError(FileError):
    """Raised when a file path would escape the uploads directory."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("code", "PATH_TRAVERSAL")
        super().__init__("Invalid file path detected.", **kwargs)


# ── Utility helpers ────────────────────────────────────────────────────────


def error_response(exc: Exception) -> Dict[str, Any]:
    """
    Convert any exception into a user-safe response dict.

    SmartPrintError subclasses return their structured ``to_dict()``.
    All other exceptions return a generic safe message.
    """
    if isinstance(exc, SmartPrintError):
        return exc.to_dict()
    return {
        "error": True,
        "code": "INTERNAL_ERROR",
        "message": "An internal error occurred. Please try again.",
        "detail": "",
    }
