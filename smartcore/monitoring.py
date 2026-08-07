"""
IntelliPrint Nexus — Real-Time System Monitoring (Enterprise Edition)
===============================================================
Provides system health, performance metrics, AI performance,
database health, and a full aggregated monitoring dashboard.

All functions are safe to call from any thread.
Never raises — all exceptions return safe fallback values.
"""

from __future__ import annotations

import time
import threading
from collections import deque
from datetime import datetime
from typing import Any, Dict, Deque, Optional, Tuple

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("monitor")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.monitor")

try:
    from smartcore.config import cfg as _cfg
    _WINDOW_SIZE     = _cfg.MONITORING.METRICS_WINDOW_SIZE
    _SLOW_QUERY_MS   = _cfg.MONITORING.SLOW_QUERY_THRESHOLD_MS
    _HIGH_CPU        = _cfg.MONITORING.HIGH_CPU_THRESHOLD
    _HIGH_RAM        = _cfg.MONITORING.HIGH_RAM_THRESHOLD
    _QUEUE_WARNING   = _cfg.MONITORING.QUEUE_DEPTH_WARNING
except ImportError:
    _WINDOW_SIZE   = 60
    _SLOW_QUERY_MS = 200.0
    _HIGH_CPU      = 85.0
    _HIGH_RAM      = 90.0
    _QUEUE_WARNING = 20

# ── Internal rolling metrics ───────────────────────────────────────────────

_LOCK = threading.Lock()
_REQUEST_TIMES: Dict[str, Deque[float]] = {}   # endpoint → deque of duration_ms
_STARTED_AT: float = time.monotonic()


def record_request_timing(endpoint: str, duration_ms: float) -> None:
    """Record a request duration for rolling average computation."""
    with _LOCK:
        if endpoint not in _REQUEST_TIMES:
            _REQUEST_TIMES[endpoint] = deque(maxlen=_WINDOW_SIZE)
        _REQUEST_TIMES[endpoint].append(duration_ms)


def get_avg_response_time(endpoint: str) -> float:
    """Return the rolling average response time (ms) for an endpoint."""
    with _LOCK:
        times = _REQUEST_TIMES.get(endpoint)
        if not times:
            return 0.0
        return round(sum(times) / len(times), 1)


# ── System resources ───────────────────────────────────────────────────────

def get_system_health() -> Dict[str, Any]:
    """
    Return real-time system resource metrics.

    Returns a dict with cpu_percent, ram_*, disk_*, gpu_*, uptime.
    Falls back to 'N/A' for unavailable metrics.
    """
    result: Dict[str, Any] = {
        "cpu_percent":   "N/A",
        "cpu_count":     "N/A",
        "ram_used_gb":   "N/A",
        "ram_total_gb":  "N/A",
        "ram_percent":   "N/A",
        "disk_used_gb":  "N/A",
        "disk_total_gb": "N/A",
        "disk_percent":  "N/A",
        "uptime_hours":  round((time.monotonic() - _STARTED_AT) / 3600, 2),
        "timestamp":     datetime.utcnow().isoformat(),
    }

    try:
        import psutil
        result["cpu_percent"]  = round(psutil.cpu_percent(interval=0.3), 1)
        result["cpu_count"]    = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        result["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        result["ram_used_gb"]  = round(mem.used  / (1024 ** 3), 1)
        result["ram_percent"]  = mem.percent
        disk = psutil.disk_usage("/")
        result["disk_total_gb"] = round(disk.total / (1024 ** 3), 1)
        result["disk_used_gb"]  = round(disk.used  / (1024 ** 3), 1)
        result["disk_percent"]  = disk.percent
    except ImportError:
        pass
    except Exception as exc:
        _log.debug("psutil error: %s", exc)

    # GPU stats
    try:
        from smartcore.gpu_manager import gpu_manager
        gpu = gpu_manager.get_gpu_status()
        result["gpu_available"]       = gpu.get("gpu_available", False)
        result["gpu_name"]            = gpu.get("gpu_name", "N/A")
        result["gpu_memory_used_mb"]  = gpu.get("memory_used_mb", 0)
        result["gpu_memory_total_mb"] = gpu.get("memory_total_mb", 0)
        result["gpu_utilization"]     = gpu.get("utilization_percent", 0)
        result["gpu_temperature"]     = gpu.get("temperature_c", "N/A")
    except Exception:
        result["gpu_available"] = False

    # Alerts
    result["alerts"] = _compute_alerts(result)
    return result


def _compute_alerts(health: Dict[str, Any]) -> list:
    alerts = []
    if isinstance(health.get("cpu_percent"), (int, float)) and health["cpu_percent"] > _HIGH_CPU:
        alerts.append({"level": "warning", "message": f"High CPU usage: {health['cpu_percent']}%"})
    if isinstance(health.get("ram_percent"), (int, float)) and health["ram_percent"] > _HIGH_RAM:
        alerts.append({"level": "critical", "message": f"High RAM usage: {health['ram_percent']}%"})
    return alerts


# ── Database health ────────────────────────────────────────────────────────

def check_db_health() -> Dict[str, Any]:
    """
    Test database connectivity and measure query latency.
    Returns dict with connected (bool), latency_ms (float), wal_size_kb.
    """
    try:
        from smartdb.models import engine
        from sqlalchemy import text

        t0 = time.monotonic()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("PRAGMA wal_checkpoint"))
            wal_row = conn.execute(text("PRAGMA wal_autocheckpoint")).fetchone()
        latency_ms = round((time.monotonic() - t0) * 1000, 2)

        slow = latency_ms > _SLOW_QUERY_MS

        # WAL file size
        try:
            import os
            wal_path = "smartprint.db-wal"
            wal_kb   = round(os.path.getsize(wal_path) / 1024, 1) if os.path.exists(wal_path) else 0
        except Exception:
            wal_kb = 0

        return {
            "connected":    True,
            "latency_ms":   latency_ms,
            "slow_query":   slow,
            "wal_size_kb":  wal_kb,
            "status":       "warning" if slow else "healthy",
        }
    except Exception as exc:
        _log.error("DB health check failed: %s", exc)
        return {"connected": False, "latency_ms": -1, "slow_query": False, "status": "error"}


