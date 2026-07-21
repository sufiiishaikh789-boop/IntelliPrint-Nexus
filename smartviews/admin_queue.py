"""
SmartPrint AI - Admin Analytics Dashboard
Fully Automated Print Monitoring.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import get_all_jobs, get_all_printers

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_admin_queue():
    """Render the admin automated queue dashboard."""

    st.html(_clean_html(_aq_css()))

    st.markdown(_clean_html("""
        <div class="aq-header">
            <div class="aq-icon">📊</div>
            <div class="aq-title">Queue & Hardware Monitoring</div>
            <div class="aq-subtitle">System is running in Fully Automated Mode</div>
        </div>
        """), unsafe_allow_html=True)

    # ── Fetch data ───────────────────────────────────────────────────────
    all_jobs = []
    try:
        all_jobs = get_all_jobs() or []
    except Exception:
        pass
        
    printers = []
    try:
        printers = get_all_printers() or []
    except Exception:
        pass

    all_jobs = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)

    # ── Stats bar ────────────────────────────────────────────────────────
    total_revenue = sum(j.get("cost", 0) for j in all_jobs if j.get("status", "").lower() not in ("failed", "pending"))
    queued_count = sum(1 for j in all_jobs if j.get("status", "").lower() == "queued")
    printing_count = sum(1 for j in all_jobs if j.get("status", "").lower() == "printing")
    completed_count = sum(1 for j in all_jobs if j.get("status", "").lower() in ("completed", "ready"))

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    _mini_stat(sc1, "Total Revenue", f"₹{total_revenue:.0f}", "#f59e0b")
    _mini_stat(sc2, "Total Jobs", str(len(all_jobs)), "#00D9FF")
    _mini_stat(sc3, "Queued", str(queued_count), "#3b82f6")
    _mini_stat(sc4, "Printing", str(printing_count), "#39FF14")
    _mini_stat(sc5, "Completed", str(completed_count), "#10b981")

    st.markdown(_clean_html("<br>"), unsafe_allow_html=True)
    
    # ── Hardware Printer Status ──────────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">🖨️ Hardware Status</div>'), unsafe_allow_html=True)
    
    if not printers:
        st.info("No hardware printers detected. Run printer_monitor.py.")
    else:
        for p in printers:
            active_jobs = [j for j in all_jobs if j.get("printer_id") == p.get("id") and j.get("status", "").lower() in ("queued", "printing")]
            st.markdown(_clean_html(f"""
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:700; color:#fff;">{p.get("name")}</div>
                        <div style="color:rgba(255,255,255,0.5); font-size:0.8rem;">{p.get("printer_type")} • Toner: {p.get("toner_level")}%</div>
                    </div>
                    <div>
                        <span style="color:{'#10b981' if p.get("status") == 'Online' else '#ef4444'}; font-weight:700; font-size:0.9rem;">● {p.get("status")}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#00F5FF; font-weight:700; font-size:1.1rem;">{len(active_jobs)} Active Jobs</div>
                    </div>
                </div>
                """), unsafe_allow_html=True)

    st.markdown(_clean_html("<br>"), unsafe_allow_html=True)

    # ── Job Lists (View Only) ────────────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">📋 Active Queues (Automated)</div>'), unsafe_allow_html=True)
    
    tab_queued, tab_printing, tab_completed, tab_all = st.tabs(
        ["📋 Queued", "🖨️ Printing", "✅ Completed", "All Jobs"]
    )

    with tab_queued:
        queued = [j for j in all_jobs if j.get("status", "").lower() == "queued"]
        _render_job_list(queued)

    with tab_printing:
        printing = [j for j in all_jobs if j.get("status", "").lower() == "printing"]
        _render_job_list(printing)

    with tab_completed:
        completed = [j for j in all_jobs if j.get("status", "").lower() in ("completed", "ready")]
        _render_job_list(completed)
        
    with tab_all:
        _render_job_list(all_jobs)


def _render_job_list(jobs: list):
    """Render a read-only list of jobs."""
    if not jobs:
        st.info("No jobs found in this category.")
        return

    for job in jobs:
        print_id = job.get("print_id", "N/A")
        doc_name = job.get("document_name", "Document")
        status = job.get("status", "unknown")
        user_id = job.get("user_id", "?")
        created = job.get("created_at", "")[:16]
        priority = job.get("priority", False)
        
        status_display = status.replace("_", " ").title()
        badge_color = _status_color(status.lower())

        st.markdown(_clean_html(f"""
            <div class="aq-job-row">
                <div class="aq-job-id">{print_id}</div>
                <div class="aq-job-doc">{doc_name}</div>
                <div class="aq-job-user">User #{user_id}</div>
                <span class="aq-badge" style="background:{badge_color}20;color:{badge_color};">
                    {'⚡ ' if priority else ''}{status_display}
                </span>
                <div class="aq-job-time">{created}</div>
            </div>
            """), unsafe_allow_html=True)


def _mini_stat(column, label: str, value: str, color: str):
    with column:
        st.markdown(_clean_html(f"""
            <div class="aq-mini-stat" style="border-bottom:3px solid {color};">
                <div class="aq-ms-value">{value}</div>
                <div class="aq-ms-label">{label}</div>
            </div>
            """), unsafe_allow_html=True)

def _status_color(status: str) -> str:
    return {
        "pending": "#6b7280",
        "queued": "#3b82f6",
        "printing": "#39FF14",
        "completed": "#10b981",
        "ready": "#06b6d4",
        "failed": "#ef4444",
    }.get(status, "#6b7280")

def _aq_css() -> str:
    return """
    <style>
    .aq-header { text-align: center; padding: 20px 0 10px; }
    .aq-icon { font-size: 3rem; margin-bottom: 8px; }
    .aq-title { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #00D9FF, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .aq-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    .section-title { font-size: 1.15rem; font-weight: 700; color: rgba(255,255,255,0.85); margin-bottom: 12px; }
    .aq-mini-stat { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px 10px; text-align: center; }
    .aq-ms-value { font-size: 1.5rem; font-weight: 800; color: #fff; }
    .aq-ms-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; }
    .aq-job-row { display: flex; align-items: center; gap: 14px; padding: 14px 18px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; margin-bottom: 4px; }
    .aq-job-row:hover { background: rgba(255,255,255,0.06); }
    .aq-job-id { font-family: 'Courier New', monospace; color: #00D9FF; font-weight: 600; font-size: 0.85rem; min-width: 120px; }
    .aq-job-doc { flex: 1; color: rgba(255,255,255,0.7); font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .aq-job-user { color: rgba(255,255,255,0.4); font-size: 0.82rem; min-width: 80px; }
    .aq-badge { padding: 3px 12px; border-radius: 16px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; }
    .aq-job-time { color: rgba(255,255,255,0.3); font-size: 0.78rem; min-width: 120px; text-align: right; }
    </style>
    """
