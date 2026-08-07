"""
IntelliPrint Nexus - Admin Activity Feed & Audit Log
Chronological live activity feed + audit log of all admin actions.
"""

import streamlit as st
import re
import json
from datetime import datetime, timedelta

from smartdb.crud import get_all_jobs, get_all_printers, get_all_users_with_stats


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


def _status_icon(status: str) -> str:
    icons = {
        "pending": "⏳", "queued": "📋", "queue assigned": "📋",
        "preparing": "🔥", "printing": "🖨️",
        "completed": "✅", "ready": "📦",
        "collected": "🏃", "cancelled": "❌",
        "failed": "⚠️", "archived": "🗃️",
        "payment_pending": "💳",
    }
    return icons.get(status.lower(), "●")


def _status_color(status: str) -> str:
    colors = {
        "pending": "#f59e0b", "queued": "#3b82f6", "queue assigned": "#3b82f6",
        "preparing": "#f97316", "printing": "#3B82F6",
        "completed": "#10b981", "ready": "#8B5CF6",
        "collected": "#6b7280", "cancelled": "#ef4444",
        "failed": "#ef4444", "payment_pending": "#f97316",
    }
    return colors.get(status.lower(), "#6b7280")


def _build_activity_feed(jobs: list, printers: dict) -> list:
    """Build a unified activity feed from job timeline events."""
    events = []
    for job in jobs:
        doc = (job.get("document_name") or "Document")[:30]
        user_id = job.get("user_id", "?")
        printer_id = job.get("printer_id")
        printer_name = printers.get(printer_id, "Unassigned") if printer_id else "Unassigned"
        print_id = job.get("print_id", "")
        status = job.get("status", "")

        # Parse stored timeline events
        raw_tl = job.get("job_timeline")
        if raw_tl:
            try:
                timeline = json.loads(raw_tl)
                for ev in timeline:
                    events.append({
                        "time": ev.get("time", ""),
                        "icon": ev.get("icon", "●"),
                        "message": f"{ev.get('event','?')} — {doc} ({print_id})",
                        "meta": f"Student #{user_id} • {printer_name}",
                        "color": "#3B82F6",
                        "status": status,
                    })
            except Exception:
                pass

        # Fall back: derive events from timestamps
        submitted = job.get("submitted_at")
        completed = job.get("completed_at")
        if submitted:
            t = str(submitted)[11:16]
            events.append({
                "time": t,
                "icon": "📤",
                "message": f"Uploaded — {doc} ({print_id})",
                "meta": f"Student #{user_id}",
                "color": "#3b82f6",
                "status": "uploaded",
            })
        if completed:
            t = str(completed)[11:16]
            events.append({
                "time": t,
                "icon": "✅",
                "message": f"Completed — {doc} ({print_id})",
                "meta": f"Student #{user_id} • {printer_name}",
                "color": "#10b981",
                "status": "completed",
            })

    # Sort by time (string sort works for HH:MM format)
    events.sort(key=lambda e: e.get("time", ""), reverse=True)
    return events[:100]  # Cap at 100 events


