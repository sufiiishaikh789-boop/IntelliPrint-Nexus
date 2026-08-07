"""
IntelliPrint Nexus — Professional Print Receipt Generator (Enterprise Edition)
=========================================================================
Generates a styled PDF receipt using PyMuPDF (fitz).
Includes: Logo, Student info, Printer, Pages, Amount, Payment ID,
          Pickup ID, QR Code, Date/Time, Receipt Number.

Enterprise improvements:
- Receipt numbers use ``secrets.token_urlsafe`` (cryptographically secure)
  instead of ``random.choices`` (pseudo-random, not appropriate for IDs)
- Structured logger from smartcore.logger
- from __future__ import annotations
"""
from __future__ import annotations

import datetime
import os
import secrets
import string

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE: bool = True
except ImportError:
    FITZ_AVAILABLE = False

# ── Structured logger ─────────────────────────────────────────────────
try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("helpers")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.receipt")


def _random_receipt_no() -> str:
    """
    Generate a cryptographically unique receipt number like RCP-2026-XXXXXX.
    Uses ``secrets`` module for enterprise-grade ID generation.
    """
    # 6 URL-safe characters (base64, no padding) → enough entropy for uniqueness
    raw    = secrets.token_urlsafe(6)[:6].upper()
    # Replace any non-alphanumeric chars that may appear in base64
    safe   = "".join(c if c.isalnum() else "X" for c in raw)
    year   = datetime.datetime.utcnow().year
    return f"RCP-{year}-{safe}"