# ── Queue depth ────────────────────────────────────────────────────────────

def get_queue_health() -> Dict[str, Any]:
    """Return queue depth and processing metrics."""
    try:
        from smartdb.crud import get_db
        from smartdb.models import PrintJob
        from sqlalchemy import func

        with get_db() as db:
            rows = (
                db.query(PrintJob.status, func.count(PrintJob.id))
                .group_by(PrintJob.status)
                .all()
            )
            counts = {s: c for s, c in rows}

        queued   = counts.get("Queued",    0)
        printing = counts.get("Printing",  0)
        pending  = counts.get("Pending",   0)
        depth    = queued + printing + pending

        from smartutils.queue_manager import get_queue_metrics
        throughput = get_queue_metrics()

        return {
            "queue_depth":    depth,
            "pending":        pending,
            "queued":         queued,
            "printing":       printing,
            "status":         "warning" if depth > _QUEUE_WARNING else "healthy",
            **throughput,
        }
    except Exception as exc:
        _log.debug("Queue health check error: %s", exc)
        return {"queue_depth": 0, "status": "unknown"}


# ── AI health ──────────────────────────────────────────────────────────────

def get_ai_performance() -> Dict[str, Any]:
    """Return AI engine health and cache statistics."""
    try:
        from smartai.document_quality import check_ai_health
        return check_ai_health()
    except Exception as exc:
        _log.debug("AI health check error: %s", exc)
        return {"model_loaded": False, "status": "unknown"}


# ── Full dashboard ─────────────────────────────────────────────────────────

def get_monitoring_dashboard() -> Dict[str, Any]:
    """
    Return the full aggregated monitoring report.
    Combines system, database, queue, and AI health into one call.
    """
    return {
        "system":    get_system_health(),
        "database":  check_db_health(),
        "queue":     get_queue_health(),
        "ai":        get_ai_performance(),
        "workers":   _get_worker_status(),
        "generated_at": datetime.utcnow().isoformat(),
    }


def _get_worker_status() -> Dict[str, Any]:
    try:
        from smartcore.background_workers import get_worker_status
        return get_worker_status()
    except Exception:
        return {}


# ── Printer health summary ─────────────────────────────────────────────────

def get_printer_health_summary() -> Dict[str, Any]:
    """Return aggregated printer status counts and toner warnings."""
    try:
        from smartdb.crud import get_all_printers
        printers = get_all_printers()
        total    = len(printers)
        online   = sum(1 for p in printers if p["status"] == "Online")
        offline  = sum(1 for p in printers if p["status"] == "Offline")
        warnings = [
            p["name"] for p in printers if (p.get("toner_level") or 100) < 20
        ]
        return {
            "total":           total,
            "online":          online,
            "offline":         offline,
            "maintenance":     total - online - offline,
            "toner_warnings":  warnings,
            "status":          "warning" if offline > 0 or warnings else "healthy",
        }
    except Exception as exc:
        _log.debug("Printer health summary error: %s", exc)
        return {"total": 0, "online": 0, "offline": 0, "status": "unknown"}
