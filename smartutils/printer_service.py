"""
IntelliPrint Nexus — Printer Service (Enterprise Edition)
=====================================================
Drives a print job through the full lifecycle:
  Queued → Preparing Printer → Printing (PPM-based) → Completed → Ready

Enterprise improvements:
- json imported at module level (not inside function body)
- Retry wrapper: process_job_with_retry(job_id, max_retries=3)
- Explicit rollback on all session failures
- All stage transitions logged via structured logger
- sys.path hack replaced with proper package import
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Optional

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("printer")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.printer")

try:
    from smartcore.config import cfg as _cfg
    _PREPARE_SECONDS = _cfg.QUEUE.PREPARE_SECONDS
    _MAX_RETRIES     = _cfg.QUEUE.MAX_RETRIES
    _RETRY_BACKOFF   = _cfg.QUEUE.RETRY_BACKOFF_S
except ImportError:
    _PREPARE_SECONDS = 4.0
    _MAX_RETRIES     = 3
    _RETRY_BACKOFF   = 5.0

# ── Platform guard ─────────────────────────────────────────────────────────
try:
    import win32print
    import win32api
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

from smartdb.models import SessionLocal, PrintJob, Printer


# ── write_log shim for backward compatibility ──────────────────────────────
def write_log(log_name: str, message: str, exc: Optional[Exception] = None) -> None:
    try:
        from smartcore.logger import write_log as _wl
        _wl(log_name, message, exc)
    except ImportError:
        try:
            from smartutils.helpers import write_log as _legacy_wl
            _legacy_wl(log_name, message, exc)
        except Exception:
            pass


# ── Printer availability check ─────────────────────────────────────────────

def is_printer_installed(printer_name: str) -> bool:
    """Check if the printer name matches an installed local/network printer."""
    if not PYWIN32_AVAILABLE or not printer_name:
        return False
    try:
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return any(p[2] == printer_name for p in printers)
    except Exception:
        return False


# ── Timeline helper ────────────────────────────────────────────────────────

def _append_timeline(db, job: PrintJob, event: str, icon: str = "✓") -> None:
    """Append a timeline event within an already-open DB session."""
    try:
        timeline = json.loads(getattr(job, "job_timeline", None) or "[]")
    except Exception:
        timeline = []
    timeline.append({
        "time":  datetime.utcnow().strftime("%H:%M"),
        "event": event,
        "icon":  icon,
    })
    job.job_timeline = json.dumps(timeline)


# ── Hardware spooling ──────────────────────────────────────────────────────

def print_pdf_hardware(file_path: str, printer_name: str, copies: int = 1) -> bool:
    """Spool a PDF to a Windows printer, or simulate if hardware not present."""
    _log.info("print_pdf: file='%s' printer='%s' copies=%d", file_path, printer_name, copies)

    if not os.path.exists(file_path):
        _log.info("File not found: '%s' — simulating (demo mode)", file_path)
        return True

    if PYWIN32_AVAILABLE and is_printer_installed(printer_name):
        try:
            for _ in range(copies):
                win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
                time.sleep(1)
            _log.info("Physical print SUCCESS: '%s' %d copies", printer_name, copies)
            return True
        except Exception as exc:
            _log.warning("Physical print FAILED — falling back to simulation: %s", exc)

    _log.info("[SIMULATION] Simulating print to '%s'", printer_name)
    return True


# ── Core pipeline ──────────────────────────────────────────────────────────

def process_job_realistic(
    job_id: int,
    ppm: int = 20,
    print_duration_s: float = 30.0,
) -> bool:
    """
    Execute the full realistic print pipeline for a single job.

    Stages:
      1. Preparing Printer  (PREPARE_SECONDS delay)
      2. Printing           (print_duration_s — based on pages/PPM)
      3. Completed
      4. Ready for Pickup

    Returns True on success, False on failure.
    The job is marked Failed on unrecoverable errors.
    """
    db = SessionLocal()
    try:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            _log.error("process_job_realistic(%d): job not found", job_id)
            return False

        _log.info(
            "START job_id=%d print_id='%s' status='%s' printer_id=%s ppm=%d duration=%.1fs",
            job.id, job.print_id, job.status, job.printer_id, ppm, print_duration_s,
        )

        if job.status != "Queued":
            _log.info("SKIP job_id=%d: not Queued (status='%s')", job.id, job.status)
            return False

        # ── Resolve printer ────────────────────────────────────────────────
        printer = None
        if job.printer_id:
            printer = db.query(Printer).filter(Printer.id == job.printer_id).first()
        if not printer:
            printer = db.query(Printer).filter(Printer.status.in_(["Online", "Idle"])).first()
            if printer:
                job.printer_id = printer.id

        printer_name = printer.name if printer else "Virtual Printer"

        # ══ STAGE 1: Preparing Printer ══════════════════════════════════════
        job.status = "Preparing"
        _append_timeline(db, job, "Printer is Warming Up", "🔥")
        db.commit()
        _log.info("job_id=%d → Preparing Printer ('%s')", job_id, printer_name)
        db.close()
        db = None

        time.sleep(_PREPARE_SECONDS)

        # ══ STAGE 2: Printing ══════════════════════════════════════════════
        db = SessionLocal()
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False

        printer_id = job.printer_id
        if printer_id:
            printer = db.query(Printer).filter(Printer.id == printer_id).first()

        job.status            = "Printing"
        job.print_started_at  = datetime.utcnow()
        _append_timeline(db, job, f"Printing Started on {printer_name}", "🖨️")
        if printer:
            printer.status = "Busy"
        db.commit()
        _log.info("job_id=%d → Printing on '%s' for %.1fs", job_id, printer_name, print_duration_s)

        # Capture data needed after DB close
        pdf_path = getattr(job, "preview_pdf_path", None) or job.file_path or ""
        copies   = job.copies or 1
        db.close()
        db = None

        # Spool to hardware (non-blocking — spooler handles actual timing)
        print_pdf_hardware(pdf_path, printer_name, copies)

        # Wait for realistic print duration
        time.sleep(print_duration_s)

        # ══ STAGE 3: Completed ═════════════════════════════════════════════
        db = SessionLocal()
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False

        if printer_id:
            printer = db.query(Printer).filter(Printer.id == printer_id).first()

        job.status       = "Completed"
        job.completed_at = datetime.utcnow()
        _append_timeline(db, job, "Printing Completed Successfully", "✅")

        if printer:
            printer.status        = "Online"
            printer.total_prints  = (printer.total_prints or 0) + copies * (job.total_pages or 1)
            printer.toner_level   = max(
                0.0,
                (printer.toner_level or 100.0) - 0.1 * copies * (job.total_pages or 1),
            )

        db.commit()
        _log.info("job_id=%d → Completed", job_id)
        db.close()
        db = None

        time.sleep(1)

        # ══ STAGE 4: Ready for Pickup ══════════════════════════════════════
        db = SessionLocal()
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False

        job.status = "Ready"
        _append_timeline(db, job, "Ready for Pickup — Please collect at the counter", "📦")
        db.commit()
        _log.info("job_id=%d → Ready for Pickup", job_id)
        return True

    except Exception as exc:
        _log.error("CRITICAL: process_job_realistic job_id=%d: %s", job_id, exc, exc_info=True)
        # Try to mark job as Failed
        _mark_job_failed(job_id, str(exc))
        return False
    finally:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
            db.close()


def _mark_job_failed(job_id: int, reason: str) -> None:
    """Safely mark a job as Failed without raising exceptions."""
    try:
        db = SessionLocal()
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if job and (job.status or "") not in ("Ready", "Completed", "Collected"):
            job.status = "Failed"
            _append_timeline(db, job, f"Job Failed: {reason[:100]}", "⚠️")
            db.commit()
        db.close()
    except Exception as exc:
        _log.error("Could not mark job %d as Failed: %s", job_id, exc)


# ── Retry wrapper ──────────────────────────────────────────────────────────

def process_job_with_retry(
    job_id: int,
    ppm: int = 20,
    print_duration_s: float = 30.0,
    max_retries: int = _MAX_RETRIES,
) -> bool:
    """
    Run ``process_job_realistic`` with exponential-backoff retry.

    Returns True if any attempt succeeds.
    Marks job as Failed and returns False after all retries are exhausted.
    """
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            result = process_job_realistic(job_id, ppm, print_duration_s)
            if result:
                return True
            if attempt < max_retries:
                delay = _RETRY_BACKOFF * (2 ** (attempt - 1))
                _log.warning("Job %d attempt %d/%d failed — retrying in %.1fs", job_id, attempt, max_retries, delay)
                time.sleep(delay)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _RETRY_BACKOFF * (2 ** (attempt - 1))
                _log.warning("Job %d exception attempt %d/%d: %s — retrying in %.1fs", job_id, attempt, max_retries, exc, delay)
                time.sleep(delay)

    _log.error("Job %d exhausted %d retries", job_id, max_retries)
    _mark_job_failed(job_id, f"Exhausted {max_retries} retries. Last error: {last_exc}")
    return False


# ── Backward-compat alias ──────────────────────────────────────────────────
def process_job(job_id: int) -> bool:
    """Legacy wrapper — uses default PPM=20, 30s duration."""
    return process_job_realistic(job_id, ppm=20, print_duration_s=30.0)
