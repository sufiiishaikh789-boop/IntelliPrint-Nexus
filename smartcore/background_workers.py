"""
IntelliPrint Nexus — Background Workers (Enterprise Edition)
=======================================================
Centralised management for all daemon background threads.

Workers:
1. DatabaseCleanupWorker  — nightly WAL checkpoint + old log pruning
2. PrinterHeartbeatWorker — pings all printers every 60 s
3. FileCleanupWorker      — removes orphaned uploads every 6 h
4. NotificationWorker     — processes batched notification queue
5. AnalyticsWorker        — hourly analytics snapshot cache (NEW)

All workers:
- Named threads (visible in thread dumps)
- Crash-safe: exceptions are caught and logged, loop continues
- Idempotent start (calling start_all_workers() twice is safe)
- Cleanly stoppable via stop_all_workers()

Enterprise improvements:
- Replaced __import__("sqlalchemy") anti-pattern with proper module-level import
- Added AnalyticsWorker for pre-computed hourly dashboard snapshots
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("worker")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.worker")

# ── Worker registry ────────────────────────────────────────────────────────
_WORKERS: Dict[str, threading.Thread] = {}
_RUNNING: bool = False
_LOCK = threading.Lock()


# ── BaseWorker ─────────────────────────────────────────────────────────────

class _BaseWorker:
    """Abstract base for all SmartPrint background workers."""

    name: str = "BaseWorker"
    interval_s: float = 60.0

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the worker thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name=self.name,
            daemon=True,
        )
        self._thread.start()
        _log.info("%s started (interval=%.0fs)", self.name, self.interval_s)

    def stop(self) -> None:
        """Signal the worker to stop after its current iteration."""
        self._stop_event.set()
        _log.info("%s stop requested", self.name)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        """Main worker loop: run, sleep, repeat until stopped."""
        while not self._stop_event.is_set():
            try:
                self.run()
            except Exception as exc:
                _log.error("%s unhandled exception: %s", self.name, exc, exc_info=True)
            # Wait in small increments so stop_event is checked promptly
            for _ in range(int(self.interval_s)):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def run(self) -> None:
        """Override this method with worker logic."""
        raise NotImplementedError


# ── Concrete Workers ───────────────────────────────────────────────────────

class DatabaseCleanupWorker(_BaseWorker):
    """
    Nightly database maintenance:
    - WAL checkpoint to reclaim disk space
    - VACUUM on main database
    - Delete notification records older than 90 days
    """
    name = "DBCleanupWorker"
    interval_s = 86_400.0   # 24 hours

    def run(self) -> None:
        _log.info("DatabaseCleanupWorker: running maintenance cycle")
        try:
            # Proper import — no __import__() anti-pattern
            from sqlalchemy import text as sa_text
            from smartdb.models import engine
            with engine.connect() as conn:
                conn.execute(sa_text("PRAGMA wal_checkpoint(TRUNCATE)"))
                conn.execute(sa_text("VACUUM"))
                conn.commit()
            _log.info("DBCleanupWorker: WAL checkpoint + VACUUM complete")
        except Exception as exc:
            _log.error("DBCleanupWorker: DB maintenance failed: %s", exc)

        # Prune old notifications (>90 days)
        try:
            from datetime import timedelta, datetime
            from smartdb.models import Notification, SessionLocal
            cutoff = datetime.utcnow() - timedelta(days=90)
            db = SessionLocal()
            try:
                result = db.query(Notification).filter(Notification.created_at < cutoff).delete()
                db.commit()
                if result:
                    _log.info("DBCleanupWorker: pruned %d old notifications", result)
            finally:
                db.close()
        except Exception as exc:
            _log.error("DBCleanupWorker: notification pruning failed: %s", exc)


class PrinterHeartbeatWorker(_BaseWorker):
    """
    Pings all registered printers every 60 seconds and updates their
    online status in the database.
    """
    name = "PrinterHeartbeatWorker"
    interval_s = 60.0

    def run(self) -> None:
        try:
            from smartcore.printer_manager import printer_manager
            printer_manager._check_all_printers()
            _log.debug("PrinterHeartbeatWorker: heartbeat cycle complete")
        except Exception as exc:
            _log.error("PrinterHeartbeatWorker: error during heartbeat: %s", exc)


class FileCleanupWorker(_BaseWorker):
    """
    Cleans up orphaned upload files every 6 hours.
    Removes files not referenced by any active print job.
    """
    name = "FileCleanupWorker"
    interval_s = 6 * 3600.0   # 6 hours

    def run(self) -> None:
        _log.info("FileCleanupWorker: starting orphan cleanup")
        try:
            from smartcore.file_manager import cleanup_temp_files
            deleted = cleanup_temp_files()
            _log.info("FileCleanupWorker: removed %d orphan file(s)", deleted)
        except Exception as exc:
            _log.error("FileCleanupWorker: cleanup failed: %s", exc)


class NotificationWorker(_BaseWorker):
    """
    Processes batched notification delivery.
    Currently a stub — extend to add email/SMS/push delivery.
    """
    name = "NotificationWorker"
    interval_s = 30.0

    def run(self) -> None:
        # Placeholder — integrate with email/SMS service here
        pass


# ── Analytics snapshot cache ──────────────────────────────────────────────
_analytics_cache: Dict[str, Any] = {}
_analytics_cache_lock = threading.Lock()


class AnalyticsWorker(_BaseWorker):
    """
    Pre-computes hourly analytics snapshots and stores them in an in-process
    cache so dashboard queries are instantaneous instead of running heavy
    SQL aggregations on every page render.

    Access the latest snapshot via ``get_analytics_snapshot()``.
    """
    name = "AnalyticsWorker"
    interval_s = 3600.0   # 1 hour

    def run(self) -> None:
        _log.info("AnalyticsWorker: computing hourly analytics snapshot")
        try:
            from smartdb.crud import get_dashboard_stats, get_today_stats
            snapshot: Dict[str, Any] = {
                "dashboard": get_dashboard_stats(),
                "today":     get_today_stats(),
            }
            with _analytics_cache_lock:
                _analytics_cache.update(snapshot)
                _analytics_cache["computed_at"] = __import__("datetime").datetime.utcnow().isoformat()
            _log.info("AnalyticsWorker: snapshot cached successfully")
        except Exception as exc:
            _log.error("AnalyticsWorker: snapshot computation failed: %s", exc)


def get_analytics_snapshot() -> Dict[str, Any]:
    """Return the latest pre-computed analytics snapshot (non-blocking)."""
    with _analytics_cache_lock:
        return dict(_analytics_cache)


# ── Worker instances ───────────────────────────────────────────────────────

_DB_CLEANUP_WORKER        = DatabaseCleanupWorker()
_PRINTER_HEARTBEAT_WORKER = PrinterHeartbeatWorker()
_FILE_CLEANUP_WORKER      = FileCleanupWorker()
_NOTIFICATION_WORKER      = NotificationWorker()
_ANALYTICS_WORKER         = AnalyticsWorker()

_ALL_WORKERS: List[_BaseWorker] = [
    _DB_CLEANUP_WORKER,
    _PRINTER_HEARTBEAT_WORKER,
    _FILE_CLEANUP_WORKER,
    _NOTIFICATION_WORKER,
    _ANALYTICS_WORKER,
]


# ── Public API ─────────────────────────────────────────────────────────────

def start_all_workers() -> None:
    """Start all background workers (idempotent — safe to call multiple times)."""
    global _RUNNING
    with _LOCK:
        if _RUNNING:
            _log.debug("start_all_workers: already running")
            return
        _RUNNING = True

    for worker in _ALL_WORKERS:
        try:
            worker.start()
        except Exception as exc:
            _log.error("Failed to start %s: %s", worker.name, exc)

    _log.info("All background workers started (%d workers)", len(_ALL_WORKERS))


def stop_all_workers() -> None:
    """Signal all background workers to stop."""
    global _RUNNING
    _RUNNING = False
    for worker in _ALL_WORKERS:
        try:
            worker.stop()
        except Exception as exc:
            _log.error("Failed to stop %s: %s", worker.name, exc)
    _log.info("All background workers stop requested")


def get_worker_status() -> Dict[str, Any]:
    """Return the alive status of each background worker."""
    return {
        worker.name: {
            "alive":      worker.is_alive(),
            "interval_s": worker.interval_s,
        }
        for worker in _ALL_WORKERS
    }
