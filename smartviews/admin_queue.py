"""
IntelliPrint Nexus - Admin Queue & Live Monitor
Fully Automated Print Monitoring with Live Queue View.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import get_all_jobs, get_all_printers

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def _live_queue_monitor(all_jobs: list, printers: list):
    """Render a live queue monitor with per-printer job tracking."""
    st.markdown('<div class="lq-title">📡 Live Queue Monitor</div>', unsafe_allow_html=True)

    # Per-printer active view
    if printers:
        for p in printers:
            pid = p.get("id")
            pname = p.get("name", "Printer")
            pstatus = p.get("status", "Unknown")
            pstatus_color = {"online": "#10b981", "offline": "#ef4444", "maintenance": "#f59e0b"}.get(pstatus.lower(), "#6b7280")
            printing_job = next((j for j in all_jobs if j.get("printer_id") == pid and (j.get("status") or "").lower() == "printing"), None)
            queued_jobs = [j for j in all_jobs if j.get("printer_id") == pid and (j.get("status") or "").lower() == "queued"]

            if printing_job:
                pages = printing_job.get("total_pages", 1) or 1
                copies = printing_job.get("copies", 1) or 1
                priority = printing_job.get("priority", "Normal")
                wait = printing_job.get("estimated_wait_time", 0) or 0
                doc = (printing_job.get("document_name") or "Document")[:30]
                progress_pct = min(95, max(10, 60))  # estimated mid-progress
                user_id = printing_job.get("user_id", "?")
                print_id = printing_job.get("print_id", "—")
                st.markdown(f"""
                <div class="lq-printer-card active-printer">
                    <div class="lq-printer-top">
                        <div>
                            <span class="lq-printer-name">🖨️ {pname}</span>
                            <span class="lq-printer-status" style="color:{pstatus_color};">● {pstatus}</span>
                        </div>
                        <span class="lq-printing-label">🟢 PRINTING</span>
                    </div>
                    <div class="lq-active-job">
                        <div class="lq-job-doc">📄 {doc}</div>
                        <div class="lq-job-meta">
                            ID: <b style="color:#3B82F6;">{print_id}</b> &nbsp;•&nbsp;
                            Student: <b>#{user_id}</b> &nbsp;•&nbsp;
                            Pages: <b>{pages}×{copies}</b> &nbsp;•&nbsp;
                            Priority: <b style="color:{'#f59e0b' if priority=='Priority' else '#a0aec0'};">{priority}</b> &nbsp;•&nbsp;
                            Est. Remaining: <b>{wait} min</b>
                        </div>
                        <div style="margin-top:8px;">
                            <div style="display:flex;justify-content:space-between;font-size:.7rem;color:rgba(255,255,255,.4);margin-bottom:3px;">
                                <span>Progress</span><span>{progress_pct}%</span>
                            </div>
                            <div class="lq-progress-bg"><div class="lq-progress-fill" style="width:{progress_pct}%;"></div></div>
                        </div>
                    </div>
                    {f'<div class="lq-queue-count">⏳ {len(queued_jobs)} job(s) waiting in queue</div>' if queued_jobs else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="lq-printer-card idle-printer">
                    <div class="lq-printer-top">
                        <div>
                            <span class="lq-printer-name">🖨️ {pname}</span>
                            <span class="lq-printer-status" style="color:{pstatus_color};">● {pstatus}</span>
                        </div>
                        <span class="lq-idle-label">{'🟡 IDLE' if pstatus.lower()=='online' else '🔴 ' + pstatus.upper()}</span>
                    </div>
                    {f'<div class="lq-queue-count">⏳ {len(queued_jobs)} job(s) waiting in queue</div>' if queued_jobs else '<div class="lq-no-jobs">No jobs assigned</div>'}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No printers registered in the system.")

    # ── Unassigned/pending queue ───────────────────────────────────────────
    unassigned = [j for j in all_jobs if (j.get("status") or "").lower() in ("pending", "payment_pending", "queued") and not j.get("printer_id")]
    if unassigned:
        st.markdown(f"""
        <div class="lq-unassigned">
            <div class="lq-unassigned-title">📥 Unassigned Queue ({len(unassigned)} jobs)</div>
        </div>
        """, unsafe_allow_html=True)
        for i, j in enumerate(unassigned[:8], 1):
            status = j.get("status", "Pending")
            badge_color = {"pending": "#f59e0b", "payment_pending": "#e67e22", "queued": "#3b82f6"}.get(status.lower(), "#6b7280")
            st.markdown(f"""
            <div class="lq-unassigned-row">
                <span style="color:rgba(255,255,255,.4);min-width:24px;">#{i}</span>
                <span style="color:#3B82F6;font-family:monospace;font-size:.82rem;">{j.get('print_id','—')}</span>
                <span style="flex:1;color:rgba(255,255,255,.7);font-size:.82rem;">{(j.get('document_name') or 'Document')[:30]}</span>
                <span style="color:rgba(255,255,255,.4);font-size:.75rem;">Student #{j.get('user_id','?')}</span>
                <span class="lq-badge" style="background:{badge_color}22;color:{badge_color};">{status}</span>
            </div>
            """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Queue", key="lq_refresh_btn"):
        st.rerun()
    st.markdown("---")


def show_admin_queue():
    """Render the admin automated queue dashboard."""

    st.html(_clean_html(_aq_css()))

    st.markdown(_clean_html("""
        <div class="aq-header">
            <div class="aq-icon">🔧</div>
            <div class="aq-title">Queue & Hardware Monitoring</div>
            <div class="aq-subtitle">Live queue monitor + automated print management</div>
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

    # ── Live Queue Monitor (NEW) ─────────────────────────────────────────
    _live_queue_monitor(all_jobs, printers)


    all_jobs = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)

    # ── Stats bar ────────────────────────────────────────────────────────
    total_revenue = sum(j.get("cost", 0) for j in all_jobs if j.get("status", "").lower() not in ("failed", "pending"))
    queued_count = sum(1 for j in all_jobs if j.get("status", "").lower() == "queued")
    printing_count = sum(1 for j in all_jobs if j.get("status", "").lower() == "printing")
    completed_count = sum(1 for j in all_jobs if j.get("status", "").lower() in ("completed", "ready"))

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    _mini_stat(sc1, "Total Revenue", f"₹{total_revenue:.0f}", "#f59e0b")
    _mini_stat(sc2, "Total Jobs", str(len(all_jobs)), "#3B82F6")
    _mini_stat(sc3, "Queued", str(queued_count), "#3b82f6")
    _mini_stat(sc4, "Printing", str(printing_count), "#A78BFA")
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
                        <div style="color:#60A5FA; font-weight:700; font-size:1.1rem;">{len(active_jobs)} Active Jobs</div>
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
        "printing": "#A78BFA",
        "completed": "#10b981",
        "ready": "#06b6d4",
        "failed": "#ef4444",
    }.get(status, "#6b7280")

def _aq_css() -> str:
    return """
    <style>
    .aq-header { text-align: center; padding: 20px 0 10px; }
    .aq-icon { font-size: 3rem; margin-bottom: 8px; }
    .aq-title { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #3B82F6, #60A5FA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .aq-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    .section-title { font-size: 1.15rem; font-weight: 700; color: rgba(255,255,255,0.85); margin-bottom: 12px; }
    .aq-mini-stat { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px 10px; text-align: center; }
    .aq-ms-value { font-size: 1.5rem; font-weight: 800; color: #fff; }
    .aq-ms-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; }
    .aq-job-row { display: flex; align-items: center; gap: 14px; padding: 14px 18px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; margin-bottom: 4px; }
    .aq-job-row:hover { background: rgba(255,255,255,0.06); }
    .aq-job-id { font-family: 'Courier New', monospace; color: #3B82F6; font-weight: 600; font-size: 0.85rem; min-width: 120px; }
    .aq-job-doc { flex: 1; color: rgba(255,255,255,0.7); font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .aq-job-user { color: rgba(255,255,255,0.4); font-size: 0.82rem; min-width: 80px; }
    .aq-badge { padding: 3px 12px; border-radius: 16px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; }
    .aq-job-time { color: rgba(255,255,255,0.3); font-size: 0.78rem; min-width: 120px; text-align: right; }

    /* Live Queue Monitor */
    .lq-title { font-size:1.1rem; font-weight:700; color:rgba(255,255,255,.85); text-transform:uppercase; letter-spacing:.5px; margin:0 0 12px; }
    .lq-printer-card { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:14px; padding:16px; margin-bottom:10px; }
    .active-printer { border-color:rgba(57,255,20,.2); background:rgba(57,255,20,.03); }
    .idle-printer { border-color:rgba(255,255,255,.05); }
    .lq-printer-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .lq-printer-name { font-size:1rem; font-weight:700; color:#fff; margin-right:10px; }
    .lq-printer-status { font-size:.78rem; font-weight:600; }
    .lq-printing-label { background:rgba(57,255,20,.12); color:#A78BFA; padding:4px 12px; border-radius:10px; font-size:.75rem; font-weight:700; letter-spacing:.5px; }
    .lq-idle-label { background:rgba(255,255,255,.07); color:rgba(255,255,255,.5); padding:4px 12px; border-radius:10px; font-size:.75rem; font-weight:700; }
    .lq-active-job { background:rgba(0,0,0,.2); border-radius:10px; padding:12px; }
    .lq-job-doc { font-size:.9rem; font-weight:600; color:#fff; margin-bottom:6px; }
    .lq-job-meta { font-size:.78rem; color:rgba(255,255,255,.5); line-height:1.8; }
    .lq-progress-bg { height:6px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
    .lq-progress-fill { height:6px; background:linear-gradient(90deg,#A78BFA,#3B82F6); border-radius:4px; animation:lq-pulse 2s ease-in-out infinite; }
    @keyframes lq-pulse { 0%,100%{opacity:.8} 50%{opacity:1} }
    .lq-queue-count { margin-top:8px; font-size:.78rem; color:rgba(255,255,255,.4); }
    .lq-no-jobs { font-size:.78rem; color:rgba(255,255,255,.25); margin-top:6px; }
    .lq-unassigned { margin:12px 0 6px; }
    .lq-unassigned-title { font-size:.88rem; font-weight:700; color:#f59e0b; margin-bottom:6px; }
    .lq-unassigned-row { display:flex; align-items:center; gap:10px; padding:8px 12px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.04); border-radius:8px; margin-bottom:3px; }
    .lq-badge { padding:2px 8px; border-radius:10px; font-size:.68rem; font-weight:700; }
    </style>
    """

