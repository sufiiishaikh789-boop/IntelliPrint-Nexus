"""
IntelliPrint Nexus — Helper Utilities (Enterprise Edition)
=====================================================
Shared helper functions: ID generation, QR codes, formatting, cost calculation.

Enterprise improvements:
- from __future__ import annotations
- Structured logger from smartcore.logger
- Removed duplicate generate_pickup_id() body (now delegates to generate_print_id)
"""
from __future__ import annotations

import os
import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_H

# ── Structured logger ─────────────────────────────────────────────────
try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("helpers")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.helpers")


# ---------------------------------------------------------------------------
# Print-ID generation
# ---------------------------------------------------------------------------

def generate_print_id() -> str:
    """Generate a unique print ID in the format SP{YEAR}-XXXX (4 random uppercase alphanumerics)."""
    year   = datetime.utcnow().strftime("%Y")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    pid    = f"SP{year}-{suffix}"
    _log.debug("generate_print_id: %s", pid)
    return pid


def generate_pickup_id() -> str:
    """
    Generate a unique Pickup ID in the same format as generate_print_id.
    Delegates to generate_print_id() — same algorithm, same format.
    Kept as a separate named function for semantic clarity at call sites.
    """
    return generate_print_id()


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

    img = qr.make_image(fill_color="#3B82F6", back_color="white")
    img.save(path)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# PDF Preview generation (post-payment only)
# ---------------------------------------------------------------------------

