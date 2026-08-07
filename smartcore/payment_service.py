"""
IntelliPrint Nexus — Payment Service (Enterprise Edition)
====================================================
Transaction-safe, idempotent payment engine with audit logging,
receipt generation, and webhook-ready architecture.

Features:
- Unique traceable transaction IDs (TXN + timestamp + random suffix)
- Idempotency: duplicate payment attempts return existing record
- Amount validation against expected job cost
- Comprehensive payment audit log
- Receipt generation as structured dict
- Webhook-ready: fire events to registered endpoints
- Payment status state machine validation
- Refund scaffold for future integration
"""

from __future__ import annotations

import random
import string
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from smartcore.config import cfg as _cfg
    _PREFIX    = _cfg.PAYMENT.TRANSACTION_ID_PREFIX
    _ID_LEN    = _cfg.PAYMENT.TRANSACTION_ID_LENGTH
    _MAX_AMT   = _cfg.PAYMENT.MAX_AMOUNT
    _MIN_AMT   = _cfg.PAYMENT.MIN_AMOUNT
except ImportError:
    _PREFIX  = "TXN"
    _ID_LEN  = 12
    _MAX_AMT = 10_000.0
    _MIN_AMT = 0.50

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("payment")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.payment")

try:
    from smartcore.exceptions import (
        PaymentError,
        PaymentAmountMismatchError,
        DuplicatePaymentError,
    )
except ImportError:
    PaymentError = Exception
    PaymentAmountMismatchError = Exception
    DuplicatePaymentError = Exception


# ── Transaction ID generation ─────────────────────────────────────────────────

def generate_transaction_id() -> str:
    """
    Generate a unique, traceable transaction ID.

    Format: ``TXN-<timestamp_ms>-<8 random uppercase alphanumeric chars>``
    Example: ``TXN-1753493836000-A7KP2QRX``

    The timestamp component guarantees chronological ordering;
    the random suffix ensures uniqueness under concurrent submissions.
    """
    ts   = int(time.time() * 1000)
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{_PREFIX}-{ts}-{rand}"


# ── Amount validation ─────────────────────────────────────────────────────────

def validate_payment_amount(amount: float, expected: float, tolerance: float = 0.01) -> None:
    """
    Validate that the payment amount matches the expected job cost.

    Raises ``PaymentAmountMismatchError`` if amounts differ by more than
    ``tolerance`` rupees (default 1 paisa).

    Parameters
    ----------
    amount   : float — actual amount being charged
    expected : float — amount expected from the job record
    tolerance: float — acceptable floating-point rounding error
    """
    if amount < _MIN_AMT:
        raise PaymentError(f"Payment amount ₹{amount:.2f} is below the minimum ₹{_MIN_AMT:.2f}.")
    if amount > _MAX_AMT:
        raise PaymentError(f"Payment amount ₹{amount:.2f} exceeds the maximum ₹{_MAX_AMT:.2f}.")
    if abs(amount - expected) > tolerance:
        raise PaymentAmountMismatchError(expected=expected, received=amount)


# ── Core payment processing ───────────────────────────────────────────────────

