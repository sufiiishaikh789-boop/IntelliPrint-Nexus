"""
IntelliPrint Nexus - Queue Tracking (Live Enterprise Tracker)
Shows real-time print job progress with:
  - 14-stage status pipeline
  - Live % progress with current page
  - PPM-based ETA calculation
  - Queue position
  - Cancellation (only when status allows)
  - Job timeline
"""

import streamlit as st
import re
import time
from datetime import datetime

from smartdb.crud import (
    get_user_jobs, get_live_progress, get_job_timeline,
    cancel_job_safe, get_queue_position, get_all_printers,
    assign_printer_and_queue, get_payment_by_job,
)

# ── Status configuration ──────────────────────────────────────────────────────
_STAGES = [
    ("Pending",          "⏳", "#f59e0b"),
    ("Payment Pending",  "💳", "#f97316"),
    ("Payment Successful","💰", "#10b981"),
    ("Queue Assigned",   "📋", "#3b82f6"),
    ("Waiting",          "🕐", "#eab308"),
    ("Preparing",        "🔥", "#f97316"),
    ("Printing",         "🖨️", "#3B82F6"),
    ("Completed",        "✅", "#10b981"),
    ("Ready",            "📦", "#8B5CF6"),
    ("Collected",        "🏃", "#6b7280"),
]

_STATUS_COLORS = {
    "pending":           "#f59e0b",
    "payment_pending":   "#f97316",
    "payment successful":"#10b981",
    "queued":            "#3b82f6",
    "queue assigned":    "#3b82f6",
    "waiting":           "#eab308",
    "preparing":         "#f97316",
    "printing":          "#3B82F6",
    "completed":         "#10b981",
    "ready":             "#8B5CF6",
    "collected":         "#6b7280",
    "cancelled":         "#ef4444",
    "failed":            "#ef4444",
    "archived":          "#4b5563",
}

CANCELLABLE_STATUSES = {
    "pending", "payment_pending", "queued", "waiting",
    "uploaded", "ai analysis", "queue assigned",
}


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


def _stage_index(status: str) -> int:
    s = status.lower().strip()
    mapping = {
        "pending": 0, "payment_pending": 1, "payment successful": 2,
        "queued": 3, "queue assigned": 3, "waiting": 4,
        "preparing": 5, "printing": 6,
        "completed": 7, "ready": 8, "collected": 9,
        "cancelled": 9, "failed": 9,
    }
    return mapping.get(s, 0)