def show_admin_activity():
    """Render the activity feed and audit log page."""
    st.html(_activity_css())

    st.markdown("""
    <div class="act-header">
        <div class="act-title">📡 Live Activity Feed</div>
        <div class="act-subtitle">Real-time chronological log of all system events and admin actions</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────────────
    jobs = get_all_jobs() or []
    printers_list = get_all_printers() or []
    printers = {p["id"]: p["name"] for p in printers_list}

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📡 Activity Feed", "🖨️ Printer Events", "📊 Job Summary"])

    with tab1:
        _render_activity_feed(jobs, printers)

    with tab2:
        _render_printer_events(jobs, printers_list)

    with tab3:
        _render_job_summary(jobs, printers)

    # Refresh button
    if st.button("🔄 Refresh Feed", key="act_refresh", use_container_width=False):
        st.rerun()


def _render_activity_feed(jobs: list, printers: dict):
    """Render the main chronological activity feed."""
    events = _build_activity_feed(jobs, printers)

    if not events:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:rgba(255,255,255,.4);">
            📭 No activity recorded yet. Activity will appear here as jobs are processed.
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div style="font-size:.8rem;color:rgba(255,255,255,.4);margin-bottom:12px;">
        Showing {len(events)} recent events (newest first)
    </div>
    """, unsafe_allow_html=True)

    for ev in events:
        t = ev.get("time", "")
        icon = ev.get("icon", "●")
        message = ev.get("message", "")
        meta = ev.get("meta", "")
        color = ev.get("color", "#6b7280")

        st.markdown(f"""
        <div class="act-event">
            <div class="ae-time">{t}</div>
            <div class="ae-dot" style="background:{color};"></div>
            <div class="ae-body">
                <div class="ae-msg">{icon} {message}</div>
                <div class="ae-meta">{meta}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_printer_events(jobs: list, printers_list: list):
    """Render per-printer event breakdown."""
    for p in printers_list:
        pid = p.get("id")
        pname = p.get("name", "Printer")
        p_jobs = [j for j in jobs if j.get("printer_id") == pid]
        total = len(p_jobs)
        printing = sum(1 for j in p_jobs if (j.get("status") or "").lower() == "printing")
        completed = sum(1 for j in p_jobs if (j.get("status") or "").lower() in ("completed", "ready", "collected"))
        failed = sum(1 for j in p_jobs if (j.get("status") or "").lower() in ("failed", "cancelled"))
        status = (p.get("status") or "Unknown")
        status_color = _status_color(status)

        st.markdown(f"""
        <div class="printer-event-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div>
                    <div style="font-size:1rem;font-weight:700;color:#fff;">🖨️ {pname}</div>
                    <div style="font-size:.75rem;color:rgba(255,255,255,.4);">📍 {p.get('location','—')}</div>
                </div>
                <span style="background:{status_color}22;color:{status_color};border:1px solid {status_color}44;
                             padding:3px 12px;border-radius:10px;font-size:.75rem;font-weight:700;">
                    ● {status}
                </span>
            </div>
            <div style="display:flex;gap:12px;flex-wrap:wrap;">
                <div class="pe-metric"><div style="color:#3B82F6;font-weight:800;">{total}</div><div class="pe-lbl">Total Jobs</div></div>
                <div class="pe-metric"><div style="color:#eab308;font-weight:800;">{printing}</div><div class="pe-lbl">Printing</div></div>
                <div class="pe-metric"><div style="color:#10b981;font-weight:800;">{completed}</div><div class="pe-lbl">Completed</div></div>
                <div class="pe-metric"><div style="color:#ef4444;font-weight:800;">{failed}</div><div class="pe-lbl">Failed/Cancelled</div></div>
                <div class="pe-metric"><div style="color:#8B5CF6;font-weight:800;">{p.get('toner_level',100):.0f}%</div><div class="pe-lbl">Toner</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_job_summary(jobs: list, printers: dict):
    """Render a summary table of all jobs."""
    if not jobs:
        st.markdown('<div style="color:rgba(255,255,255,.4);padding:20px;">No jobs found.</div>', unsafe_allow_html=True)
        return

    # Status distribution
    from collections import Counter
    status_counts = Counter((j.get("status") or "Unknown") for j in jobs)

    st.markdown("**Status Distribution**")
    cols = st.columns(min(len(status_counts), 6))
    for col, (status, count) in zip(cols, status_counts.most_common()):
        color = _status_color(status)
        with col:
            st.markdown(f"""
            <div class="twin-stat" style="border-left:3px solid {color};">
                <div class="ts-label">{_status_icon(status)} {status}</div>
                <div class="ts-value" style="color:{color};">{count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Recent jobs table
    st.markdown("**Recent Jobs (Last 20)**")
    recent = sorted(jobs, key=lambda j: str(j.get("submitted_at", "")), reverse=True)[:20]
    for j in recent:
        status = j.get("status", "")
        color = _status_color(status)
        icon = _status_icon(status)
        doc = (j.get("document_name") or "—")[:28]
        pid = j.get("printer_id")
        pname = printers.get(pid, "Unassigned") if pid else "Unassigned"
        st.markdown(f"""
        <div class="act-event">
            <div class="ae-time">{str(j.get('submitted_at',''))[:16]}</div>
            <div class="ae-dot" style="background:{color};"></div>
            <div class="ae-body">
                <div class="ae-msg">{icon} {doc} — <code style="color:#3B82F6;">{j.get('print_id','')}</code></div>
                <div class="ae-meta">Student #{j.get('user_id','?')} • {pname} •
                    <span style="color:{color};">{status}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _activity_css() -> str:
    return """<style>
.act-header { padding:18px 0 12px; margin-bottom:1rem; }
.act-title {
    font-size:1.9rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.act-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }

.act-event {
    display:flex; align-items:flex-start; gap:10px;
    padding:8px 0; border-bottom:1px solid rgba(255,255,255,.04);
}
.ae-time { font-size:.72rem; color:rgba(255,255,255,.35); font-family:monospace;
           min-width:52px; padding-top:3px; }
.ae-dot { width:8px; height:8px; border-radius:50%; margin-top:6px; flex-shrink:0; }
.ae-body { flex:1; }
.ae-msg { font-size:.84rem; color:rgba(255,255,255,.8); font-weight:500; }
.ae-meta { font-size:.72rem; color:rgba(255,255,255,.35); margin-top:1px; }

.printer-event-card {
    background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:14px; margin-bottom:10px;
}
.pe-metric { text-align:center; background:rgba(255,255,255,.03);
             border-radius:8px; padding:8px 14px; }
.pe-lbl { font-size:.62rem; color:rgba(255,255,255,.4);
           text-transform:uppercase; letter-spacing:.3px; margin-top:2px; }

.twin-stat { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
             border-radius:12px; padding:12px 16px; margin-bottom:12px; }
.ts-label { font-size:.72rem; color:rgba(255,255,255,.45); font-weight:600; text-transform:uppercase; }
.ts-value { font-size:1.4rem; font-weight:800; margin-top:2px; }
</style>"""