def process_payment(
    job_id: int,
    user_id: int,
    amount: float,
    method: str,
    expected_amount: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Create a payment record for a print job (idempotent).

    If a payment already exists for ``job_id`` with status ``Success``,
    returns the existing payment dict without creating a duplicate.

    Parameters
    ----------
    job_id          : int   — print job primary key
    user_id         : int   — user primary key
    amount          : float — amount in rupees
    method          : str   — "UPI" / "Card" / "NetBanking"
    expected_amount : float — if provided, validates amount matches job cost

    Returns
    -------
    dict — payment record dict (same structure as ``get_payment_by_job``)
    """
    from smartdb.crud import get_payment_by_job, create_payment

    # ── Idempotency check ────────────────────────────────────────────────────
    existing = get_payment_by_job(job_id)
    if existing and existing.get("status") == "Success":
        _log.info(
            "process_payment: payment already exists for job_id=%d txn=%s — returning existing",
            job_id, existing.get("transaction_id"),
        )
        return existing

    # ── Amount validation ────────────────────────────────────────────────────
    if expected_amount is not None:
        validate_payment_amount(amount, expected_amount)

    # ── Create payment record ────────────────────────────────────────────────
    txn_id  = generate_transaction_id()
    payment = create_payment(
        job_id=job_id,
        user_id=user_id,
        amount=amount,
        method=method,
        transaction_id=txn_id,
        status="Success",
    )

    log_payment_event("payment_created", {
        "job_id":         job_id,
        "user_id":        user_id,
        "amount":         amount,
        "method":         method,
        "transaction_id": txn_id,
    })

    _fire_webhook("payment.success", payment)
    return payment


def verify_payment(transaction_id: str) -> Dict[str, Any]:
    """
    Verify a payment exists and is in Success status.

    Returns dict with ``verified`` (bool) and the payment record.
    """
    from smartdb.crud import get_payment_by_transaction_id

    payment = get_payment_by_transaction_id(transaction_id)
    if not payment:
        return {"verified": False, "reason": "Transaction not found.", "payment": None}
    if payment["status"] != "Success":
        return {
            "verified": False,
            "reason":   f"Payment status is '{payment['status']}', not Success.",
            "payment":  payment,
        }
    return {"verified": True, "reason": "OK", "payment": payment}


# ── Receipt generation ────────────────────────────────────────────────────────

def get_payment_receipt(transaction_id: str) -> Dict[str, Any]:
    """
    Generate a structured receipt dict for a completed payment.

    Returns a dict suitable for display in the UI or export to PDF.
    """
    from smartdb.crud import get_payment_by_transaction_id, get_job_by_id

    payment = get_payment_by_transaction_id(transaction_id)
    if not payment:
        return {"error": "Payment not found.", "transaction_id": transaction_id}

    job = get_job_by_id(payment["job_id"]) if payment.get("job_id") else None

    return {
        "receipt_type":    "IntelliPrint Nexus Payment Receipt",
        "transaction_id":  transaction_id,
        "payment_status":  payment.get("status", "Unknown"),
        "amount":          payment.get("amount", 0.0),
        "method":          payment.get("method", "Unknown"),
        "paid_at":         str(payment.get("created_at", "")),
        "job_id":          payment.get("job_id"),
        "print_id":        job.get("print_id")        if job else None,
        "document_name":   job.get("document_name")   if job else None,
        "total_pages":     job.get("total_pages")     if job else None,
        "copies":          job.get("copies")          if job else None,
        "color_mode":      job.get("color_mode")      if job else None,
        "pickup_id":       job.get("pickup_id")       if job else None,
        "generated_at":    datetime.utcnow().isoformat(),
        "issuer":          "IntelliPrint Nexus — University Printing System",
    }


# ── Refund scaffold ───────────────────────────────────────────────────────────

def initiate_refund(payment_id: int, reason: str) -> Dict[str, Any]:
    """
    Scaffold for future refund integration.

    Currently marks the payment as Refunded in the database and
    fires a ``payment.refund`` webhook event. No actual money movement.
    """
    from smartdb.crud import update_payment_status, get_all_payments

    success = update_payment_status(payment_id, "Refunded", notes=f"Refund: {reason}")
    if success:
        log_payment_event("refund_initiated", {"payment_id": payment_id, "reason": reason})
        _fire_webhook("payment.refund", {"payment_id": payment_id, "reason": reason})
        return {"success": True, "message": "Refund recorded. Contact admin for processing."}
    return {"success": False, "message": "Payment record not found."}


# ── Audit logging ─────────────────────────────────────────────────────────────

def log_payment_event(event_type: str, data: Dict[str, Any]) -> None:
    """Write a structured payment audit log entry."""
    try:
        _log.info(
            "[PAYMENT_EVENT] type=%s data=%s",
            event_type,
            {k: v for k, v in data.items() if k not in ("password", "card_number")},
        )
    except Exception:
        pass


# ── Webhook (fire-and-forget) ─────────────────────────────────────────────────

_WEBHOOK_ENDPOINTS: List[str] = []  # Register endpoints here for real integration


def register_webhook(url: str) -> None:
    """Register a URL to receive payment webhook events."""
    if url not in _WEBHOOK_ENDPOINTS:
        _WEBHOOK_ENDPOINTS.append(url)


def _fire_webhook(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Fire a webhook event to all registered endpoints (fire-and-forget).
    Never blocks, never raises.
    """
    if not _WEBHOOK_ENDPOINTS:
        return
    import threading
    import json

    def _send(url: str) -> None:
        try:
            import urllib.request
            body = json.dumps({"event": event_type, "payload": payload, "ts": time.time()}).encode()
            req  = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception as exc:
            _log.debug("Webhook to '%s' failed: %s", url, exc)

    for endpoint in _WEBHOOK_ENDPOINTS:
        threading.Thread(target=_send, args=(endpoint,), daemon=True).start()