def show_queue_tracking():
    """Render the live queue tracking page."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_clean_html(_queue_css()))

    # ── Header ────────────────────────────────────────────────────────────────
    st.html(_clean_html("""
        <div class="queue-header">
            <div class="queue-icon">📋</div>
            <div class="queue-title">Live Queue Tracker</div>
            <div class="queue-subtitle">Real-time progress monitoring for your print jobs</div>
        </div>
        """))

    # ── Fetch all jobs for this student ────────────────────────────────────────
    all_jobs = get_user_jobs(user_id) or []

    # ── Step 1: Auto-recover "Pending" jobs that already have payment "Success" ─
    #
    # Root cause: payment.py used to call create_payment("Success") FIRST,
    # then generate QR/PDF (which could fail), then call assign_printer_and_queue().
    # If QR/PDF failed, the job was permanently orphaned: payment=Success,
    # status=Pending, no printer assigned, queue manager never dispatched it.
    #
    # Fix: detect these orphaned jobs and re-queue them now.
    for job in all_jobs:
        if job.get("status", "").lower() == "pending":
            try:
                pay = get_payment_by_job(job["id"])
                if pay and pay.get("status") == "Success":
                    # This job has a successful payment but was never queued.
                    # Re-run assign_printer_and_queue() to fix it now.
                    assign_printer_and_queue(
                        job_id   = job["id"],
                        pages    = job.get("total_pages", 1) or 1,
                        copies   = job.get("copies", 1) or 1,
                        priority = job.get("priority", "Normal") or "Normal",
                    )
            except Exception:
                pass  # Never crash the tracker due to recovery attempt

    # ── Step 2: Re-fetch (recovery may have changed statuses) ─────────────────
    all_jobs = get_user_jobs(user_id) or []

    # ── Step 3: Filter what to display ───────────────────────────────────────
    #
    # Show:
    #   - All in-progress statuses (pending → printing)
    #   - "Ready" and "Completed" (job is done but awaiting pickup)
    #
    # Exclude:
    #   - "Pending" jobs with NO successful payment (pre-payment placeholders
    #     that were never paid — they clutter the tracker)
    #   - "Collected", "Cancelled", "Failed", "Archived" (terminal states)
    #
    displayable_active = {
        "payment_pending", "payment successful",
        "queued", "queue assigned", "waiting",
        "preparing", "printing",
        "completed", "ready",
    }

    def _should_show(j: dict) -> bool:
        status = j.get("status", "").lower()
        if status in displayable_active:
            return True
        if status == "pending":
            # Only show "Pending" if the student has already paid for it
            try:
                pay = get_payment_by_job(j["id"])
                return pay is not None and pay.get("status") == "Success"
            except Exception:
                return False
        return False

    active_jobs = [j for j in all_jobs if _should_show(j)]

    if not active_jobs:
        st.html(_clean_html("""
            <div class="empty-state">
                <div style="font-size:3rem;margin-bottom:12px;">🎉</div>
                <div style="font-size:1.1rem;font-weight:700;color:#fff;">No Active Print Jobs</div>
                <div style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin-top:6px;max-width:400px;margin:8px auto 0;">
                    Your queues are clear. Upload a document to submit a new print request.
                </div>
            </div>
            """))
        col_l, col_c, col_r = st.columns([1, 1.5, 1])
        with col_c:
            if st.button("📤 Upload Document", key="queue_upload_btn", use_container_width=True):
                st.session_state["current_page"] = "Submit Print Job"
                st.rerun()
        return

    # ── Printer map ───────────────────────────────────────────────────────────
    printers = {p["id"]: p for p in (get_all_printers() or [])}

    for idx, job in enumerate(active_jobs):
        _render_live_job_card(job, idx, printers)

    # ── Auto-refresh hint ──────────────────────────────────────────────────────
    st.html("""
    <div style="text-align:center;color:rgba(255,255,255,.3);font-size:.78rem;margin-top:16px;">
        💡 This page auto-refreshes. Press <b>R</b> or click the ↺ button to update manually.
    </div>
    """)

    # Auto-refresh every 5 s while printing; every 15 s while queued/waiting
    printing_now = any(
        j.get("status", "").lower() in ("printing", "preparing")
        for j in active_jobs
    )
    queued_now = any(
        j.get("status", "").lower() in ("queued", "queue assigned", "waiting", "pending")
        for j in active_jobs
    )
    if printing_now:
        time.sleep(5)
        st.rerun()
    elif queued_now:
        time.sleep(8)
        st.rerun()


def _render_live_job_card(job: dict, idx: int, printers: dict):
    """Render a single live job card with full progress metrics."""
    from datetime import datetime as _dt, timedelta

    job_id     = job.get("id")
    print_id   = job.get("print_id", "N/A")
    doc_name   = job.get("document_name", "Document")
    status     = job.get("status", "Pending")
    status_lower = status.lower()
    pages      = job.get("total_pages", 1) or 1
    copies     = job.get("copies", 1) or 1
    created    = str(job.get("submitted_at", ""))[:16]
    priority   = job.get("priority", "Normal")
    printer_id = job.get("printer_id")
    pickup_id  = job.get("pickup_id", "")
    ewt        = job.get("estimated_wait_time")     # minutes from DB

    printer_name = (
        printers.get(printer_id, {}).get("name", "Assigning…")
        if printer_id else "Assigning…"
    )
    status_color = _STATUS_COLORS.get(status_lower, "#6b7280")
    stage_idx    = _stage_index(status)

    # ── Live progress data ────────────────────────────────────────────────────
    progress = {}
    if job_id:
        try:
            progress = get_live_progress(job_id) or {}
        except Exception:
            progress = {}

    progress_pct = progress.get("progress_pct", 0)
    current_page = progress.get("current_page", 0)
    total_p      = progress.get("total_pages", pages * copies)
    elapsed      = progress.get("elapsed", "—")
    remaining    = progress.get("remaining", "—")

    # ── Queue position — fetch for any pre-printing status with printer ───────
    queue_pos = 0
    if printer_id and status_lower in (
        "queued", "queue assigned", "waiting", "preparing"
    ):
        try:
            queue_pos = get_queue_position(job_id, printer_id)
        except Exception:
            queue_pos = 0

    # ── ETA string + estimated start/end clock times ──────────────────────────
    def _fmt_min(m: int) -> str:
        if m < 1:
            return "< 1 min"
        if m < 60:
            return f"{m} min"
        h, rem = divmod(m, 60)
        return f"{h}h {rem}m" if rem else f"{h}h"

    now = _dt.now()

    if status_lower == "printing":
        eta_str   = f"~{remaining}"
        start_str = "Now"
        end_min   = int(progress.get("total_pages", pages * copies) / max(1, progress.get("ppm", 20)))
        end_str   = (now + timedelta(minutes=max(1, end_min))).strftime("%I:%M %p")
    elif status_lower in ("completed", "ready", "collected"):
        eta_str   = "Done"
        start_str = "—"
        end_str   = "—"
    elif ewt is not None and ewt > 0:
        # Use DB-stored ETA (set by assign_printer_and_queue after payment)
        eta_str   = _fmt_min(int(ewt))
        start_str = (now + timedelta(minutes=int(ewt))).strftime("%I:%M %p")
        total_print_min = max(1, int((pages * copies) / 20))
        end_str   = (now + timedelta(minutes=int(ewt) + total_print_min)).strftime("%I:%M %p")
    elif status_lower in ("queued", "waiting", "queue assigned"):
        # Fallback estimate when no ETA stored
        est_min   = max(1, (pages * copies) // 20 + 1)
        eta_str   = _fmt_min(est_min)
        start_str = (now + timedelta(minutes=est_min)).strftime("%I:%M %p")
        end_str   = (now + timedelta(minutes=est_min + max(1, (pages * copies) // 20))).strftime("%I:%M %p")
    else:
        eta_str   = "Awaiting payment"
        start_str = "—"
        end_str   = "—"

    # ── Card HTML ─────────────────────────────────────────────────────────────
    priority_badge = (
        '<span style="background:rgba(168,85,247,.2);color:#a855f7;border:1px solid rgba(168,85,247,.4);'
        'padding:2px 10px;border-radius:10px;font-size:.7rem;font-weight:700;">⚡ PRIORITY</span>'
        if priority and priority.lower() in ("priority", "high", "urgent") else ""
    )
    status_anim = 'class="printing-pulse"' if status_lower == "printing" else ""
    qpos_badge = (
        f'<div style="font-size:.72rem;color:rgba(255,255,255,.35);margin-top:4px;">Queue #{queue_pos}</div>'
        if queue_pos else ""
    )

    st.html(_clean_html(f"""
        <div class="job-card">
            <div class="jc-header">
                <div>
                    <div class="jc-print-id">{print_id}</div>
                    <div class="jc-doc-name">{doc_name[:50]}</div>
                    <div class="jc-meta">{pages}p × {copies} copies · {created} · {printer_name}</div>
                </div>
                <div style="text-align:right;">
                    <span class="jc-status-badge" {status_anim}
                          style="background:{status_color}22;color:{status_color};border:1px solid {status_color}44;">
                        ● {status}
                    </span>
                    <div style="margin-top:6px;">{priority_badge}</div>
                    {qpos_badge}
                </div>
            </div>
        </div>
    """))

    # ── Progress bar ──────────────────────────────────────────────────────────
    if status_lower == "printing":
        st.html(f"""
        <div style="margin:0 0 4px;">
            <div style="display:flex;justify-content:space-between;font-size:.72rem;
                        color:rgba(255,255,255,.4);margin-bottom:3px;">
                <span>🖨️ Page {current_page} / {total_p}</span>
                <span>{progress_pct}%</span>
            </div>
            <div class="pr-bar-bg">
                <div class="pr-bar-fill printing-bar" style="width:{progress_pct}%;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.7rem;
                        color:rgba(255,255,255,.3);margin-top:4px;">
                <span>Elapsed: {elapsed}</span><span>Remaining: {remaining}</span>
            </div>
        </div>
        """)
    else:
        pct = min(100, max(0, int((stage_idx / (len(_STAGES) - 1)) * 100)))
        st.progress(pct / 100)

    # ── Stage pipeline ────────────────────────────────────────────────────────
    stage_cols = st.columns(len(_STAGES))
    for i, (col, (stage_name, icon, color)) in enumerate(zip(stage_cols, _STAGES)):
        with col:
            if i < stage_idx:
                bg  = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},.08)"
                cls = f"color:{color};"
            elif i == stage_idx:
                bg  = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},.15)"
                cls = f"color:{color};border:1px solid {color}44;"
            else:
                bg  = "rgba(255,255,255,.02)"
                cls = "color:rgba(255,255,255,.2);"
            st.html(f"""
            <div style="text-align:center;padding:6px 2px;border-radius:8px;
                        background:{bg};{cls}transition:all .3s;">
                <div style="font-size:.9rem;">{icon}</div>
                <div style="font-size:.55rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:.3px;margin-top:2px;">{stage_name}</div>
            </div>
            """)

    # ── Six-metric row ────────────────────────────────────────────────────────
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    metrics = [
        (m1, "🖨️ Printer",       printer_name[:18]),
        (m2, "📄 Pages",          f"{pages} × {copies}"),
        (m3, "⏱️ ETA",            eta_str),
        (m4, "📋 Queue Position", f"#{queue_pos}" if queue_pos else "—"),
        (m5, "🕐 Est. Start",     start_str),
        (m6, "✅ Est. Complete",  end_str),
    ]
    for col, label, value in metrics:
        with col:
            st.html(f"""
            <div class="metric-pill">
                <div class="mp-label">{label}</div>
                <div class="mp-value">{value}</div>
            </div>""")

    # ── Pickup ID if present ──────────────────────────────────────────────────
    if pickup_id:
        st.html(f"""
        <div style="background:rgba(124,255,0,.05);border:1px solid rgba(124,255,0,.2);
                    border-radius:10px;padding:10px 14px;margin:8px 0;">
            <span style="font-size:.68rem;color:rgba(255,255,255,.4);
                         text-transform:uppercase;">Pickup ID</span>
            <span style="font-size:1rem;font-weight:800;color:#8B5CF6;
                         font-family:monospace;margin-left:10px;">{pickup_id}</span>
        </div>
        """)

    # ── Timeline ──────────────────────────────────────────────────────────────
    if job_id:
        timeline = []
        try:
            timeline = get_job_timeline(job_id) or []
        except Exception:
            timeline = []
        if timeline:
            with st.expander(f"📅 Job Timeline — {len(timeline)} events", expanded=False):
                for ev in reversed(timeline):
                    t          = ev.get("time", "")
                    icon_ev    = ev.get("icon", "●")
                    event_name = ev.get("event", "")
                    st.html(f"""
                    <div style="display:flex;align-items:center;gap:10px;
                                padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);">
                        <span style="font-size:.75rem;color:rgba(255,255,255,.3);
                                     font-family:monospace;min-width:45px;">{t}</span>
                        <span style="font-size:.9rem;">{icon_ev}</span>
                        <span style="font-size:.82rem;color:rgba(255,255,255,.7);">{event_name}</span>
                    </div>
                    """)

    # ── Cancel button (only when allowed) ─────────────────────────────────────
    can_cancel = status_lower in CANCELLABLE_STATUSES
    if can_cancel:
        bc1, bc2 = st.columns([3, 1])
        with bc2:
            if st.button("❌ Cancel Job", key=f"cancel_btn_{job_id}_{idx}", use_container_width=True):
                ok, msg = cancel_job_safe(job_id)
                if ok:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

    st.html('<div class="job-divider"></div>')


def _queue_css() -> str:
    return """
    <style>
    @keyframes printing-pulse {
        0%,100% { opacity:1; }
        50% { opacity:.6; }
    }
    @keyframes bar-animate {
        0% { opacity:.7; } 50% { opacity:1; } 100% { opacity:.7; }
    }
    .printing-pulse { animation: printing-pulse 1.5s ease-in-out infinite !important; }
    .printing-bar { animation: bar-animate 1.5s ease-in-out infinite;
                    background: linear-gradient(90deg,#3B82F6,#8B5CF6) !important; }

    .queue-header { text-align:center; padding:20px 0 10px; }
    .queue-icon { font-size:3rem; margin-bottom:8px; }
    .queue-title {
        font-size:2rem; font-weight:800;
        background:linear-gradient(135deg,#3B82F6,#8B5CF6);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .queue-subtitle { color:rgba(255,255,255,0.5); font-size:.95rem; margin-top:4px; }

    .empty-state {
        text-align:center; padding:40px 20px;
        background:rgba(255,255,255,.03); border:1px dashed rgba(255,255,255,.1);
        border-radius:16px; margin:15px 0;
    }

    .job-card {
        background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
        border-radius:16px; padding:16px 20px; margin-top:10px;
    }
    .jc-header { display:flex; justify-content:space-between; align-items:flex-start; }
    .jc-print-id { font-family:'Courier New',monospace; color:#3B82F6; font-weight:700; font-size:.95rem; }
    .jc-doc-name { color:#fff; font-weight:600; font-size:.95rem; margin:4px 0 2px; }
    .jc-meta { color:rgba(255,255,255,.4); font-size:.78rem; }
    .jc-status-badge { padding:4px 12px; border-radius:12px; font-size:.78rem; font-weight:700;
                        display:inline-block; }

    .metric-pill {
        background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
        border-radius:10px; padding:8px 12px; margin:6px 0;
    }
    .mp-label { font-size:.65rem; color:rgba(255,255,255,.4); text-transform:uppercase; letter-spacing:.3px; }
    .mp-value { font-size:.9rem; font-weight:700; color:#fff; margin-top:2px; }

    .pr-bar-bg { height:8px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; margin:4px 0; }
    .pr-bar-fill { height:8px; border-radius:4px; transition:width .4s; background:#3B82F6; }

    .job-divider { border-top:1px solid rgba(255,255,255,.04); margin:14px 0 8px; }
    </style>
    """