def generate_receipt(
    output_dir: str,
    student_name: str,
    student_id: str,
    document_name: str,
    printer_name: str,
    pages: int,
    copies: int,
    color_mode: str,
    duplex: bool,
    paper_size: str,
    priority: str,
    amount: float,
    payment_id: str,
    pickup_id: str,
    qr_image_path: str,
    print_id: str,
    status: str = "Completed",
) -> str:
    """
    Generate a professional PDF receipt and return its path.
    Falls back to returning '' if PyMuPDF is unavailable.
    """
    os.makedirs(output_dir, exist_ok=True)
    receipt_no = _random_receipt_no()
    safe_pid = print_id.replace("/", "-").replace("\\", "-")
    out_path = os.path.join(output_dir, f"receipt_{safe_pid}.pdf")

    if not FITZ_AVAILABLE:
        return ""

    now = datetime.datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")

    # ── Colours ───────────────────────────────────────────────────────────────
    BG      = (0.047, 0.059, 0.078)      # Dark navy
    PANEL   = (0.075, 0.090, 0.118)      # Slightly lighter panel
    ACCENT  = (0.0,   0.851, 1.0)        # Cyan  #3B82F6
    GREEN   = (0.486, 1.0,   0.0)        # Lime  #8B5CF6
    WHITE   = (1.0,   1.0,   1.0)
    GRAY    = (0.5,   0.5,   0.5)
    DIMGRAY = (0.3,   0.3,   0.3)

    W, H = fitz.paper_size("a4")  # 595 × 842
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)

    def rect(x0, y0, x1, y1):
        return fitz.Rect(x0, y0, x1, y1)

    # ── Background ────────────────────────────────────────────────────────────
    page.draw_rect(rect(0, 0, W, H), color=None, fill=BG)

    # ── Header stripe ─────────────────────────────────────────────────────────
    page.draw_rect(rect(0, 0, W, 90), color=None, fill=PANEL)
    page.draw_line(fitz.Point(0, 90), fitz.Point(W, 90), color=ACCENT, width=2)

    # Logo text
    page.insert_text(fitz.Point(30, 40), "⚡ IntelliPrint Nexus", fontsize=18,
                     fontname="Helvetica-Bold", color=WHITE)
    page.insert_text(fitz.Point(30, 62), "Intelligent University Printing System",
                     fontsize=9, fontname="Helvetica", color=(0.6, 0.6, 0.6))

    # Receipt badge (right side)
    page.draw_rect(rect(W - 160, 15, W - 20, 70),
                   color=ACCENT, fill=None, width=1.5, radius=4)
    page.insert_text(fitz.Point(W - 148, 38), "PRINT RECEIPT", fontsize=8,
                     fontname="Helvetica-Bold", color=ACCENT)
    page.insert_text(fitz.Point(W - 148, 54), receipt_no, fontsize=7,
                     fontname="Helvetica", color=WHITE)

    # ── Pickup ID Banner ──────────────────────────────────────────────────────
    page.draw_rect(rect(20, 100, W - 20, 148),
                   color=None,
                   fill=(GREEN[0] * 0.08, GREEN[1] * 0.08, GREEN[2] * 0.08),
                   radius=8)
    page.draw_rect(rect(20, 100, W - 20, 148),
                   color=(GREEN[0] * 0.4, GREEN[1] * 0.4, GREEN[2] * 0.4),
                   fill=None, width=1, radius=8)
    page.insert_text(fitz.Point(35, 122), "PICKUP ID", fontsize=8,
                     fontname="Helvetica-Bold", color=GREEN)
    page.insert_text(fitz.Point(35, 140), pickup_id or "—", fontsize=16,
                     fontname="Helvetica-Bold", color=GREEN)

    # QR code (right of pickup banner)
    if qr_image_path and os.path.exists(qr_image_path):
        try:
            qr_rect = rect(W - 120, 100, W - 20, 200)
            page.insert_image(qr_rect, filename=qr_image_path)
        except Exception:
            pass

    # ── Section: Student Information ──────────────────────────────────────────
    y = 165
    _section_title(page, "Student Information", 20, y, W - 20, W, WHITE, ACCENT)
    y += 28
    rows_student = [
        ("Student Name", student_name),
        ("Student ID",   student_id),
        ("Receipt No.",  receipt_no),
        ("Date",         date_str),
        ("Time",         time_str),
    ]
    y = _info_rows(page, rows_student, 20, y, W - 20, WHITE, GRAY, PANEL)

    # ── Section: Print Job Details ────────────────────────────────────────────
    y += 10
    _section_title(page, "Print Job Details", 20, y, W - 20, W, WHITE, ACCENT)
    y += 28
    rows_job = [
        ("Document",      document_name[:45]),
        ("Print Job ID",  print_id),
        ("Printer",       printer_name),
        ("Pages",         str(pages)),
        ("Copies",        str(copies)),
        ("Color Mode",    color_mode),
        ("Duplex",        "Yes" if duplex else "No"),
        ("Paper Size",    paper_size),
        ("Priority",      priority),
    ]
    y = _info_rows(page, rows_job, 20, y, W - 20, WHITE, GRAY, PANEL)

    # ── Section: Payment Summary ──────────────────────────────────────────────
    y += 10
    _section_title(page, "Payment Summary", 20, y, W - 20, W, WHITE, ACCENT)
    y += 28
    rows_pay = [
        ("Payment ID",     payment_id or "—"),
        ("Payment Method", "Online"),
        ("Amount Paid",    f"Rs. {amount:.2f}"),
        ("Payment Status", "Successful"),
        ("Job Status",     status),
    ]
    y = _info_rows(page, rows_pay, 20, y, W - 20, WHITE, GRAY, PANEL)

    # ── Total amount box ──────────────────────────────────────────────────────
    y += 8
    page.draw_rect(rect(20, y, W - 20, y + 44),
                   color=None,
                   fill=(0.0, 0.851 * 0.1, 1.0 * 0.1),
                   radius=6)
    page.draw_rect(rect(20, y, W - 20, y + 44),
                   color=ACCENT, fill=None, width=1, radius=6)
    page.insert_text(fitz.Point(32, y + 16), "TOTAL PAID", fontsize=8,
                     fontname="Helvetica-Bold", color=ACCENT)
    page.insert_text(fitz.Point(32, y + 34), f"Rs. {amount:.2f}",
                     fontsize=16, fontname="Helvetica-Bold", color=WHITE)

    # ── Footer ────────────────────────────────────────────────────────────────
    y = H - 50
    page.draw_line(fitz.Point(20, y), fitz.Point(W - 20, y),
                   color=(0.15, 0.15, 0.15), width=1)
    page.insert_text(fitz.Point(20, y + 18),
                     "Thank you for using IntelliPrint Nexus! Please collect your documents at the counter.",
                     fontsize=7.5, fontname="Helvetica", color=GRAY)
    page.insert_text(fitz.Point(20, y + 32),
                     "IntelliPrint Nexus • University Print Management System • support@smartprint.edu",
                     fontsize=7, fontname="Helvetica", color=DIMGRAY)

    doc.save(out_path)
    doc.close()
    return out_path


def _section_title(page, title: str, x0, y, x1, W, white, accent):
    """Draw a section header bar."""
    page.draw_rect(fitz.Rect(x0, y, x1, y + 22),
                   color=None, fill=(0.1, 0.1, 0.15), radius=4)
    page.draw_line(fitz.Point(x0, y + 22), fitz.Point(x0 + 60, y + 22),
                   color=accent, width=1.5)
    page.insert_text(fitz.Point(x0 + 8, y + 15), title.upper(),
                     fontsize=8, fontname="Helvetica-Bold", color=accent)


def _info_rows(page, rows, x0, y, x1, white, gray, panel) -> int:
    """Draw alternating info rows and return the new y position."""
    mid = (x0 + x1) // 2
    for i, (label, value) in enumerate(rows):
        bg = panel if i % 2 == 0 else (0.06, 0.07, 0.09)
        page.draw_rect(fitz.Rect(x0, y, x1, y + 22),
                       color=None, fill=bg)
        page.insert_text(fitz.Point(x0 + 8, y + 15), str(label),
                         fontsize=8.5, fontname="Helvetica", color=gray)
        page.insert_text(fitz.Point(mid, y + 15), str(value),
                         fontsize=8.5, fontname="Helvetica-Bold", color=white)
        y += 22
    return y
