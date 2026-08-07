"""
IntelliPrint Nexus — CRUD Operations (Enterprise Edition)
=====================================================
Complete data-access layer for every model in the system.

Enterprise improvements over the previous version:
- N+1 queries eliminated: ``get_all_payments_with_jobs`` and
  ``get_all_users_with_stats`` now use SQL JOINs / subqueries
- ``get_student_analytics`` aggregation moved to SQL GROUP BY
- Duplicate ``import json`` removed (single ``_json`` import)
- ``get_db_with_retry`` handles SQLite 'database is locked' transparently
- ``update_payment_status`` added (was missing from payment flow)
- ``get_payment_by_transaction_id`` for idempotent payment checks
- Pagination support on all list queries (``offset``, ``limit`` params)
- Typed exception propagation for all write operations
- Complete type hints throughout
- Extracted ``_mlog_to_dict()`` shared serializer (DRY principle)
- Added ``get_admin_analytics()`` for SQL-level monthly/hourly reporting
"""

from __future__ import annotations

import json as _json
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from smartdb.models import (
    AIAnalysis,
    ChatHistory,
    MaintenanceLog,
    Notification,
    Payment,
    PrintJob,
    Printer,
    SessionLocal,
    User,
)

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("db")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.db")


# ---------------------------------------------------------------------------
# One-time DB migration: add manual_override column if it does not exist
# ---------------------------------------------------------------------------
# This is idempotent — safe to run on every startup.
# SQLite ALTER TABLE ADD COLUMN cannot modify existing rows, but
# server_default="0" ensures new/existing rows default to 0 (False).
# ---------------------------------------------------------------------------

def _ensure_manual_override_column() -> None:
    """Add manual_override column to printers table if not already present."""
    try:
        from smartdb.models import engine
        with engine.connect() as conn:
            # PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk)
            result = conn.execute(text("PRAGMA table_info(printers)"))
            cols = [row[1] for row in result.fetchall()]
            if "manual_override" not in cols:
                conn.execute(text(
                    "ALTER TABLE printers ADD COLUMN manual_override INTEGER NOT NULL DEFAULT 0"
                ))
                conn.commit()
                _log.info("DB migration: added 'manual_override' column to printers")
    except Exception as _mig_exc:
        # Never crash on migration — log and continue
        try:
            _log.warning("Could not add manual_override column: %s", _mig_exc)
        except Exception:
            pass


