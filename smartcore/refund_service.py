"""
IntelliPrint Nexus - Refund Service
=====================================
Backend-only, security-hardened refund engine.

Rules enforced server-side (never trusting client input):
  - QUEUED job cancelled by owning student: 2% penalty, 98% refund
  - PRINTING job: refund request REJECTED (no refund)
  - COMPLETED / already CANCELLED / already REFUNDED: rejected (no duplicate)
  - Admin marks POWER_FAILURE: 100% refund, 0% penalty (admin-only)

Race-condition mitigation:
  Uses a conditional SQL UPDATE (WHERE status in allowed_statuses) inside a
  single DB transaction. If 0 rows are updated, another thread already changed
  the status and the cancellation is safely rejected.

Payment gateway:
  Currently simulated. Replace _simulate_gateway_refund() with a real
  Razorpay / PayU / Paytm SDK call when a live gateway is available.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("refund")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.refund")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CANCELLATION_PENALTY_RATE = 0.02   # 2% deducted on student cancellation
POWER_FAILURE_PENALTY_RATE = 0.00  # 0% - full refund

REASON_STUDENT_CANCELLATION = "STUDENT_CANCELLATION"
REASON_POWER_FAILURE         = "POWER_FAILURE"

STATUS_PENDING    = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_REFUNDED   = "REFUNDED"
STATUS_FAILED     = "FAILED"

# Job statuses that allow student-initiated cancellation
_STUDENT_CANCELLABLE_STATUSES = frozenset({
    "queued",
    "pending",
    "waiting",
})

# Job statuses where NO refund is possible (mid-print or done)
_NO_REFUND_STATUSES = frozenset({
    "printing",
    "preparing",
    "completed",
    "ready",
    "collected",
})

# Power failure allowed for these statuses
_PF_ALLOWED_STATUSES = frozenset({"queued", "printing", "pending", "preparing"})


# ---------------------------------------------------------------------------
# Calculation (pure function - no DB access, easy to unit-test)
# ---------------------------------------------------------------------------

def calculate_refund(
    paid_amount: float,
    reason: str,
) -> Tuple[float, float]:
    """
    Calculate penalty and refund amounts.

    Parameters
    ----------
    paid_amount : float - original amount paid (in rupees)
    reason      : str   - STUDENT_CANCELLATION | POWER_FAILURE

    Returns
    -------
    (penalty_amount, refund_amount) - both rounded to 2 decimal places

    Examples
    --------
    >>> calculate_refund(100, "STUDENT_CANCELLATION")
    (2.0, 98.0)
    >>> calculate_refund(500, "POWER_FAILURE")
    (0.0, 500.0)
    """
    # Use integer paise arithmetic to avoid floating-point rounding errors
    paid_paise = round(paid_amount * 100)

    if reason == REASON_POWER_FAILURE:
        penalty_paise = 0
    else:
        # 2% rounded to nearest paise
        penalty_paise = round(paid_paise * CANCELLATION_PENALTY_RATE)

    refund_paise = paid_paise - penalty_paise

    penalty = round(penalty_paise / 100, 2)
    refund  = round(refund_paise  / 100, 2)
    return penalty, refund


# ---------------------------------------------------------------------------
# Gateway simulation (replace with real SDK for production)
# ---------------------------------------------------------------------------

def _simulate_gateway_refund(
    transaction_id: str,
    refund_amount: float,
    reason: str,
) -> Dict[str, Any]:
    """
    Simulate a payment gateway refund call.

    In production replace this function body with a real SDK call, e.g.:
        import razorpay
        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
        return client.payment.refund(payment_id, {"amount": int(refund_amount*100)})

    Returns a dict with:
        success          : bool
        gateway_refund_id: str  (simulated RFD-xxx ID)
        failure_reason   : str | None
    """
    import random
    import string
    gw_id = "RFD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    _log.info(
        "GATEWAY (simulated) refund txn=%s amount=%.2f reason=%s -> %s",
        transaction_id, refund_amount, reason, gw_id,
    )
    return {
        "success":           True,
        "gateway_refund_id": gw_id,
        "failure_reason":    None,
    }


# ---------------------------------------------------------------------------
# Core: Student cancellation
# ---------------------------------------------------------------------------

def process_student_cancellation(
    job_id: int,
    requesting_user_id: int,
) -> Dict[str, Any]:
    """
    Cancel a queued print job on behalf of a student and initiate a refund.

    Security
    --------
    - Validates that requesting_user_id owns the job.
    - All refund amounts calculated server-side (not from client input).
    - Uses a conditional DB update to prevent race conditions.
    - Rejects duplicate refund attempts.

    Returns
    -------
    dict with keys:
        success       : bool
        message       : str
        penalty       : float | None
        refund_amount : float | None
        paid_amount   : float | None
        refund_status : str | None
    """
    from smartdb.crud import (
        get_job_by_id,
        get_payment_by_job,
        update_payment_status,
    )
    from smartdb.crud_refund import (
        atomic_cancel_job_for_refund,
        update_payment_refund_fields,
        update_job_cancellation_info,
    )

    # 1. Fetch the job
    job = get_job_by_id(job_id)
    if not job:
        return {"success": False, "message": "Print job not found."}

    # 2. Ownership check (SECURITY: student can only cancel their own jobs)
    if job.get("user_id") != requesting_user_id:
        _log.warning(
            "SECURITY: user %d tried to cancel job %d belonging to user %d",
            requesting_user_id, job_id, job.get("user_id"),
        )
        return {
            "success": False,
            "message": "You are not authorised to cancel this print job.",
        }

    current_status = (job.get("status") or "").lower()
    print_id = job.get("print_id", f"JOB-{job_id}")

    # 3. Status eligibility check
    if current_status in _NO_REFUND_STATUSES:
        if current_status in ("printing", "preparing"):
            msg = (
                "Printing has already started. "
                "This print job is not eligible for a refund."
            )
            _send_ineligible_notification(requesting_user_id, print_id, msg)
            return {"success": False, "message": msg, "refund_amount": 0.0}
        else:
            return {
                "success": False,
                "message": f"This job cannot be cancelled (status: {job.get('status')}).",
            }

    if current_status == "cancelled":
        return {"success": False, "message": "This job is already cancelled."}

    # 4. Fetch payment record
    payment = get_payment_by_job(job_id)
    if not payment:
        return {
            "success": False,
            "message": "No payment record found for this job.",
        }
    if (payment.get("status") or "").lower() not in ("success",):
        return {
            "success": False,
            "message": "Payment for this job is not confirmed. Cannot refund.",
        }

    # 5. Duplicate refund check
    existing_refund_status = payment.get("refund_status")
    if existing_refund_status in (STATUS_REFUNDED, STATUS_PROCESSING, STATUS_PENDING):
        return {
            "success": False,
            "message": f"A refund is already in progress (status: {existing_refund_status}).",
        }

    # 6. Calculate refund (server-side ONLY - never trust client values)
    paid_amount = float(payment.get("amount") or 0.0)
    if paid_amount <= 0:
        return {"success": False, "message": "Invalid payment amount for refund."}

    penalty, refund_amount = calculate_refund(paid_amount, REASON_STUDENT_CANCELLATION)

    # 7. Atomic job cancellation (race-condition safe)
    # Only cancels if job is STILL in an allowed status at DB time
    cancelled = atomic_cancel_job_for_refund(
        job_id,
        allowed_statuses=list(_STUDENT_CANCELLABLE_STATUSES),
        new_status="Cancelled",
    )
    if not cancelled:
        return {
            "success": False,
            "message": (
                "This job could not be cancelled. "
                "It may have moved to Printing or already been cancelled. "
                "Please refresh and try again."
            ),
        }

    # 8. Store cancellation metadata on the job
    update_job_cancellation_info(
        job_id=job_id,
        reason=f"Student cancellation by user #{requesting_user_id}",
        cancelled_at=datetime.utcnow(),
    )

    # 9. Mark refund as PENDING before gateway call
    payment_id = payment["id"]
    update_payment_refund_fields(
        payment_id=payment_id,
        refund_status=STATUS_PENDING,
        refund_reason=REASON_STUDENT_CANCELLATION,
        original_amount=paid_amount,
        penalty_amount=penalty,
        refund_amount=refund_amount,
        refund_initiated_at=datetime.utcnow(),
    )

    # 10. Call payment gateway
    txn_id = payment.get("transaction_id", "")
    gw_result = _simulate_gateway_refund(txn_id, refund_amount, REASON_STUDENT_CANCELLATION)

    if gw_result["success"]:
        update_payment_refund_fields(
            payment_id=payment_id,
            refund_status=STATUS_REFUNDED,
            gateway_refund_id=gw_result["gateway_refund_id"],
            refund_processed_at=datetime.utcnow(),
        )
        update_payment_status(
            payment_id,
            "Refunded",
            notes=(
                f"Refunded Rs.{refund_amount:.2f} (penalty Rs.{penalty:.2f}). "
                f"Reason: Student Cancellation. GW: {gw_result['gateway_refund_id']}"
            ),
        )
        _log.info(
            "REFUND SUCCESS job_id=%d user=%d paid=%.2f penalty=%.2f refund=%.2f gw=%s",
            job_id, requesting_user_id, paid_amount, penalty, refund_amount,
            gw_result["gateway_refund_id"],
        )
        _send_cancellation_refund_notification(
            user_id=requesting_user_id,
            print_id=print_id,
            paid_amount=paid_amount,
            penalty=penalty,
            refund_amount=refund_amount,
        )
        return {
            "success":       True,
            "message":       "Print job cancelled and refund initiated successfully.",
            "paid_amount":   paid_amount,
            "penalty":       penalty,
            "refund_amount": refund_amount,
            "refund_status": STATUS_REFUNDED,
        }
    else:
        update_payment_refund_fields(
            payment_id=payment_id,
            refund_status=STATUS_FAILED,
            refund_failure_reason=gw_result.get("failure_reason", "Gateway error"),
            refund_processed_at=datetime.utcnow(),
        )
        _log.error(
            "REFUND GATEWAY FAILED job_id=%d reason=%s",
            job_id, gw_result.get("failure_reason"),
        )
        _send_refund_failed_notification(user_id=requesting_user_id, print_id=print_id)
        return {
            "success":       False,
            "message":       "Refund gateway failed. Admin notified. Please contact support.",
            "refund_status": STATUS_FAILED,
        }


# ---------------------------------------------------------------------------
# Core: Admin power-failure refund
# ---------------------------------------------------------------------------

def process_power_failure_refund(
    job_id: int,
    admin_user_id: int,
) -> Dict[str, Any]:
    """
    Issue a full refund because of a printing-centre power failure.

    SECURITY: Only call this after verifying Admin role via require_admin().

    Returns
    -------
    dict with success, message, refund_amount, refund_status
    """
    from smartdb.crud import (
        get_job_by_id,
        get_payment_by_job,
        update_payment_status,
    )
    from smartdb.crud_refund import (
        atomic_cancel_job_for_refund,
        update_payment_refund_fields,
        update_job_cancellation_info,
    )

    # 1. Fetch job
    job = get_job_by_id(job_id)
    if not job:
        return {"success": False, "message": "Print job not found."}

    current_status = (job.get("status") or "").lower()
    print_id = job.get("print_id", f"JOB-{job_id}")
    student_user_id = job.get("user_id")

    if current_status not in _PF_ALLOWED_STATUSES:
        return {
            "success": False,
            "message": f"Power failure refund not applicable for job in status '{job.get('status')}'.",
        }

    # 2. Fetch payment
    payment = get_payment_by_job(job_id)
    if not payment:
        return {"success": False, "message": "No payment record found for this job."}
    if (payment.get("status") or "").lower() != "success":
        return {"success": False, "message": "Payment is not confirmed. Cannot refund."}

    # 3. Duplicate refund check
    existing_refund_status = payment.get("refund_status")
    if existing_refund_status in (STATUS_REFUNDED, STATUS_PROCESSING, STATUS_PENDING):
        return {
            "success": False,
            "message": f"A refund already exists (status: {existing_refund_status}).",
        }

    # 4. Calculate full refund (0% penalty for power failure)
    paid_amount = float(payment.get("amount") or 0.0)
    if paid_amount <= 0:
        return {"success": False, "message": "Invalid payment amount."}

    penalty, refund_amount = calculate_refund(paid_amount, REASON_POWER_FAILURE)

    # 5. Atomically cancel/stop the job
    cancelled = atomic_cancel_job_for_refund(
        job_id,
        allowed_statuses=list(_PF_ALLOWED_STATUSES),
        new_status="Cancelled",
    )
    if not cancelled:
        return {
            "success": False,
            "message": "Could not update job status. It may have already changed.",
        }

    update_job_cancellation_info(
        job_id=job_id,
        reason=f"Power failure - full refund by admin #{admin_user_id}",
        cancelled_at=datetime.utcnow(),
    )

    # 6. Mark PENDING then call gateway
    payment_id = payment["id"]
    update_payment_refund_fields(
        payment_id=payment_id,
        refund_status=STATUS_PENDING,
        refund_reason=REASON_POWER_FAILURE,
        original_amount=paid_amount,
        penalty_amount=0.0,
        refund_amount=refund_amount,
        refund_initiated_at=datetime.utcnow(),
    )

    txn_id = payment.get("transaction_id", "")
    gw_result = _simulate_gateway_refund(txn_id, refund_amount, REASON_POWER_FAILURE)

    if gw_result["success"]:
        update_payment_refund_fields(
            payment_id=payment_id,
            refund_status=STATUS_REFUNDED,
            gateway_refund_id=gw_result["gateway_refund_id"],
            refund_processed_at=datetime.utcnow(),
        )
        update_payment_status(
            payment_id,
            "Refunded",
            notes=(
                f"Full refund Rs.{refund_amount:.2f} - Power failure. "
                f"Admin: #{admin_user_id}. GW: {gw_result['gateway_refund_id']}"
            ),
        )
        _log.info(
            "POWER_FAILURE REFUND job_id=%d admin=%d refund=%.2f gw=%s",
            job_id, admin_user_id, refund_amount, gw_result["gateway_refund_id"],
        )
        if student_user_id:
            _send_power_failure_notification(
                user_id=student_user_id,
                print_id=print_id,
                refund_amount=refund_amount,
            )
        return {
            "success":       True,
            "message":       f"Full refund of Rs.{refund_amount:.2f} initiated successfully.",
            "paid_amount":   paid_amount,
            "penalty":       0.0,
            "refund_amount": refund_amount,
            "refund_status": STATUS_REFUNDED,
        }
    else:
        update_payment_refund_fields(
            payment_id=payment_id,
            refund_status=STATUS_FAILED,
            refund_failure_reason=gw_result.get("failure_reason", "Gateway error"),
            refund_processed_at=datetime.utcnow(),
        )
        _log.error(
            "POWER_FAILURE REFUND GATEWAY FAILED job_id=%d reason=%s",
            job_id, gw_result.get("failure_reason"),
        )
        return {
            "success":       False,
            "message":       "Refund gateway failed. Please retry or process manually.",
            "refund_status": STATUS_FAILED,
        }


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_refund_info(job_id: int) -> Optional[Dict[str, Any]]:
    """Return refund info for a job, or None if no refund exists."""
    try:
        from smartdb.crud_refund import get_payment_by_job_with_refund
        payment = get_payment_by_job_with_refund(job_id)
        if payment and payment.get("refund_status"):
            return payment
    except Exception:
        pass
    return None


def get_student_refund_history(user_id: int) -> List[Dict[str, Any]]:
    """Return all refund records for a student."""
    try:
        from smartdb.crud_refund import get_refund_history_for_user
        return get_refund_history_for_user(user_id) or []
    except Exception:
        return []


def get_all_refunds_admin() -> List[Dict[str, Any]]:
    """Return all refund records (admin view)."""
    try:
        from smartdb.crud_refund import get_all_payments_with_refund_info
        return get_all_payments_with_refund_info() or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Notification helpers (use existing notification system)
# ---------------------------------------------------------------------------

def _send_cancellation_refund_notification(
    user_id: int,
    print_id: str,
    paid_amount: float,
    penalty: float,
    refund_amount: float,
) -> None:
    try:
        from smartdb.crud import create_notification
        create_notification(
            user_id=user_id,
            title="Print Cancellation & Refund",
            message=(
                f"Your print job #{print_id} was cancelled from the queue. "
                f"A 2% cancellation fee of Rs.{penalty:.2f} was deducted. "
                f"Rs.{refund_amount:.2f} has been initiated as your refund. "
                f"(Original amount: Rs.{paid_amount:.2f})"
            ),
            notification_type="warning",
        )
    except Exception as exc:
        _log.warning("Could not send cancellation notification: %s", exc)


def _send_power_failure_notification(
    user_id: int,
    print_id: str,
    refund_amount: float,
) -> None:
    try:
        from smartdb.crud import create_notification
        create_notification(
            user_id=user_id,
            title="Full Refund Issued - Power Failure",
            message=(
                f"Your print job #{print_id} could not be completed due to a "
                f"printing-centre power failure. A full refund of Rs.{refund_amount:.2f} "
                f"has been initiated."
            ),
            notification_type="warning",
        )
    except Exception as exc:
        _log.warning("Could not send power failure notification: %s", exc)


def _send_ineligible_notification(
    user_id: int,
    print_id: str,
    reason: str,
) -> None:
    try:
        from smartdb.crud import create_notification
        create_notification(
            user_id=user_id,
            title="Cancellation Not Eligible for Refund",
            message=(
                f"Printing for job #{print_id} has already started. "
                f"This print job is not eligible for a refund."
            ),
            notification_type="error",
        )
    except Exception as exc:
        _log.warning("Could not send ineligible notification: %s", exc)


def _send_refund_failed_notification(
    user_id: int,
    print_id: str,
) -> None:
    try:
        from smartdb.crud import create_notification
        create_notification(
            user_id=user_id,
            title="Refund Processing Failed",
            message=(
                f"We attempted to process your refund for job #{print_id} "
                f"but the payment gateway returned an error. "
                f"Please contact the printing centre - your job has been cancelled "
                f"and the refund will be processed manually."
            ),
            notification_type="error",
        )
    except Exception as exc:
        _log.warning("Could not send refund-failed notification: %s", exc)
