"""
SmartPrint AI - Queue Tracking
Refactored layout hierarchy following standard container layout system.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import get_user_jobs

_STATUS_STAGES = ["Pending", "Queued", "Printing", "Completed", "Ready"]
_STAGE_ICONS = {"Pending": "⏳", "Queued": "📋", "Printing": "🖨️", "Completed": "✅", "Ready": "📦"}

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_queue_tracking():
    """Render the queue tracking page."""
    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_clean_html(_queue_css()))

    # ── SECTION 1: Page Header ───────────────────────────────────────────
    with st.container():
        st.markdown(_clean_html("""
            <div class="queue-header">
                <div class="queue-icon">📋</div>
                <div class="queue-title">Queue Tracking</div>
                <div class="queue-subtitle">Monitor the live progress of your print jobs</div>
            </div>
            """), unsafe_allow_html=True)

    # ── Fetch active jobs ────────────────────────────────────────────────
    all_jobs = get_user_jobs(user_id) or []
    active_statuses = {"pending", "payment_pending", "queued", "printing"}
    active_jobs = [
        j for j in all_jobs if j.get("status", "").lower() in active_statuses
    ]

    # SECTION 2: Auto-refresh message
    with st.container():
        st.markdown(_clean_html("""
            <div class="refresh-hint">
                💡 <em>Updates occur automatically as terminal nodes complete jobs</em>
            </div>
            """), unsafe_allow_html=True)

    if not active_jobs:
        with st.container():
            st.markdown(_clean_html("""
                <div class="empty-state">
                    <div style="font-size:3rem; margin-bottom:12px;">🎉</div>
                    <div style="font-size:1.1rem; font-weight:700; color:#fff;">No Active Print Jobs</div>
                    <div style="font-size:0.85rem; color:rgba(255,255,255,0.4); margin-top:6px; max-width:400px; margin-left:auto; margin-right:auto;">
                        Your queues are clear. Upload a document from the home screen to submit a print request.
                    </div>
                </div>
                """), unsafe_allow_html=True)
            col_l, col_c, col_r = st.columns([1, 1.5, 1])
            with col_c:
                if st.button("📤 Upload Document", key="queue_upload_btn", use_container_width=True):
                    st.session_state["current_page"] = "Submit Print Job"
                    st.rerun()
        return

    # ── SECTION 3: Active Job Cards & Status Steps ────────────────────────
    for idx, job in enumerate(active_jobs):
        with st.container():
            _render_job_card(job, idx)


def _render_job_card(job: dict, idx: int):
    """Render a single job card with status visualization."""
    print_id = job.get("print_id", "N/A")
    doc_name = job.get("document_name", "Document")
    status = job.get("status", "pending").lower()
    created = job.get("created_at", "")[:16]
    pages = job.get("pages", 0)
    copies = job.get("copies", 1)

    # Normalize internal status to displays
    display_status = _normalize_status(status)
    current_stage = _STATUS_STAGES.index(display_status) if display_status in _STATUS_STAGES else 0
    progress_pct = (current_stage + 1) / len(_STATUS_STAGES)

    if display_status == "Pending":
        est_wait = "~10 min"
    elif display_status == "Queued":
        est_wait = "~5 min"
    elif display_status == "Printing":
        est_wait = "~2 min"
    else:
        est_wait = "Ready"

    st.markdown(_clean_html(f"""
        <div class="job-card">
            <div class="jc-header">
                <div class="jc-print-id">{print_id}</div>
                <div class="jc-est-wait">⏳ {est_wait}</div>
            </div>
            <div class="jc-doc-name">{doc_name}</div>
            <div class="jc-meta">{pages} pages • {copies} copies • Submitted {created}</div>
        </div>
        """), unsafe_allow_html=True)

    st.progress(progress_pct)

    # Status stages grid
    stage_cols = st.columns(len(_STATUS_STAGES))
    for i, (col, stage) in enumerate(zip(stage_cols, _STATUS_STAGES)):
        with col:
            icon = _STAGE_ICONS.get(stage, "⬜")
            if i < current_stage:
                state_class = "stage-done"
            elif i == current_stage:
                state_class = "stage-active"
            else:
                state_class = "stage-pending"

            st.markdown(_clean_html(f"""
                <div class="stage-item {state_class}">
                    <div class="stage-icon">{icon}</div>
                    <div class="stage-label">{stage}</div>
                </div>
                """), unsafe_allow_html=True)

    st.markdown('<div class="job-divider"></div>', unsafe_allow_html=True)


def _normalize_status(status: str) -> str:
    mapping = {
        "pending": "Pending",
        "payment_pending": "Pending",
        "queued": "Queued",
        "printing": "Printing",
        "completed": "Completed",
        "ready": "Ready",
        "failed": "Pending",
    }
    return mapping.get(status, "Pending")


def _queue_css() -> str:
    return """
    <style>
    .queue-header { text-align: center; padding: 20px 0 10px; }
    .queue-icon { font-size: 3rem; margin-bottom: 8px; }
    .queue-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .queue-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    
    .refresh-hint { text-align: center; color: rgba(255,255,255,0.35); font-size: 0.82rem; margin-bottom: 12px; }
    
    .empty-state {
        text-align: center; padding: 40px 20px;
        background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.1);
        border-radius: 16px; margin: 15px 0;
    }
    
    .job-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px; padding: 18px 22px; margin-top: 12px; backdrop-filter: blur(10px);
    }
    .jc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .jc-print-id { font-family: 'Courier New', monospace; color: #00D9FF; font-weight: 700; font-size: 1rem; }
    .jc-est-wait { background: rgba(0,217,255,0.15); color: #00D9FF; padding: 3px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .jc-doc-name { color: #fff; font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
    .jc-meta { color: rgba(255,255,255,0.4); font-size: 0.8rem; }
    
    .stage-item { text-align: center; padding: 8px 2px; border-radius: 10px; transition: all 0.2s ease; }
    .stage-icon { font-size: 1.15rem; margin-bottom: 2px; }
    .stage-label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    
    .stage-done { background: rgba(16,185,129,0.08); color: #10b981; }
    .stage-active { background: rgba(0,217,255,0.12); color: #00D9FF; border: 1px solid rgba(0,217,255,0.25); }
    .stage-pending { color: rgba(255,255,255,0.22); }
    
    .job-divider { border-top: 1px solid rgba(255,255,255,0.04); margin: 15px 0 10px; }
    </style>
    """