def generate_pdf_preview(
    source_pdf_path: str,
    pickup_id: str,
    qr_image_path: str,
    printer_name: str,
    print_id: str,
    output_dir: str = "uploads/previews",
    student_name: str = "Student",
    student_id: str = "—",
    document_name: str = "Document",
    num_pages: int = 0,
) -> str:
    """
    Create a professional print-ready PDF.

    Copies ALL original pages verbatim, then appends ONE additional A4
    separator/pickup-sheet as the FINAL page.  The separator contains:
      • IntelliPrint Nexus logo text
      • Pickup ID (large, prominent)
      • QR Code encoding the Pickup ID
      • Student ID, Student Name, Document Name
      • Printer Name, Print Job ID, Number of Pages
      • Date & Time stamp
      • "Ready for Pickup" label

    The ORIGINAL uploaded PDF is NEVER modified.
    Returns the absolute path to the generated print-ready PDF.
    Falls back to returning the source path if PyMuPDF is unavailable.
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_id = pickup_id.replace("/", "-").replace("\\", "-")
    out_path = os.path.join(output_dir, f"printready_{safe_id}.pdf")

    try:
        import fitz  # PyMuPDF

        src = fitz.open(source_pdf_path)
        total_pages = num_pages or src.page_count
        out_doc = fitz.open()

        # ── 1. Copy ALL original pages verbatim ───────────────────────────
        out_doc.insert_pdf(src)
        src.close()

        # ── 2. Append professional separator/pickup sheet ─────────────────
        # A4 page: 595 × 842 points (72 pt = 1 inch)
        W, H = 595.0, 842.0
        page = out_doc.new_page(width=W, height=H)
        cx = W / 2  # horizontal centre

        # ── Background: dark slate fills entire page ──────────────────────
        page.draw_rect(
            fitz.Rect(0, 0, W, H),
            color=(0.05, 0.07, 0.12),
            fill=(0.05, 0.07, 0.12),
        )

        # ── Top accent stripe ─────────────────────────────────────────────
        page.draw_rect(
            fitz.Rect(0, 0, W, 6),
            color=(0.0, 0.85, 1.0),
            fill=(0.0, 0.85, 1.0),
        )
        page.draw_rect(
            fitz.Rect(0, 6, W, 10),
            color=(0.48, 1.0, 0.0),
            fill=(0.48, 1.0, 0.0),
        )

        # ── IntelliPrint Nexus Logo / Header ───────────────────────────────────
        page.insert_text(
            (cx - 90, 42),
            "SmartPrint",
            fontsize=24,
            color=(0.0, 0.85, 1.0),
            fontname="helv",
        )
        page.insert_text(
            (cx + 54, 42),
            " AI",
            fontsize=24,
            color=(0.48, 1.0, 0.0),
            fontname="helv",
        )
        page.insert_text(
            (cx - 90, 58),
            "Intelligent Print Management System",
            fontsize=8,
            color=(0.6, 0.6, 0.7),
            fontname="helv",
        )

        # ── Thin divider ──────────────────────────────────────────────────
        page.draw_line(
            fitz.Point(40, 68), fitz.Point(W - 40, 68),
            color=(0.2, 0.25, 0.35),
            width=0.8,
        )

        # ── "PICKUP SEPARATOR SHEET" subtitle ─────────────────────────────
        page.insert_text(
            (cx - 70, 85),
            "PICKUP IDENTIFICATION SHEET",
            fontsize=9,
            color=(0.5, 0.55, 0.65),
            fontname="helv",
        )

        # ── QR Code (centred) ─────────────────────────────────────────────
        qr_size = 150
        qr_top  = 98
        qr_rect = fitz.Rect(cx - qr_size / 2, qr_top, cx + qr_size / 2, qr_top + qr_size)
        if os.path.exists(qr_image_path):
            page.insert_image(qr_rect, filename=qr_image_path)
        else:
            # Placeholder box if QR missing
            page.draw_rect(qr_rect, color=(0.3, 0.3, 0.4), fill=(0.1, 0.12, 0.18))
            page.insert_text((cx - 20, qr_top + 80), "QR N/A", fontsize=9, color=(0.5, 0.5, 0.6))

        # ── Scan hint under QR ────────────────────────────────────────────
        page.insert_text(
            (cx - 65, qr_top + qr_size + 14),
            "Scan to verify pickup or show Pickup ID at counter",
            fontsize=7.5,
            color=(0.5, 0.55, 0.65),
        )

        # ── Pickup ID — large prominent display ───────────────────────────
        pid_y = qr_top + qr_size + 40
        # Label
        page.insert_text(
            (cx - 28, pid_y),
            "PICKUP  ID",
            fontsize=8,
            color=(0.5, 0.55, 0.65),
        )
        # Large ID value
        page.insert_text(
            (cx - 68, pid_y + 22),
            pickup_id,
            fontsize=28,
            color=(0.48, 1.0, 0.0),
            fontname="helv",
        )

        # ── "READY FOR PICKUP" badge ──────────────────────────────────────
        badge_y = pid_y + 40
        badge_rect = fitz.Rect(cx - 90, badge_y, cx + 90, badge_y + 22)
        page.draw_rect(badge_rect, color=(0.0, 0.85, 1.0), fill=(0.0, 0.85, 1.0), radius=4)
        page.insert_text(
            (cx - 58, badge_y + 15),
            "✓  READY FOR PICKUP",
            fontsize=10,
            color=(0.05, 0.07, 0.12),
            fontname="helv",
        )

        # ── Divider ───────────────────────────────────────────────────────
        info_top = badge_y + 36
        page.draw_line(
            fitz.Point(40, info_top), fitz.Point(W - 40, info_top),
            color=(0.2, 0.25, 0.35),
            width=0.6,
        )

        # ── Details Grid (two columns) ────────────────────────────────────
        def _field(lx, y, label, value, label_col=(0.45, 0.5, 0.6), val_col=(0.9, 0.92, 1.0)):
            """Draw label + value pair."""
            page.insert_text((lx, y), label, fontsize=7, color=label_col)
            page.insert_text((lx, y + 11), str(value)[:38], fontsize=8.5, color=val_col, fontname="helv")

        col1_x = 50
        col2_x = W / 2 + 10
        row_h  = 28  # vertical spacing between rows
        gy     = info_top + 18

        now_str = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")

        # Row 1
        _field(col1_x, gy,          "STUDENT NAME",    student_name)
        _field(col2_x, gy,          "STUDENT ID",      f"#{student_id}")
        # Row 2
        _field(col1_x, gy + row_h,  "DOCUMENT NAME",   document_name[:38])
        _field(col2_x, gy + row_h,  "TOTAL PAGES",     str(total_pages))
        # Row 3
        _field(col1_x, gy + 2*row_h, "PRINTER",        printer_name)
        _field(col2_x, gy + 2*row_h, "PRINT JOB ID",   print_id)
        # Row 4
        _field(col1_x, gy + 3*row_h, "DATE & TIME",    now_str)
        _field(col2_x, gy + 3*row_h, "PICKUP ID",      pickup_id, val_col=(0.48, 1.0, 0.0))

        # ── Bottom separator line ─────────────────────────────────────────
        bot_line_y = gy + 4 * row_h + 10
        page.draw_line(
            fitz.Point(40, bot_line_y), fitz.Point(W - 40, bot_line_y),
            color=(0.2, 0.25, 0.35),
            width=0.6,
        )

        # ── Footer note ───────────────────────────────────────────────────
        page.insert_text(
            (40, bot_line_y + 14),
            "This separator sheet is for the shopkeeper. "
            "The document above this page is the actual printout.",
            fontsize=6.5,
            color=(0.4, 0.45, 0.55),
        )
        page.insert_text(
            (40, bot_line_y + 24),
            "IntelliPrint Nexus — Secure • Fast • Reliable   |   "
            "github.com/smartprint-ai",
            fontsize=6,
            color=(0.3, 0.35, 0.45),
        )

        # ── Bottom accent stripe ──────────────────────────────────────────
        page.draw_rect(
            fitz.Rect(0, H - 10, W, H - 6),
            color=(0.48, 1.0, 0.0),
            fill=(0.48, 1.0, 0.0),
        )
        page.draw_rect(
            fitz.Rect(0, H - 6, W, H),
            color=(0.0, 0.85, 1.0),
            fill=(0.0, 0.85, 1.0),
        )

        # ── Save ─────────────────────────────────────────────────────────
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()

        return os.path.abspath(out_path)

    except Exception:
        # If PyMuPDF fails, return source path as fallback
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass
        return os.path.abspath(source_pdf_path)


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
        "total_cost":    round(total_cost, 2),
    }


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
    """
    Write a timestamped log entry.

    Delegates to smartcore.logger (enterprise rotating logger) when available.
    Falls back to direct file writes if smartcore is not yet importable.
    Guaranteed to never raise.
    """
    try:
        # ── Prefer enterprise logger ──────────────────────────────────────────
        from smartcore.logger import write_log as _enterprise_write_log
        _enterprise_write_log(log_name, message, exception)
        return
    except ImportError:
        pass
    except Exception:
        pass

    # ── Direct file fallback (used only before smartcore is bootstrapped) ────
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


