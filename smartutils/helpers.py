"""
SmartPrint AI - Helper Utilities
Shared helper functions: ID generation, QR codes, formatting, cost calculation.
"""

import os
import random
import string
from datetime import datetime
from typing import Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_H


# ---------------------------------------------------------------------------
# Print-ID generation
# ---------------------------------------------------------------------------

def generate_print_id() -> str:
    """Generate a unique print ID in the format SP2026-XXXX (4 random uppercase alphanumerics)."""
    year = datetime.utcnow().strftime("%Y")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SP{year}-{suffix}"


# ---------------------------------------------------------------------------
# QR code generation
# ---------------------------------------------------------------------------

def generate_qr_code(data: str, path: str) -> str:
    """
    Generate a QR code image and save it to *path*.

    Parameters
    ----------
    data : str
        The string payload to encode.
    path : str
        Destination file path (PNG).

    Returns
    -------
    str
        The absolute path to the saved QR image.
    """
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#00D9FF", back_color="white")
    img.save(path)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Currency formatting
# ---------------------------------------------------------------------------

def format_currency(amount: float) -> str:
    """Format a numeric amount as Indian Rupees (₹)."""
    if amount >= 1_00_000:
        return f"₹{amount:,.2f}"
    return f"₹{amount:.2f}"


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------

def calculate_cost(
    pages: int,
    copies: int = 1,
    color_mode: str = "BW",
    priority: str = "Normal",
    duplex: bool = False,
) -> dict:
    """
    Calculate the total printing cost.

    Returns a dict with `cost_per_page` and `total_cost`.
    """
    base_rate = 2.0 if color_mode == "BW" else 5.0

    # Priority surcharge
    priority_multipliers = {"Normal": 1.0, "High": 1.5, "Urgent": 2.0}
    multiplier = priority_multipliers.get(priority, 1.0)

    cost_per_page = base_rate * multiplier

    # Duplex discount (10 %)
    if duplex:
        cost_per_page *= 0.9

    total_cost = cost_per_page * pages * copies

    return {
        "cost_per_page": round(cost_per_page, 2),
        "total_cost": round(total_cost, 2),
    }


# ---------------------------------------------------------------------------
# Date / time formatting
# ---------------------------------------------------------------------------

def format_datetime(dt: Optional[datetime]) -> str:
    """Return a human-friendly date-time string, or '—' for None."""
    if dt is None:
        return "—"
    return dt.strftime("%d %b %Y, %I:%M %p")


# ---------------------------------------------------------------------------
# Status colours & emojis
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "Pending": "#F59E0B",
    "Queued": "#3B82F6",
    "Printing": "#8B5CF6",
    "Completed": "#10B981",
    "Ready": "#06B6D4",
    "Collected": "#6B7280",
    "Online": "#10B981",
    "Offline": "#EF4444",
    "Maintenance": "#F59E0B",
    "Success": "#10B981",
    "Failed": "#EF4444",
    "Active": "#10B981",
    "Suspended": "#EF4444",
}

_STATUS_EMOJIS = {
    "Pending": "⏳",
    "Queued": "📋",
    "Printing": "🖨️",
    "Completed": "✅",
    "Ready": "📦",
    "Collected": "🤝",
    "Online": "🟢",
    "Offline": "🔴",
    "Maintenance": "🔧",
    "Success": "✅",
    "Failed": "❌",
    "Active": "🟢",
    "Suspended": "🔴",
}


def get_status_color(status: str) -> str:
    """Return a hex colour string for the given status label."""
    return _STATUS_COLORS.get(status, "#9CA3AF")


def get_status_emoji(status: str) -> str:
    """Return an emoji for the given status label."""
    return _STATUS_EMOJIS.get(status, "⬜")


def write_log(log_name: str, message: str, exception: Optional[Exception] = None) -> None:
    """Write a timestamped log entry to uploads/LOG_NAME.log AND logs/smartprint.log.

    This function is guaranteed to never raise an exception — logging must
    never interrupt normal application flow.
    """
    try:
        import traceback

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        entry_lines = [f"[{timestamp}] [{log_name}] {message}\n"]
        if exception:
            entry_lines.append(f"  EXCEPTION: {type(exception).__name__}: {exception}\n")
            tb = traceback.format_exc()
            for tb_line in tb.splitlines():
                entry_lines.append(f"  {tb_line}\n")
            entry_lines.append("\n")
        entry = "".join(entry_lines)

        # ── Per-module log (legacy) ──────────────────────────────────────────
        legacy_dir = "uploads"
        os.makedirs(legacy_dir, exist_ok=True)
        legacy_path = os.path.join(legacy_dir, f"{log_name.upper()}.log")
        try:
            with open(legacy_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

        # ── Unified log ─────────────────────────────────────────────────────
        unified_dir = "logs"
        os.makedirs(unified_dir, exist_ok=True)
        unified_path = os.path.join(unified_dir, "smartprint.log")
        try:
            with open(unified_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

        # ── Console — UTF-8 safe, never raises UnicodeEncodeError ───────────
        # On Windows the default console encoding (cp1252) cannot represent
        # characters such as ₹, ✓, 🎉, etc.  We encode to UTF-8 and write
        # directly to the underlying binary buffer when available; otherwise
        # we fall back to replacing unencodable characters so that a
        # UnicodeEncodeError is never propagated to the caller.
        try:
            import sys
            line = entry.rstrip()
            stdout = sys.stdout
            # Prefer the raw binary buffer so we control the encoding
            if hasattr(stdout, "buffer"):
                stdout.buffer.write((line + "\n").encode("utf-8", errors="replace"))
                stdout.buffer.flush()
            else:
                # Fallback: encode to the console's encoding, replacing
                # any character that cannot be represented.
                safe_line = line.encode(
                    stdout.encoding or "utf-8", errors="replace"
                ).decode(stdout.encoding or "utf-8", errors="replace")
                print(safe_line)
        except Exception:
            # Last-resort: silently swallow any console error so that the
            # logger itself can never crash the application.
            pass

    except Exception:
        # Outermost guard — write_log must NEVER propagate an exception.
        pass


