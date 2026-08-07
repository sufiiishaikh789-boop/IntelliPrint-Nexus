"""
IntelliPrint Nexus — Enterprise Logging Service
==========================================
Provides a centralized, rotating, structured logging system.
All modules should obtain their logger via ``get_logger(name)``.

Features:
- Per-module rotating file handlers (10 MB × 5 backups)
- Single unified log for aggregated viewing
- Thread-safe (Python's logging is GIL-protected)
- UTF-8 aware (handles emoji, ₹, etc.)
- Never raises — logging must never crash the app
- Optional context injection (user_id, job_id)

Usage::

    from smartcore.logger import get_logger
    log = get_logger("queue")
    log.info("Job %s dispatched to printer", job_id)
    log.exception("Failed to process job", exc_info=True)
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
from typing import Optional


# ── Bootstrap config (avoid circular imports) ─────────────────────────────
_LOG_DIR = "logs"
_MAX_BYTES = 10 * 1024 * 1024   # 10 MB
_BACKUP_COUNT = 5
_LEVEL = logging.INFO
_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)-12s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Per-module log files ───────────────────────────────────────────────────
_MODULE_LOGS: dict[str, str] = {
    "app":      "logs/app.log",
    "db":       "logs/database.log",
    "queue":    "logs/queue.log",
    "printer":  "logs/printer.log",
    "payment":  "logs/payment.log",
    "security": "logs/security.log",
    "ai":       "logs/ai.log",
    "upload":   "logs/upload.log",
    "monitor":  "logs/monitor.log",
    "worker":   "logs/workers.log",
}
_UNIFIED_LOG = "logs/smartprint.log"

# ── Internal state ─────────────────────────────────────────────────────────
_lock = threading.Lock()
_initialized: bool = False
_loggers: dict[str, logging.Logger] = {}


def _safe_makedirs(path: str) -> None:
    """Create directory silently."""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def _make_rotating_handler(path: str) -> Optional[logging.Handler]:
    """Create a UTF-8-safe rotating file handler, or None on failure."""
    try:
        _safe_makedirs(os.path.dirname(path))
        handler = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
        return handler
    except Exception:
        return None


def _make_console_handler() -> logging.Handler:
    """Create a console handler that never raises UnicodeEncodeError."""
    class _SafeStreamHandler(logging.StreamHandler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                msg = self.format(record)
                stream = self.stream
                if hasattr(stream, "buffer"):
                    stream.buffer.write((msg + self.terminator).encode("utf-8", errors="replace"))
                    stream.buffer.flush()
                else:
                    safe = msg.encode(
                        getattr(stream, "encoding", "utf-8") or "utf-8",
                        errors="replace",
                    ).decode(getattr(stream, "encoding", "utf-8") or "utf-8", errors="replace")
                    stream.write(safe + self.terminator)
                    stream.flush()
            except Exception:
                pass

    handler = _SafeStreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
    return handler


def _initialize() -> None:
    """Initialize the logging system (idempotent, thread-safe)."""
    global _initialized
    with _lock:
        if _initialized:
            return

        _safe_makedirs(_LOG_DIR)

        # Unified log handler — attached to the root "smartprint" logger
        root_logger = logging.getLogger("smartprint")
        root_logger.setLevel(_LEVEL)
        root_logger.propagate = False

        unified_handler = _make_rotating_handler(_UNIFIED_LOG)
        if unified_handler:
            root_logger.addHandler(unified_handler)

        console = _make_console_handler()
        root_logger.addHandler(console)

        # Per-module loggers
        for name, path in _MODULE_LOGS.items():
            logger = logging.getLogger(f"smartprint.{name}")
            logger.setLevel(_LEVEL)
            logger.propagate = True          # also goes to root (unified log)
            handler = _make_rotating_handler(path)
            if handler:
                logger.addHandler(handler)
            _loggers[name] = logger

        _initialized = True


def get_logger(name: str = "app") -> logging.Logger:
    """
    Return a named logger for the given module.

    Parameters
    ----------
    name : str
        One of: ``app``, ``db``, ``queue``, ``printer``, ``payment``,
        ``security``, ``ai``, ``upload``, ``monitor``, ``worker``.
        Unknown names fall back to the unified root logger.

    Returns
    -------
    logging.Logger
    """
    _initialize()
    key = name.lower().strip()
    if key in _loggers:
        return _loggers[key]
    # Unknown module — child of root so it flows to unified log
    logger = logging.getLogger(f"smartprint.{key}")
    logger.setLevel(_LEVEL)
    logger.propagate = True
    _loggers[key] = logger
    return logger


# ── Backward-compatible write_log shim ───────────────────────────────────
def write_log(log_name: str, message: str, exception: Optional[Exception] = None) -> None:
    """
    Drop-in replacement for the legacy ``write_log`` utility.

    Translates old-style calls into the new structured logger so that
    existing callers (queue_manager, printer_service, etc.) continue to
    work without modification while gaining rotation and structure.
    """
    try:
        _initialize()
        # Map legacy log names → module logger names
        _name_map = {
            "QUEUE_LOG":    "queue",
            "PRINTER_LOG":  "printer",
            "JOB_LOG":      "queue",
            "PAYMENT_LOG":  "payment",
            "AI_LOG":       "ai",
            "SECURITY_LOG": "security",
            "UPLOAD_LOG":   "upload",
        }
        module = _name_map.get(log_name.upper(), "app")
        logger = get_logger(module)

        if exception:
            logger.error("%s", message, exc_info=exception)
        else:
            logger.info("%s", message)
    except Exception:
        # Logging must NEVER raise
        pass


# Auto-initialize when imported
_initialize()