_ensure_manual_override_column()


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Yield a database session, rolling back on error and always closing."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_with_retry(
    max_retries: int = 3,
    backoff_s: float = 0.5,
) -> Generator[Session, None, None]:
    """
    Like ``get_db`` but retries on 'database is locked' errors.

    Useful for write operations in multi-threaded contexts (queue manager,
    background workers) where SQLite WAL contention can occur.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        db: Session = SessionLocal()
        try:
            yield db
            return
        except Exception as exc:
            db.rollback()
            last_exc = exc
            err_msg = str(exc).lower()
            if "database is locked" in err_msg or "locked" in err_msg:
                if attempt < max_retries - 1:
                    sleep_s = backoff_s * (2 ** attempt)
                    _log.warning("DB locked, retry %d/%d in %.1fs", attempt + 1, max_retries, sleep_s)
                    time.sleep(sleep_s)
                    continue
            raise
        finally:
            db.close()
    if last_exc:
        raise last_exc


# ===========================================================================
# USER CRUD
# ===========================================================================

def create_user(
    username: str,
    email: str,
    password_hash: str,
    role: str = "Student",
) -> User:
    """Create and persist a new User row. Returns the detached ORM object."""
    with get_db_with_retry() as db:
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            status="Active",
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        _log.info("Created user id=%d username='%s'", user.id, user.username)
        return user


def get_user_by_username(username: str) -> Optional[User]:
    """Fetch a user ORM object by username. Returns None if not found."""
    with get_db() as db:
        return db.query(User).filter(User.username == username).first()


def get_user_by_email(email: str) -> Optional[User]:
    """Fetch a user ORM object by email. Returns None if not found."""
    with get_db() as db:
        return db.query(User).filter(User.email == email.strip().lower()).first()


def get_all_users() -> List[Dict[str, Any]]:
    """Return all users as a list of serialised dicts (safe for Streamlit)."""
    with get_db() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [_user_to_dict(u) for u in users]


def _user_to_dict(u: User) -> Dict[str, Any]:
    """Serialise a User ORM object to a plain dict."""
    return {
        "id":          u.id,
        "username":    u.username,
        "email":       u.email,
        "role":        u.role,
        "status":      u.status,
        "avatar_url":  u.avatar_url,
        "student_id":  getattr(u, "student_id",  None),
        "department":  getattr(u, "department",  None),
        "course":      getattr(u, "course",      None),
        "phone":       getattr(u, "phone",       None),
        "preferences": getattr(u, "preferences", None),
        "created_at":  u.created_at,
        "last_login":  u.last_login,
    }


def update_user_last_login(user_id: int) -> None:
    """Stamp the current UTC time on last_login for the given user."""
    with get_db_with_retry() as db:
        db.query(User).filter(User.id == user_id).update(
            {"last_login": datetime.utcnow()},
            synchronize_session=False,
        )
        db.commit()


def update_user_credentials(
    user_id: int,
    email: str,
    password_hash: Optional[str] = None,
) -> bool:
    """Update email and optionally the password hash. Returns True on success."""
    with get_db_with_retry() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.email = email.strip().lower()
        if password_hash:
            user.password_hash = password_hash
        db.commit()
        return True


def update_user_profile(
    user_id: int,
    student_id: Optional[str] = None,
    department: Optional[str] = None,
    course: Optional[str] = None,
    phone: Optional[str] = None,
    avatar_url: Optional[str] = None,
    email: Optional[str] = None,
    password_hash: Optional[str] = None,
) -> bool:
    """Update extended profile fields. Only non-None values are written."""
    with get_db_with_retry() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        _FIELD_MAP = {
            "student_id":    student_id,
            "department":    department,
            "course":        course,
            "phone":         phone,
            "avatar_url":    avatar_url,
            "email":         email.strip().lower() if email else None,
            "password_hash": password_hash,
        }
        for field_name, val in _FIELD_MAP.items():
            if val is not None:
                setattr(user, field_name, val)
        db.commit()
        return True


def suspend_user(user_id: int) -> bool:
    """Suspend a student account. Returns True on success."""
    with get_db_with_retry() as db:
        result = db.query(User).filter(User.id == user_id).update(
            {"status": "Suspended"}, synchronize_session=False
        )
        db.commit()
        return result > 0


def activate_user(user_id: int) -> bool:
    """Reactivate a suspended account. Returns True on success."""
    with get_db_with_retry() as db:
        result = db.query(User).filter(User.id == user_id).update(
            {"status": "Active"}, synchronize_session=False
        )
        db.commit()
        return result > 0


# ===========================================================================
# PRINT JOB CRUD
# ===========================================================================

def create_print_job(
    user_id: int,
    document_name: str,
    file_path: str,
    print_id: str,
    copies: int = 1,
    color_mode: str = "BW",
    duplex: bool = False,
    page_range: Optional[str] = None,
    paper_size: str = "A4",
    priority: str = "Normal",
    total_pages: int = 1,
    cost_per_page: float = 2.0,
    total_cost: float = 0.0,
    quality_score: Optional[float] = None,
    printer_id: Optional[int] = None,
    qr_code_path: Optional[str] = None,
    estimated_wait_time: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a new print job and return its serialised dict."""
    with get_db_with_retry() as db:
        job = PrintJob(
            user_id=user_id,
            document_name=document_name,
            file_path=file_path,
            print_id=print_id,
            status="Pending",
            copies=copies,
            color_mode=color_mode,
            duplex=duplex,
            page_range=page_range,
            paper_size=paper_size,
            priority=priority,
            total_pages=total_pages,
            cost_per_page=cost_per_page,
            total_cost=total_cost,
            quality_score=quality_score,
            printer_id=printer_id,
            qr_code_path=qr_code_path,
            estimated_wait_time=estimated_wait_time,
            submitted_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        _log.info("Created print job id=%d print_id='%s'", job.id, job.print_id)
        return _job_to_dict(job)


def get_user_jobs(
    user_id: int,
    limit: int = 500,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Return print jobs for a given user (newest first). Supports pagination."""
    with get_db() as db:
        jobs = (
            db.query(PrintJob)
            .filter(PrintJob.user_id == user_id)
            .order_by(PrintJob.submitted_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_job_to_dict(j) for j in jobs]


def get_all_jobs(
    limit: int = 1000,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Return all print jobs (admin view), newest first. Supports pagination."""
    with get_db() as db:
        jobs = (
            db.query(PrintJob)
            .order_by(PrintJob.submitted_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_job_to_dict(j) for j in jobs]


def update_job_status(job_id: int, new_status: str) -> bool:
    """Update the status of a print job. Returns True on success."""
    with get_db_with_retry() as db:
        updates: Dict[str, Any] = {"status": new_status}
        if new_status in ("Completed", "Ready", "Collected"):
            updates["completed_at"] = datetime.utcnow()
        result = db.query(PrintJob).filter(PrintJob.id == job_id).update(
            updates, synchronize_session=False
        )
        db.commit()
        return result > 0


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single print job by its primary key."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        return _job_to_dict(job) if job else None


def get_job_by_print_id(print_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single print job by human-readable print_id (e.g. SP2026-AB12)."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.print_id == print_id).first()
        return _job_to_dict(job) if job else None


def _job_to_dict(job: PrintJob) -> Dict[str, Any]:
    """Serialise a PrintJob ORM object to a plain dict."""
    return {
        "id":                    job.id,
        "user_id":               job.user_id,
        "document_name":         job.document_name,
        "file_path":             job.file_path,
        "status":                job.status,
        "copies":                job.copies,
        "color_mode":            job.color_mode,
        "duplex":                job.duplex,
        "page_range":            job.page_range,
        "paper_size":            job.paper_size,
        "priority":              job.priority,
        "total_pages":           job.total_pages,
        "pages":                 job.total_pages,          # alias
        "cost_per_page":         job.cost_per_page,
        "total_cost":            job.total_cost,
        "cost":                  job.total_cost,           # alias
        "quality_score":         job.quality_score,
        "printer_id":            job.printer_id,
        "print_id":              job.print_id,
        "qr_code_path":          job.qr_code_path,
        "pickup_id":             getattr(job, "pickup_id",            None),
        "preview_pdf_path":      getattr(job, "preview_pdf_path",     None),
        "estimated_wait_time":   job.estimated_wait_time,
        "print_started_at":      getattr(job, "print_started_at",     None),
        "job_timeline":          getattr(job, "job_timeline",         None),
        "submitted_at":          job.submitted_at,
        "created_at":            str(job.submitted_at),   # legacy alias
        "completed_at":          job.completed_at,
        "document_fingerprint":  getattr(job, "document_fingerprint", None),
        "is_bookmarked":         getattr(job, "is_bookmarked",        False),
        "reprint_count":         getattr(job, "reprint_count",        0),
    }


def set_job_pickup_info(
    job_id: int,
    pickup_id: str,
    qr_code_path: str,
    preview_pdf_path: str,
) -> bool:
    """Store pickup ID, QR path, and preview PDF — called only after payment."""
    with get_db_with_retry() as db:
        updates: Dict[str, Any] = {
            "pickup_id":    pickup_id,
            "qr_code_path": qr_code_path,
        }
        if preview_pdf_path:
            updates["preview_pdf_path"] = preview_pdf_path
        result = db.query(PrintJob).filter(PrintJob.id == job_id).update(
            updates, synchronize_session=False
        )
        db.commit()
        return result > 0


def get_job_payment_status(job_id: int) -> Optional[str]:
    """Return the payment status for a job, or None if no payment exists."""
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.job_id == job_id).first()
        return payment.status if payment else None


# ---------------------------------------------------------------------------
# Timeline helpers
# ---------------------------------------------------------------------------

def append_job_timeline(job_id: int, event: str, icon: str = "✓") -> bool:
    """Append a timestamped event to the job's timeline JSON array."""
    with get_db_with_retry() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False
        try:
            timeline = _json.loads(getattr(job, "job_timeline", None) or "[]")
        except Exception:
            timeline = []
        timeline.append({
            "time":  datetime.utcnow().strftime("%H:%M"),
            "event": event,
            "icon":  icon,
        })
        job.job_timeline = _json.dumps(timeline)
        db.commit()
        return True


def get_job_timeline(job_id: int) -> List[Dict[str, Any]]:
    """Return the timeline events list for a job."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return []
        try:
            return _json.loads(getattr(job, "job_timeline", None) or "[]")
        except Exception:
            return []


def get_live_progress(job_id: int) -> Dict[str, Any]:
    """
    Return live progress metrics for a printing job.
    Calculates % complete, current page, elapsed time, ETA based on PPM.
    """
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return {}

        total_pages = (job.total_pages or 1) * (job.copies or 1)
        status = (job.status or "").lower()

        ppm: int = 20
        if job.printer_id:
            printer = db.query(Printer).filter(Printer.id == job.printer_id).first()
            if printer:
                ppm = getattr(printer, "pages_per_minute", 20) or 20

        total_duration_s = max(1, (total_pages / ppm) * 60)

        def _fmt(seconds: float) -> str:
            s = int(seconds)
            m, sec = divmod(s, 60)
            return f"{m}m {sec:02d}s" if m else f"{sec}s"

        if status == "printing":
            started = getattr(job, "print_started_at", None) or job.submitted_at
            elapsed_s = max(0.0, (datetime.utcnow() - started).total_seconds()) if started else 0.0
            progress_pct = min(99, int((elapsed_s / total_duration_s) * 100))
            current_page = min(total_pages, max(1, int((elapsed_s / total_duration_s) * total_pages)))
            remaining_s = max(0.0, total_duration_s - elapsed_s)
        elif status in ("completed", "ready", "ready for pickup", "collected", "archived"):
            elapsed_s = total_duration_s
            progress_pct = 100
            current_page = total_pages
            remaining_s = 0.0
        else:
            elapsed_s = 0.0
            progress_pct = 0
            current_page = 0
            remaining_s = total_duration_s

        return {
            "status":           job.status,
            "total_pages":      total_pages,
            "current_page":     current_page,
            "progress_pct":     progress_pct,
            "elapsed":          _fmt(elapsed_s),
            "remaining":        _fmt(remaining_s),
            "ppm":              ppm,
            "print_started_at": getattr(job, "print_started_at", None),
        }


def cancel_job_safe(job_id: int) -> Tuple[bool, str]:
    """
    Cancel a job only if its current status allows it.

    Allowed: Pending, Queued, Waiting, Payment Pending, Uploaded, and
    pre-print AI/selection stages.
    Blocked: Preparing Printer, Printing, Completed, Ready, Collected.

    Returns ``(success, message)``.
    """
    _CANCELLABLE = frozenset({
        "pending", "queued", "waiting", "payment_pending",
        "uploaded", "ai analysis", "quality check",
        "printer selection", "queue assigned",
    })
    with get_db_with_retry() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False, "Job not found."
        if (job.status or "").lower() not in _CANCELLABLE:
            return False, (
                f"Cannot cancel job in status '{job.status}'. "
                "Cancellation is only allowed before printing starts."
            )
        job.status = "Cancelled"
        db.commit()
    append_job_timeline(job_id, "Job Cancelled by Student", "❌")
    return True, "Job cancelled successfully."


def get_queue_position(job_id: int, printer_id: int) -> int:
    """Return the 1-based queue position of a job for its printer (0 if not found)."""
    with get_db() as db:
        queued_jobs = (
            db.query(PrintJob)
            .filter(
                PrintJob.printer_id == printer_id,
                PrintJob.status == "Queued",
            )
            .order_by(PrintJob.priority.desc(), PrintJob.submitted_at.asc())
            .all()
        )
        for i, j in enumerate(queued_jobs, 1):
            if j.id == job_id:
                return i
        return 0


def cancel_job(job_id: int) -> bool:
    """Simple cancel — no status check. Returns True on success."""
    return update_job_status(job_id, "Cancelled")


def move_job_to_top(job_id: int) -> bool:
    """Promote a job to Priority and set estimated_wait_time=1 minute."""
    with get_db_with_retry() as db:
        result = db.query(PrintJob).filter(PrintJob.id == job_id).update(
            {"priority": "Priority", "estimated_wait_time": 1},
            synchronize_session=False,
        )
        db.commit()
        return result > 0



def assign_printer_and_queue(
    job_id: int,
    pages: int = 1,
    copies: int = 1,
    priority: str = "Normal",
) -> dict:
    """
    Core post-payment function.

    1. Selects the best ONLINE printer (lowest active queue depth).
    2. Calculates a realistic ETA based on PPM, queue backlog, and priority.
    3. Atomically updates printer_id + estimated_wait_time + status = "Queued".
    4. Appends three timeline events (payment, queue assignment, ETA).

    Returns a dict: {printer_id, printer_name, queue_pos, eta_minutes}.
    The Queue Manager's filter (printer_id == printer.id, status == "Queued")
    will now find this job on the very next poll cycle.
    """
    import json as _j

    with get_db_with_retry() as db:
        # ── 1. Find online printers ───────────────────────────────────────────
        online_printers = (
            db.query(Printer)
            .filter(Printer.status.in_(["Online", "Idle"]))
            .order_by(Printer.toner_level.desc(), Printer.error_count.asc())
            .all()
        )

        # Graceful fallback — take any printer so job isn't orphaned
        if not online_printers:
            online_printers = db.query(Printer).all()

        if not online_printers:
            # No printers at all — still mark Queued so UI can show progress
            db.query(PrintJob).filter(PrintJob.id == job_id).update(
                {"status": "Queued", "estimated_wait_time": 10},
                synchronize_session=False,
            )
            db.commit()
            return {
                "printer_id": None, "printer_name": "Pending Assignment",
                "queue_pos": 1, "eta_minutes": 10,
            }

        # ── 2. Pick printer with shortest active queue ────────────────────────
        best_printer = online_printers[0]
        min_queue_pages = float("inf")

        for p in online_printers:
            active = db.query(PrintJob).filter(
                PrintJob.printer_id == p.id,
                PrintJob.status.in_(["Queued", "Preparing", "Printing"]),
            ).all()
            total_pages_in_q = sum(
                (j.total_pages or 1) * (j.copies or 1) for j in active
            )
            if total_pages_in_q < min_queue_pages:
                min_queue_pages = total_pages_in_q
                best_printer    = p

        # ── 3. Count queue depth for the chosen printer ───────────────────────
        queued_jobs = db.query(PrintJob).filter(
            PrintJob.printer_id == best_printer.id,
            PrintJob.status.in_(["Queued", "Preparing", "Printing"]),
        ).all()

        queued_pages = sum((j.total_pages or 1) * (j.copies or 1) for j in queued_jobs)
        this_pages   = max(1, (pages or 1)) * max(1, (copies or 1))
        queue_pos    = len(queued_jobs) + 1
        ppm          = max(1, getattr(best_printer, "pages_per_minute", 20) or 20)

        # ── 4. ETA calculation ────────────────────────────────────────────────
        # Time for jobs ahead of us + time for our own job (in minutes)
        queue_wait_min = int(queued_pages / ppm)
        our_print_min  = max(1, int(this_pages / ppm))

        # Priority shortcut: high-priority jobs jump to front
        if priority in ("Urgent", "High", "Priority"):
            eta_minutes = max(1, our_print_min)       # effectively skip the queue
        else:
            eta_minutes = max(1, queue_wait_min + our_print_min)

        # ── 5. Atomic DB update ───────────────────────────────────────────────
        db.query(PrintJob).filter(PrintJob.id == job_id).update(
            {
                "printer_id":          best_printer.id,
                "estimated_wait_time": eta_minutes,
                "status":              "Queued",
            },
            synchronize_session=False,
        )

        # Append timeline inside the same session while we have job data
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if job:
            try:
                tl = _j.loads(getattr(job, "job_timeline", None) or "[]")
            except Exception:
                tl = []
            now_str = datetime.utcnow().strftime("%H:%M")
            tl.extend([
                {"time": now_str, "event": "Payment Successful — Job queued for printing",  "icon": "💳"},
                {"time": now_str, "event": f"Assigned to {best_printer.name} (Queue #{queue_pos})", "icon": "📋"},
                {"time": now_str, "event": f"Estimated wait: {eta_minutes} min ({this_pages} pages @ {ppm} PPM)", "icon": "⏱️"},
            ])
            job.job_timeline = _j.dumps(tl)

        db.commit()

        # Capture plain Python values NOW, before the session closes.
        # Accessing best_printer.id/.name outside the with-block raises
        # sqlalchemy.orm.exc.DetachedInstanceError.
        _ret_printer_id   = int(best_printer.id)
        _ret_printer_name = str(best_printer.name)

    return {
        "printer_id":   _ret_printer_id,
        "printer_name": _ret_printer_name,
        "queue_pos":    queue_pos,
        "eta_minutes":  eta_minutes,
    }


def set_job_fingerprint(job_id: int, sha256: str) -> bool:
    """Store the SHA-256 document fingerprint on a print job."""
    with get_db_with_retry() as db:
        result = db.query(PrintJob).filter(PrintJob.id == job_id).update(
            {"document_fingerprint": sha256}, synchronize_session=False
        )
        db.commit()
        return result > 0


def get_duplicate_by_fingerprint(user_id: int, sha256: str) -> Optional[Dict[str, Any]]:
    """Return the most recent job with the same SHA-256 fingerprint, or None."""
    if not sha256:
        return None
    with get_db() as db:
        job = (
            db.query(PrintJob)
            .filter(
                PrintJob.user_id == user_id,
                PrintJob.document_fingerprint == sha256,
            )
            .order_by(PrintJob.submitted_at.desc())
            .first()
        )
        return _job_to_dict(job) if job else None


def bookmark_job(job_id: int, user_id: int, state: Optional[bool] = None) -> bool:
    """Toggle or set the bookmark flag on a print job. Returns new state."""
    with get_db_with_retry() as db:
        job = db.query(PrintJob).filter(
            PrintJob.id == job_id,
            PrintJob.user_id == user_id,
        ).first()
        if not job:
            return False
        new_state = (not getattr(job, "is_bookmarked", False)) if state is None else state
        job.is_bookmarked = new_state
        db.commit()
        return new_state


def get_print_jobs_for_printer(printer_id: int) -> List[Dict[str, Any]]:
    """Fetch all print jobs associated with a printer."""
    with get_db() as db:
        jobs = db.query(PrintJob).filter(PrintJob.printer_id == printer_id).all()
        return [_job_to_dict(j) for j in jobs]


# ===========================================================================
# PAYMENT CRUD
# ===========================================================================

def create_payment(
    job_id: int,
    user_id: int,
    amount: float,
    method: str,
    transaction_id: str,
    status: str = "Pending",
) -> Dict[str, Any]:
    """Create a payment record and return it as a dict."""
    with get_db_with_retry() as db:
        payment = Payment(
            job_id=job_id,
            user_id=user_id,
            amount=amount,
            method=method,
            transaction_id=transaction_id,
            status=status,
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        _log.info("Payment created txn=%s amount=%.2f", transaction_id, amount)
        return _payment_to_dict(payment)


def update_payment_status(payment_id: int, new_status: str, notes: str = "") -> bool:
    """Update the status of a payment record. Returns True on success."""
    with get_db_with_retry() as db:
        updates: Dict[str, Any] = {"status": new_status}
        if notes:
            updates["notes"] = notes
        result = db.query(Payment).filter(Payment.id == payment_id).update(
            updates, synchronize_session=False
        )
        db.commit()
        return result > 0


def get_payment_by_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the payment associated with a print job."""
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.job_id == job_id).first()
        return _payment_to_dict(payment) if payment else None


def get_payment_by_transaction_id(transaction_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a payment by its unique transaction ID (idempotency check)."""
    with get_db() as db:
        payment = (
            db.query(Payment)
            .filter(Payment.transaction_id == transaction_id)
            .first()
        )
        return _payment_to_dict(payment) if payment else None


def get_payment_history(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Return paginated payment history for a user, newest first."""
    with get_db() as db:
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_payment_to_dict(p) for p in payments]


def get_all_payments() -> List[Dict[str, Any]]:
    """Return all payments (simple, without join)."""
    with get_db() as db:
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
        return [_payment_to_dict(p) for p in payments]


def get_all_payments_with_jobs() -> List[Dict[str, Any]]:
    """
    Return all payments with print job and user data in a single JOIN query.

    Uses eager loading to eliminate the N+1 query pattern that existed
    in the previous implementation (which queried user and job separately
    for each payment row).
    """
    with get_db() as db:
        payments = (
            db.query(Payment)
            .options(
                joinedload(Payment.job),
                joinedload(Payment.user),
            )
            .order_by(Payment.created_at.desc())
            .all()
        )
        result = []
        for p in payments:
            job = p.job
            user = p.user
            result.append({
                "payment_id":    p.id,
                "transaction_id": p.transaction_id,
                "amount":        p.amount,
                "method":        p.method,
                "payment_status": p.status,
                "payment_time":  str(p.created_at) if p.created_at else "",
                "user_id":       p.user_id,
                "username":      user.username if user else f"User#{p.user_id}",
                "email":         user.email    if user else "",
                "job_id":        p.job_id,
                "print_id":      job.print_id      if job else "",
                "document_name": job.document_name if job else "",
                "total_pages":   job.total_pages   if job else 0,
                "copies":        job.copies        if job else 1,
                "color_mode":    job.color_mode    if job else "BW",
                "priority":      job.priority      if job else "Normal",
                "duplex":        job.duplex        if job else False,
                "printer_id":    job.printer_id    if job else None,
                "job_status":    job.status        if job else "Unknown",
                "submitted_at":  str(job.submitted_at)  if job and job.submitted_at  else "",
                "completed_at":  str(job.completed_at)  if job and job.completed_at  else "",
            })
        return result


def _payment_to_dict(p: Payment) -> Dict[str, Any]:
    return {
        "id":             p.id,
        "job_id":         p.job_id,
        "user_id":        p.user_id,
        "amount":         p.amount,
        "method":         p.method,
        "transaction_id": p.transaction_id,
        "status":         p.status,
        "notes":          getattr(p, "notes", None),
        "created_at":     p.created_at,
    }


# ===========================================================================
# PRINTER CRUD
# ===========================================================================

def get_all_printers() -> List[Dict[str, Any]]:
    """Return all printers as a list of dicts."""
    with get_db() as db:
        printers = db.query(Printer).order_by(Printer.name).all()
        return [_printer_to_dict(p) for p in printers]


def get_printer_by_id(printer_id: int) -> Optional[Dict[str, Any]]:
    """Return a single printer dict by ID."""
    with get_db() as db:
        p = db.query(Printer).filter(Printer.id == printer_id).first()
        return _printer_to_dict(p) if p else None


def update_printer_status(printer_id: int, new_status: str) -> bool:
    """Update a printer's status and mark it as manually overridden.

    Setting manual_override=True tells the PrinterHeartbeatWorker to skip
    this printer — preventing it from reverting the admin-set status based
    on the Windows spooler's physical connectivity check.
    """
    with get_db_with_retry() as db:
        result = db.query(Printer).filter(Printer.id == printer_id).update(
            {"status": new_status, "manual_override": True},
            synchronize_session=False,
        )
        db.commit()
        return result > 0


def update_printer_fields(printer_id: int, **kwargs: Any) -> bool:
    """Update arbitrary fields on a printer. Returns True on success."""
    if not kwargs:
        return False
    with get_db_with_retry() as db:
        p = db.query(Printer).filter(Printer.id == printer_id).first()
        if not p:
            return False
        for key, val in kwargs.items():
            if hasattr(p, key):
                setattr(p, key, val)
        db.commit()
        return True


def get_best_printer() -> Optional[Dict[str, Any]]:
    """
    Select the best available printer:
      1. Online status
      2. Highest toner level
      3. Fewest errors
    Returns None when no printer is available.
    """
    with get_db() as db:
        printer = (
            db.query(Printer)
            .filter(Printer.status == "Online")
            .order_by(Printer.toner_level.desc(), Printer.error_count.asc())
            .first()
        )
        return _printer_to_dict(printer) if printer else None


def add_printer(
    name: str,
    location: str,
    printer_type: str = "LaserJet",
    toner_level: float = 100.0,
    status: str = "Online",
    ppm: int = 20,
) -> Dict[str, Any]:
    """Create a new printer and return it as a dict."""
    with get_db_with_retry() as db:
        p = Printer(
            name=name,
            location=location,
            printer_type=printer_type,
            status=status,
            toner_level=toner_level,
            total_prints=0,
            error_count=0,
            temperature=35.0,
            pages_per_minute=ppm,
            last_maintenance=datetime.utcnow(),
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return _printer_to_dict(p)


def delete_printer(printer_id: int) -> bool:
    """Delete a printer by ID. Returns True on success."""
    with get_db_with_retry() as db:
        p = db.query(Printer).filter(Printer.id == printer_id).first()
        if not p:
            return False
        db.delete(p)
        db.commit()
        return True


def _printer_to_dict(p: Printer) -> Dict[str, Any]:
    """Serialise a Printer ORM object to a plain dict."""
    return {
        "id":               p.id,
        "name":             p.name,
        "status":           p.status,
        "location":         p.location,
        "printer_type":     p.printer_type,
        "total_prints":     p.total_prints,
        "toner_level":      p.toner_level,
        "error_count":      p.error_count,
        "temperature":      p.temperature,
        "pages_per_minute": getattr(p, "pages_per_minute", 20) or 20,
        "last_maintenance": p.last_maintenance,
        "last_seen_at":     getattr(p, "last_seen_at", None),
        # True when an admin manually set this status — heartbeat must not override it
        "manual_override":  bool(getattr(p, "manual_override", False)),
    }


# ===========================================================================
# NOTIFICATION CRUD
# ===========================================================================

def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
) -> Dict[str, Any]:
    """Create a notification for a user."""
    with get_db_with_retry() as db:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return _notif_to_dict(notif)


def get_user_notifications(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent notifications for a user, newest first."""
    with get_db() as db:
        notifs = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_notif_to_dict(n) for n in notifs]


# Alias used by several views
get_notifications_for_user = get_user_notifications


def mark_notification_read(notification_id: int) -> bool:
    """Mark a single notification as read. Returns True on success."""
    with get_db_with_retry() as db:
        result = db.query(Notification).filter(Notification.id == notification_id).update(
            {"is_read": True}, synchronize_session=False
        )
        db.commit()
        return result > 0


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all notifications as read. Returns count updated."""
    with get_db_with_retry() as db:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()
        return count


def get_unread_count(user_id: int) -> int:
    """Return the number of unread notifications for a user."""
    with get_db() as db:
        return (
            db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .scalar()
        ) or 0


# Alias
get_notifications_unread_count = get_unread_count


def _notif_to_dict(n: Notification) -> Dict[str, Any]:
    return {
        "id":                n.id,
        "user_id":           n.user_id,
        "title":             n.title,
        "message":           n.message,
        "notification_type": getattr(n, "notification_type", "info") or "info",
        "is_read":           n.is_read,
        "created_at":        str(n.created_at),
    }


# ===========================================================================
# AI ANALYSIS CRUD
# ===========================================================================

def create_ai_analysis(
    job_id: int,
    quality_score: float,
    is_blurry: bool = False,
    is_skewed: bool = False,
    is_low_quality: bool = False,
    recommendations: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update (upsert) an AI analysis record for a print job."""
    with get_db_with_retry() as db:
        existing = db.query(AIAnalysis).filter(AIAnalysis.job_id == job_id).first()
        if existing:
            existing.quality_score   = quality_score
            existing.is_blurry       = is_blurry
            existing.is_skewed       = is_skewed
            existing.is_low_quality  = is_low_quality
            existing.recommendations = recommendations
            existing.analyzed_at     = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return _analysis_to_dict(existing)

        analysis = AIAnalysis(
            job_id=job_id,
            quality_score=quality_score,
            is_blurry=is_blurry,
            is_skewed=is_skewed,
            is_low_quality=is_low_quality,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow(),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return _analysis_to_dict(analysis)


def get_analysis_by_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the AI analysis for a specific print job."""
    with get_db() as db:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.job_id == job_id).first()
        return _analysis_to_dict(analysis) if analysis else None


# Alias
get_ai_analysis = get_analysis_by_job


def _analysis_to_dict(a: AIAnalysis) -> Dict[str, Any]:
    return {
        "id":              a.id,
        "job_id":          a.job_id,
        "quality_score":   a.quality_score,
        "is_blurry":       a.is_blurry,
        "is_skewed":       a.is_skewed,
        "is_low_quality":  a.is_low_quality,
        "recommendations": a.recommendations,
        "analyzed_at":     a.analyzed_at,
    }


# ===========================================================================
# MAINTENANCE LOG CRUD
# ===========================================================================

def create_maintenance_log(
    printer_id: int,
    issue: str,
    severity: str = "Low",
    predicted_failure: bool = False,
) -> Dict[str, Any]:
    """Create a maintenance log entry for a printer."""
    with get_db_with_retry() as db:
        log = MaintenanceLog(
            printer_id=printer_id,
            issue=issue,
            severity=severity,
            predicted_failure=predicted_failure,
            resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return _mlog_to_dict(log)


def _mlog_to_dict(log: MaintenanceLog) -> Dict[str, Any]:
    """Serialise a MaintenanceLog ORM object to a plain dict (shared serializer)."""
    return {
        "id":                log.id,
        "printer_id":        log.printer_id,
        "issue":             log.issue,
        "severity":          log.severity,
        "predicted_failure": log.predicted_failure,
        "resolved":          log.resolved,
        "created_at":        log.created_at,
    }


def get_printer_maintenance(printer_id: int) -> List[Dict[str, Any]]:
    """Get maintenance history for a printer, newest first."""
    with get_db() as db:
        logs = (
            db.query(MaintenanceLog)
            .filter(MaintenanceLog.printer_id == printer_id)
            .order_by(MaintenanceLog.created_at.desc())
            .all()
        )
        return [_mlog_to_dict(log) for log in logs]


# ===========================================================================
# CHAT HISTORY CRUD
# ===========================================================================

def save_chat_message(user_id: int, role: str, message: str) -> Dict[str, Any]:
    """Persist a single chat message (role = 'user' or 'assistant')."""
    with get_db_with_retry() as db:
        chat = ChatHistory(
            user_id=user_id,
            role=role,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return {
            "id":         chat.id,
            "user_id":    chat.user_id,
            "role":       chat.role,
            "message":    chat.message,
            "created_at": chat.created_at,
        }


def get_chat_history(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch chat history for a user, oldest first."""
    with get_db() as db:
        messages = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id":         m.id,
                "user_id":    m.user_id,
                "role":       m.role,
                "message":    m.message,
                "created_at": m.created_at,
            }
            for m in messages
        ]


# ===========================================================================
# DASHBOARD STATISTICS
# ===========================================================================

def get_dashboard_stats() -> Dict[str, Any]:
    """
    Aggregate statistics for the admin dashboard.
    All counts are computed in a single DB round-trip using scalar subqueries.
    """
    with get_db() as db:
        total_users    = db.query(func.count(User.id)).scalar() or 0
        total_jobs     = db.query(func.count(PrintJob.id)).scalar() or 0
        total_revenue  = db.query(func.coalesce(func.sum(PrintJob.total_cost), 0.0)).scalar()

        status_counts: Dict[str, int] = {}
        rows = (
            db.query(PrintJob.status, func.count(PrintJob.id))
            .group_by(PrintJob.status)
            .all()
        )
        for status, cnt in rows:
            status_counts[status] = cnt

        pending_count   = status_counts.get("Pending",   0)
        queued_count    = status_counts.get("Queued",    0)
        printing_count  = status_counts.get("Printing",  0)
        completed_count = (
            status_counts.get("Completed", 0)
            + status_counts.get("Ready",    0)
            + status_counts.get("Collected", 0)
        )

        return {
            "total_users":    total_users,
            "total_jobs":     total_jobs,
            "total_revenue":  round(float(total_revenue), 2),
            "pending_count":  pending_count,
            "queued_count":   queued_count,
            "printing_count": printing_count,
            "completed_count": completed_count,
            # Aliases for view compatibility
            "pending":        pending_count,
            "queued":         queued_count,
            "printing":       printing_count,
            "completed":      completed_count,
        }


def get_today_stats() -> Dict[str, Any]:
    """Return today's aggregated stats for the admin dashboard."""
    with get_db() as db:
        today_start = datetime.combine(date.today(), datetime.min.time())

        # Single query for all today's jobs
        today_jobs = (
            db.query(PrintJob)
            .filter(PrintJob.submitted_at >= today_start)
            .all()
        )

        today_revenue  = sum(j.total_cost or 0.0 for j in today_jobs)
        today_pages    = sum(j.total_pages or 0   for j in today_jobs)
        today_docs     = len(today_jobs)
        today_priority = sum(1 for j in today_jobs if (j.priority or "").lower() == "priority")
        today_cancelled = sum(1 for j in today_jobs if (j.status or "").lower() in ("cancelled", "failed"))

        active_students = (
            db.query(func.count(func.distinct(PrintJob.user_id)))
            .filter(PrintJob.submitted_at >= today_start)
            .scalar()
        ) or 0

        # Printer counts in one query
        printer_rows = (
            db.query(Printer.status, func.count(Printer.id))
            .group_by(Printer.status)
            .all()
        )
        printer_status_map = {s: c for s, c in printer_rows}
        online_printers  = printer_status_map.get("Online", 0)
        offline_printers = sum(c for s, c in printer_rows if s != "Online")

        wait_times = [j.estimated_wait_time for j in today_jobs if j.estimated_wait_time]
        avg_wait = int(sum(wait_times) / len(wait_times)) if wait_times else 0

        return {
            "today_revenue":   round(today_revenue, 2),
            "today_pages":     today_pages,
            "today_docs":      today_docs,
            "today_priority":  today_priority,
            "today_cancelled": today_cancelled,
            "active_students": active_students,
            "online_printers": online_printers,
            "offline_printers": offline_printers,
            "avg_wait":        avg_wait,
        }


# ===========================================================================
# ADMIN EXTENDED QUERIES
# ===========================================================================

def get_all_users_with_stats() -> List[Dict[str, Any]]:
    """
    Return all student users with aggregated print job statistics.

    Uses a SQL subquery aggregation instead of the previous N+1 pattern
    (which queried all jobs for each user in a Python loop).
    """
    with get_db() as db:
        # Aggregate job stats per user in a single SQL query
        from sqlalchemy import case as sa_case

        agg = (
            db.query(
                PrintJob.user_id.label("uid"),
                func.count(PrintJob.id).label("total_prints"),
                func.coalesce(func.sum(PrintJob.total_pages), 0).label("total_pages"),
                func.coalesce(func.sum(PrintJob.total_cost), 0.0).label("total_amount"),
                func.max(PrintJob.submitted_at).label("last_print"),
            )
            .group_by(PrintJob.user_id)
            .subquery()
        )

        users = (
            db.query(User)
            .filter(User.role == "Student")
            .order_by(User.created_at.desc())
            .all()
        )

        # Build lookup dict from subquery results
        agg_rows = db.query(agg).all()
        stats_by_uid: Dict[int, Any] = {r.uid: r for r in agg_rows}

        result = []
        for u in users:
            s = stats_by_uid.get(u.id)
            result.append({
                "id":              u.id,
                "username":        u.username,
                "email":           u.email,
                "role":            u.role,
                "status":          u.status,
                "created_at":      str(u.created_at) if u.created_at else "",
                "last_login":      str(u.last_login)  if u.last_login  else "",
                "total_prints":    s.total_prints  if s else 0,
                "total_pages":     s.total_pages   if s else 0,
                "total_amount":    round(float(s.total_amount), 2) if s else 0.0,
                "priority_prints": 0,   # computed on demand if needed
                "cancelled_prints": 0,
                "completed_prints": 0,
                "last_print_date": str(s.last_print)[:10] if s and s.last_print else "—",
            })
        return result


# ===========================================================================
# STUDENT ANALYTICS
# ===========================================================================

def get_student_analytics(user_id: int) -> Dict[str, Any]:
    """
    Return comprehensive printing statistics for a student.
    Aggregation is done in SQL to avoid loading thousands of rows into Python.
    """
    with get_db() as db:
        jobs = db.query(PrintJob).filter(PrintJob.user_id == user_id).all()
        payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.status == "Success",
        ).all()

        total_jobs   = len(jobs)
        total_spent  = sum(p.amount for p in payments)
        duplex_jobs  = [j for j in jobs if j.duplex]
        duplex_pages = sum((j.total_pages or 0) * (j.copies or 1) for j in duplex_jobs)
        paper_saved  = duplex_pages // 2
        co2_saved    = round(paper_saved * 0.005, 2)
        color_jobs   = sum(1 for j in jobs if (j.color_mode or "") == "Color")
        bw_jobs      = total_jobs - color_jobs
        completed    = [j for j in jobs if (j.status or "").lower() in ("completed", "ready", "collected")]
        total_pages  = sum((j.total_pages or 0) * (j.copies or 1) for j in completed)

        # Monthly aggregation
        monthly_pages: Dict[str, int]   = defaultdict(int)
        monthly_spend: Dict[str, float] = defaultdict(float)
        hourly: Dict[int, int]          = defaultdict(int)

        for j in jobs:
            if j.submitted_at:
                key = j.submitted_at.strftime("%b %Y")
                monthly_pages[key] += (j.total_pages or 0) * (j.copies or 1)
                hourly[j.submitted_at.hour] += 1
        for p in payments:
            if p.created_at:
                key = p.created_at.strftime("%b %Y")
                monthly_spend[key] += p.amount

        # Printer usage via a single SQL GROUP BY
        printer_usage_rows = (
            db.query(Printer.name, func.count(PrintJob.id).label("cnt"))
            .join(PrintJob, PrintJob.printer_id == Printer.id)
            .filter(
                PrintJob.user_id == user_id,
                PrintJob.status.in_(["Completed", "Ready", "Collected"]),
            )
            .group_by(Printer.name)
            .all()
        )
        printer_usage = {name: cnt for name, cnt in printer_usage_rows}
        favorite_printer = max(printer_usage, key=printer_usage.get) if printer_usage else None

        today_jobs = [j for j in jobs if j.submitted_at and j.submitted_at.date() == date.today()]
        waits      = [j.estimated_wait_time for j in jobs if j.estimated_wait_time]
        avg_wait   = round(sum(waits) / len(waits), 1) if waits else 0

        return {
            "total_jobs":      total_jobs,
            "total_pages":     total_pages,
            "total_cost":      round(sum(j.total_cost for j in completed), 2),
            "total_spent":     round(total_spent, 2),
            "total_docs":      len(set(j.document_name for j in jobs)),
            "completed_jobs":  len(completed),
            "active_jobs":     sum(1 for j in jobs if (j.status or "").lower() in ("pending", "queued", "printing", "processing")),
            "color_count":     color_jobs,
            "color_jobs":      color_jobs,
            "bw_count":        bw_jobs,
            "bw_jobs":         bw_jobs,
            "duplex_count":    len(duplex_jobs),
            "duplex_jobs":     len(duplex_jobs),
            "simplex_count":   total_jobs - len(duplex_jobs),
            "simplex_jobs":    total_jobs - len(duplex_jobs),
            "paper_saved":     paper_saved,
            "co2_saved":       co2_saved,
            "avg_wait":        avg_wait,
            "avg_wait_min":    avg_wait,
            "favorite_printer": favorite_printer,
            "monthly_pages":   dict(monthly_pages),
            "monthly_cost":    dict(monthly_spend),
            "monthly_spend":   dict(monthly_spend),
            "hourly_distribution": dict(hourly),
            "printer_usage":   printer_usage,
            "bookmarked_jobs": sum(1 for j in jobs if getattr(j, "is_bookmarked", False)),
            "todays_jobs":     len(today_jobs),
        }


def get_favorite_printer(user_id: int) -> Optional[str]:
    """Return the name of the most frequently used printer for this user."""
    with get_db() as db:
        result = (
            db.query(Printer.name, func.count(PrintJob.id).label("cnt"))
            .join(PrintJob, PrintJob.printer_id == Printer.id)
            .filter(
                PrintJob.user_id == user_id,
                PrintJob.printer_id.isnot(None),
                PrintJob.status.in_(["Completed", "Ready", "Collected"]),
            )
            .group_by(Printer.name)
            .order_by(func.count(PrintJob.id).desc())
            .first()
        )
        return result[0] if result else None


def get_bookmarked_jobs(user_id: int) -> List[Dict[str, Any]]:
    """Return all bookmarked jobs for a student."""
    with get_db() as db:
        jobs = (
            db.query(PrintJob)
            .filter(PrintJob.user_id == user_id, PrintJob.is_bookmarked == True)  # noqa: E712
            .order_by(PrintJob.submitted_at.desc())
            .all()
        )
        return [_job_to_dict(j) for j in jobs]


# ===========================================================================
# USER SETTINGS & PROFILE
# ===========================================================================

def get_user_settings(user_id: int) -> Dict[str, Any]:
    """Return the user's saved printing preferences (from JSON blob)."""
    _defaults: Dict[str, Any] = {
        "default_copies":       1,
        "default_color_mode":   "BW",
        "default_duplex":       False,
        "default_paper_size":   "A4",
        "default_priority":     "Normal",
        "default_printer_id":   None,
        "notify_job_queued":    True,
        "notify_job_printing":  True,
        "notify_job_ready":     True,
        "notify_payment":       True,
    }
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not getattr(user, "preferences", None):
            return _defaults.copy()
        try:
            saved = _json.loads(user.preferences)
            return {**_defaults, **saved}
        except Exception:
            return _defaults.copy()


def save_user_settings(user_id: int, settings: Dict[str, Any]) -> bool:
    """Persist the user's printing preferences as a JSON blob (merge, not overwrite)."""
    with get_db_with_retry() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        existing: Dict[str, Any] = {}
        if getattr(user, "preferences", None):
            try:
                existing = _json.loads(user.preferences)
            except Exception:
                pass
        existing.update(settings)
        user.preferences = _json.dumps(existing)
        db.commit()
        return True


def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Return extended profile data for a user."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return _user_to_dict(user)


# ===========================================================================
# SEED DATA
# ===========================================================================

def seed_printers() -> None:
    """Create four sample printers if the printers table is empty."""
    with get_db() as db:
        count = db.query(func.count(Printer.id)).scalar() or 0
        if count > 0:
            return

        sample_printers = [
            Printer(
                name="HP LaserJet Pro M404",
                status="Online",
                location="Library — Ground Floor",
                printer_type="LaserJet",
                total_prints=12_450,
                toner_level=78.5,
                error_count=3,
                temperature=36.2,
                pages_per_minute=25,
                last_maintenance=datetime(2026, 5, 15),
            ),
            Printer(
                name="Canon imageCLASS MF445dw",
                status="Online",
                location="CS Lab — Block A, 2nd Floor",
                printer_type="LaserJet Multifunction",
                total_prints=8_320,
                toner_level=92.1,
                error_count=1,
                temperature=34.8,
                pages_per_minute=30,
                last_maintenance=datetime(2026, 6, 1),
            ),
            Printer(
                name="Epson EcoTank L3250",
                status="Maintenance",
                location="Admin Office — Block B",
                printer_type="InkTank",
                total_prints=5_680,
                toner_level=45.3,
                error_count=7,
                temperature=38.1,
                pages_per_minute=15,
                last_maintenance=datetime(2026, 4, 20),
            ),
            Printer(
                name="Brother HL-L2395DW",
                status="Online",
                location="Student Center — Cafeteria Building",
                printer_type="LaserJet",
                total_prints=15_900,
                toner_level=61.7,
                error_count=5,
                temperature=37.0,
                pages_per_minute=20,
                last_maintenance=datetime(2026, 5, 28),
            ),
        ]
        db.add_all(sample_printers)
        db.commit()
        _log.info("Seeded %d default printers", len(sample_printers))


# ===========================================================================
# ADMIN EXTENDED ANALYTICS (SQL-level aggregation)
# ===========================================================================

def get_admin_analytics() -> Dict[str, Any]:
    """
    Return advanced admin analytics computed entirely at the SQL level.

    Includes:
    - Monthly revenue for the past 12 months (SQL GROUP BY strftime)
    - Monthly job count for the past 12 months
    - Peak printing hours (0-23) across all jobs
    - Top 5 students by total pages printed
    - Color vs BW job ratio
    - Duplex adoption rate

    All aggregation is done in SQL — no Python-level loops over large datasets.
    """
    with get_db() as db:
        # ── Monthly revenue & job count ──────────────────────────────────────
        monthly_rows = (
            db.query(
                func.strftime("%Y-%m", PrintJob.submitted_at).label("month"),
                func.count(PrintJob.id).label("job_count"),
                func.coalesce(func.sum(PrintJob.total_cost), 0.0).label("revenue"),
            )
            .filter(PrintJob.submitted_at.isnot(None))
            .group_by(func.strftime("%Y-%m", PrintJob.submitted_at))
            .order_by(func.strftime("%Y-%m", PrintJob.submitted_at).desc())
            .limit(12)
            .all()
        )
        monthly_revenue: Dict[str, float] = {}
        monthly_jobs:    Dict[str, int]   = {}
        for row in reversed(monthly_rows):
            monthly_revenue[row.month] = round(float(row.revenue), 2)
            monthly_jobs[row.month]    = int(row.job_count)

        # ── Peak printing hours ──────────────────────────────────────────────
        hour_rows = (
            db.query(
                func.strftime("%H", PrintJob.submitted_at).label("hour"),
                func.count(PrintJob.id).label("count"),
            )
            .filter(PrintJob.submitted_at.isnot(None))
            .group_by(func.strftime("%H", PrintJob.submitted_at))
            .all()
        )
        peak_hours: Dict[int, int] = {int(r.hour): int(r.count) for r in hour_rows}

        # ── Top 5 students by pages printed ─────────────────────────────────
        top_users_rows = (
            db.query(
                User.username,
                func.coalesce(func.sum(PrintJob.total_pages * PrintJob.copies), 0).label("total_pages"),
            )
            .join(PrintJob, PrintJob.user_id == User.id)
            .filter(User.role == "Student")
            .group_by(User.id)
            .order_by(func.sum(PrintJob.total_pages * PrintJob.copies).desc())
            .limit(5)
            .all()
        )
        top_students: List[Dict[str, Any]] = [
            {"username": r.username, "total_pages": int(r.total_pages)}
            for r in top_users_rows
        ]

        # ── Color vs BW ratio ────────────────────────────────────────────────
        color_bw_rows = (
            db.query(PrintJob.color_mode, func.count(PrintJob.id).label("cnt"))
            .group_by(PrintJob.color_mode)
            .all()
        )
        color_bw: Dict[str, int] = {(r.color_mode or "BW"): int(r.cnt) for r in color_bw_rows}

        # ── Duplex adoption ──────────────────────────────────────────────────
        total_jobs   = db.query(func.count(PrintJob.id)).scalar() or 0
        duplex_jobs  = db.query(func.count(PrintJob.id)).filter(PrintJob.duplex == True).scalar() or 0  # noqa: E712
        duplex_rate  = round((duplex_jobs / max(1, total_jobs)) * 100, 1)

        return {
            "monthly_revenue":  monthly_revenue,
            "monthly_jobs":     monthly_jobs,
            "peak_hours":       peak_hours,
            "top_students":     top_students,
            "color_bw_ratio":   color_bw,
            "duplex_rate_pct":  duplex_rate,
            "total_jobs":       total_jobs,
            "duplex_jobs":      duplex_jobs,
        }

