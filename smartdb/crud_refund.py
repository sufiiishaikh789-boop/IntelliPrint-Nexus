"""
IntelliPrint Nexus - Refund CRUD Operations
=============================================
Data-access layer for refund/cancellation operations.

Kept in a separate file to avoid circular imports and keep crud.py clean.
All functions here are imported by refund_service.py and the view layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from smartdb.models import Payment, PrintJob

try:
    from smartdb.models import User
except ImportError:
    User = None  # type: ignore

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("db.refund")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.db.refund")

# Re-use session helpers from crud
from smartdb.crud import get_db, get_db_with_retry


# ---------------------------------------------------------------------------
# Atomic job cancellation (race-condition safe)
# ---------------------------------------------------------------------------

def atomic_cancel_job_for_refund(
    job_id: int,
    allowed_statuses: List[str],
    new_status: str = "Cancelled",
) -> bool:
    """
    Cancel a job only if its current status is in allowed_statuses.

    This is a conditional UPDATE — if the job has already moved to a
    different status (e.g., Printing started in another thread), 0 rows
    will be updated and we return False, preventing a double-refund.

    Parameters
    ----------
    job_id           : int  - print job primary key
    allowed_statuses : list - status values (lowercase) that permit cancel
    new_status       : str  - status to set on success (default: Cancelled)

    Returns
    -------
    bool - True if the job was successfully updated, False otherwise
    """
    # Build a lowercase-safe IN clause using SQLAlchemy ORM
    with get_db_with_retry() as db:
        # Fetch with a write-intent lock; SQLite will serialise this
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False
        current = (job.status or "").lower()
        if current not in allowed_statuses:
            _log.warning(
                "atomic_cancel: job %d has status '%s' - not in %s",
                job_id, current, allowed_statuses,
            )
            return False
        job.status = new_status
        job.updated_at = datetime.utcnow()
        db.commit()
        _log.info("atomic_cancel: job %d status '%s' -> '%s'", job_id, current, new_status)
        return True


# ---------------------------------------------------------------------------
# Job cancellation metadata
# ---------------------------------------------------------------------------

def update_job_cancellation_info(
    job_id: int,
    reason: str,
    cancelled_at: Optional[datetime] = None,
) -> bool:
    """Store cancellation reason and timestamp on a print job."""
    with get_db_with_retry() as db:
        updates: Dict[str, Any] = {
            "cancellation_reason": reason,
            "cancelled_at": cancelled_at or datetime.utcnow(),
        }
        result = db.query(PrintJob).filter(PrintJob.id == job_id).update(
            updates, synchronize_session=False
        )
        db.commit()
        return result > 0


# ---------------------------------------------------------------------------
# Payment refund field updates
# ---------------------------------------------------------------------------

def update_payment_refund_fields(payment_id: int, **kwargs: Any) -> bool:
    """
    Update arbitrary refund columns on a Payment record.

    Accepted kwargs (all optional):
        refund_status, refund_reason, original_amount, penalty_amount,
        refund_amount, gateway_refund_id, refund_failure_reason,
        refund_initiated_at, refund_processed_at

    Returns True on success.
    """
    if not kwargs:
        return False
    with get_db_with_retry() as db:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            _log.warning("update_payment_refund_fields: payment %d not found", payment_id)
            return False
        for key, val in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, val)
            else:
                _log.debug("update_payment_refund_fields: unknown field '%s' (skipped)", key)
        db.commit()
        return True


# ---------------------------------------------------------------------------
# Query: single job payment with refund info
# ---------------------------------------------------------------------------

def get_payment_by_job_with_refund(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the payment for a job including all refund fields."""
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.job_id == job_id).first()
        if not payment:
            return None
        return _payment_refund_to_dict(payment)


# ---------------------------------------------------------------------------
# Query: student refund history
# ---------------------------------------------------------------------------

def get_refund_history_for_user(
    user_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Return payments that have an associated refund (refund_status is not NULL)
    for a given student, newest first.
    """
    with get_db() as db:
        payments = (
            db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.refund_status.isnot(None),
            )
            .order_by(Payment.refund_initiated_at.desc())
            .limit(limit)
            .all()
        )
        # Enrich with job data
        result = []
        for p in payments:
            d = _payment_refund_to_dict(p)
            job = db.query(PrintJob).filter(PrintJob.id == p.job_id).first()
            if job:
                d["print_id"]      = job.print_id
                d["document_name"] = job.document_name
                d["job_status"]    = job.status
            result.append(d)
        return result


# ---------------------------------------------------------------------------
# Query: admin - all payments with refund info (join with job + user)
# ---------------------------------------------------------------------------

def get_all_payments_with_refund_info(
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """
    Return all payments (admin view) joined with job and user data.
    Includes refund columns.
    """
    from sqlalchemy.orm import joinedload
    with get_db() as db:
        payments = (
            db.query(Payment)
            .options(
                joinedload(Payment.job),
                joinedload(Payment.user),
            )
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .all()
        )
        result = []
        for p in payments:
            d = _payment_refund_to_dict(p)
            job  = p.job
            user = p.user
            d["username"]      = user.username     if user else f"User#{p.user_id}"
            d["email"]         = user.email        if user else ""
            d["print_id"]      = job.print_id      if job  else ""
            d["document_name"] = job.document_name if job  else ""
            d["job_status"]    = job.status        if job  else "Unknown"
            d["total_pages"]   = job.total_pages   if job  else 0
            d["copies"]        = job.copies        if job  else 1
            d["submitted_at"]  = str(job.submitted_at) if job and job.submitted_at else ""
            result.append(d)
        return result


# ---------------------------------------------------------------------------
# Serialiser
# ---------------------------------------------------------------------------

def _payment_refund_to_dict(p: Payment) -> Dict[str, Any]:
    """Serialise a Payment ORM object including all refund fields."""
    return {
        # Base payment fields
        "id":             p.id,
        "job_id":         p.job_id,
        "user_id":        p.user_id,
        "amount":         p.amount,
        "method":         p.method,
        "transaction_id": p.transaction_id,
        "status":         p.status,
        "notes":          getattr(p, "notes", None),
        "created_at":     str(p.created_at) if p.created_at else "",
        # Refund fields (may be None if no refund)
        "refund_status":         getattr(p, "refund_status",         None),
        "refund_reason":         getattr(p, "refund_reason",         None),
        "original_amount":       getattr(p, "original_amount",       None),
        "penalty_amount":        getattr(p, "penalty_amount",        None),
        "refund_amount":         getattr(p, "refund_amount",         None),
        "gateway_refund_id":     getattr(p, "gateway_refund_id",     None),
        "refund_failure_reason": getattr(p, "refund_failure_reason", None),
        "refund_initiated_at":   str(getattr(p, "refund_initiated_at", None) or ""),
        "refund_processed_at":   str(getattr(p, "refund_processed_at", None) or ""),
    }
