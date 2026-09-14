"""
IntelliPrint Nexus — GPU Job Telemetry CRUD
==========================================
Database operations for GPUJobTelemetry records.
All operations are thread-safe and never raise to the caller.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("crud_gpu")
except ImportError:
    _log = logging.getLogger("smartprint.crud_gpu")

try:
    from smartdb.models import SessionLocal, GPUJobTelemetry as _GPUModel
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    _log.warning("DB not available — GPU telemetry will not be persisted")


def create_gpu_telemetry(data: Dict[str, Any]) -> Optional[int]:
    """
    Insert a GPU job telemetry record.
    Returns the new record ID, or None on failure.
    """
    if not _DB_AVAILABLE:
        _log.debug("DB unavailable — skipping telemetry write")
        return None
    try:
        with SessionLocal() as session:
            record = _GPUModel(
                print_job_id     = data.get("print_job_id"),
                model_name       = data.get("model_name", ""),
                model_version    = data.get("model_version", "1.0.0"),
                device           = data.get("device", "cpu"),
                gpu_name         = data.get("gpu_name", "CPU"),
                precision        = data.get("precision", "FP32"),
                batch_size       = data.get("batch_size", 1),
                warmup_iters     = data.get("warmup_iters", 0),
                measured_iters   = data.get("measured_iters", 1),
                latency_ms       = data.get("latency_ms", 0.0),
                memory_before_mb = data.get("memory_before_mb", 0.0),
                memory_after_mb  = data.get("memory_after_mb", 0.0),
                peak_memory_mb   = data.get("peak_memory_mb", 0.0),
                throughput_rps   = data.get("throughput_rps", 0.0),
                status           = data.get("status", "success"),
                error_message    = data.get("error_message"),
                started_at       = _parse_dt(data.get("started_at")),
                completed_at     = _parse_dt(data.get("completed_at")),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
    except Exception as exc:
        _log.error("create_gpu_telemetry failed: %s", exc)
        return None


def get_recent_telemetry(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent GPU telemetry records, newest first."""
    if not _DB_AVAILABLE:
        return []
    try:
        with SessionLocal() as session:
            rows = (
                session.query(_GPUModel)
                .order_by(_GPUModel.id.desc())
                .limit(limit)
                .all()
            )
            return [_to_dict(r) for r in rows]
    except Exception as exc:
        _log.error("get_recent_telemetry failed: %s", exc)
        return []


def get_aggregate_stats() -> Dict[str, Any]:
    """
    Return aggregate GPU performance statistics.
    Used by the admin GPU Performance Center.
    """
    if not _DB_AVAILABLE:
        return _empty_stats()
    try:
        from sqlalchemy import func
        with SessionLocal() as session:
            q = session.query(_GPUModel)
            total   = q.count()
            success = q.filter(_GPUModel.status == "success").count()
            failed  = q.filter(_GPUModel.status.in_(["error", "oom", "timeout"])).count()
            fallback= q.filter(_GPUModel.status == "fallback").count()

            agg = session.query(
                func.avg(_GPUModel.latency_ms).label("avg_latency"),
                func.min(_GPUModel.latency_ms).label("min_latency"),
                func.max(_GPUModel.latency_ms).label("max_latency"),
                func.avg(_GPUModel.peak_memory_mb).label("avg_peak_mem"),
                func.avg(_GPUModel.throughput_rps).label("avg_throughput"),
            ).filter(_GPUModel.status == "success").first()

            # P95 approximation — sort and pick percentile
            latencies = [
                r.latency_ms for r in
                session.query(_GPUModel.latency_ms)
                .filter(_GPUModel.status == "success", _GPUModel.latency_ms > 0)
                .order_by(_GPUModel.latency_ms)
                .all()
            ]
            p95_ms = _percentile(latencies, 95)
            p99_ms = _percentile(latencies, 99)

            return {
                "total_jobs":     total,
                "success_jobs":   success,
                "failed_jobs":    failed,
                "fallback_jobs":  fallback,
                "avg_latency_ms": round(agg.avg_latency or 0, 3),
                "min_latency_ms": round(agg.min_latency or 0, 3),
                "max_latency_ms": round(agg.max_latency or 0, 3),
                "p95_latency_ms": round(p95_ms, 3),
                "p99_latency_ms": round(p99_ms, 3),
                "avg_peak_mem_mb": round(agg.avg_peak_mem or 0, 1),
                "avg_throughput_rps": round(agg.avg_throughput or 0, 2),
            }
    except Exception as exc:
        _log.error("get_aggregate_stats failed: %s", exc)
        return _empty_stats()


def _percentile(data: list, pct: float) -> float:
    if not data:
        return 0.0
    idx = int(len(data) * pct / 100)
    idx = min(idx, len(data) - 1)
    return float(sorted(data)[idx])


def _to_dict(r: Any) -> Dict[str, Any]:
    return {
        "id":              r.id,
        "print_job_id":    r.print_job_id,
        "model_name":      r.model_name,
        "model_version":   r.model_version,
        "device":          r.device,
        "gpu_name":        r.gpu_name,
        "precision":       r.precision,
        "batch_size":      r.batch_size,
        "latency_ms":      r.latency_ms,
        "peak_memory_mb":  r.peak_memory_mb,
        "throughput_rps":  r.throughput_rps,
        "status":          r.status,
        "error_message":   r.error_message,
        "started_at":      str(r.started_at) if r.started_at else None,
        "completed_at":    str(r.completed_at) if r.completed_at else None,
    }


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _empty_stats() -> Dict[str, Any]:
    return {
        "total_jobs": 0, "success_jobs": 0, "failed_jobs": 0, "fallback_jobs": 0,
        "avg_latency_ms": 0.0, "min_latency_ms": 0.0, "max_latency_ms": 0.0,
        "p95_latency_ms": 0.0, "p99_latency_ms": 0.0,
        "avg_peak_mem_mb": 0.0, "avg_throughput_rps": 0.0,
    }
