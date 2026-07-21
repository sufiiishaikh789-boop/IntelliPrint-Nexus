"""
SmartPrint AI - Print History Page
Complete job history with filtering, status badges, and receipt download placeholder.
"""

import streamlit as st


import re

def _clean_html(html: str) -> str:
    """Clean indentations, comments, and newlines that confuse streamlit's markdown parser."""
    # Remove HTML comments to prevent markdown parser from falling back to text/code block
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

from smartdb.crud import get_user_jobs


def show_print_history():
    """Render the print history page."""

    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_clean_html(_history_css()))

    st.markdown(_clean_html("""
        <div class="hist-header">
            <div class="hist-icon">📜</div>
            <div class="hist-title">Print History</div>
            <div class="hist-subtitle">View all your past and current print jobs</div>
        </div>
        """),
        unsafe_allow_html=True,)

    # ── Fetch jobs ───────────────────────────────────────────────────────
    all_jobs = get_user_jobs(user_id) or []
    all_jobs = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)

    # ── Status filter ────────────────────────────────────────────────────
    status_options = ["All", "Pending", "Queued", "Printing", "Completed", "Ready", "Failed"]
    selected_status = st.selectbox("Filter by Status", options=status_options, index=0)

    if selected_status != "All":
        all_jobs = [
            j for j in all_jobs if j.get("status", "").lower() == selected_status.lower()
        ]

    st.markdown(_clean_html(f'<div class="job-count">{len(all_jobs)} job(s) found</div>'),
        unsafe_allow_html=True,)

    if not all_jobs:
        st.markdown(_clean_html("""
            <div class="empty-state">
                <div style="font-size:3rem;margin-bottom:12px;">📭</div>
                <div style="font-size:1.1rem;font-weight:600;color:rgba(255,255,255,0.7);">
                    No print jobs found
                </div>
                <div style="font-size:0.85rem;color:rgba(255,255,255,0.35);margin-top:4px;">
                    Upload a document to create your first print job
                </div>
            </div>
            """),
            unsafe_allow_html=True,)
        return

    # ── Jobs table ───────────────────────────────────────────────────────
    # Header
    st.markdown(_clean_html("""
        <div class="hist-table-header">
            <div class="ht-col ht-id">Print ID</div>
            <div class="ht-col ht-doc">Document</div>
            <div class="ht-col ht-pages">Pages</div>
            <div class="ht-col ht-copies">Copies</div>
            <div class="ht-col ht-cost">Cost</div>
            <div class="ht-col ht-status">Status</div>
            <div class="ht-col ht-date">Date</div>
        </div>
        """),
        unsafe_allow_html=True,)

    for job in all_jobs:
        status = job.get("status", "unknown")
        status_display = status.replace("_", " ").title()
        badge_color = _status_badge_color(status.lower())
        cost = job.get("cost", 0)

        col_main, col_btn = st.columns([7, 1.2])
        with col_main:
            st.markdown(_clean_html(f"""
                <div class="hist-table-row" style="margin-bottom: 0; border-radius: 4px;">
                    <div class="ht-col ht-id">
                        <span class="print-id-text">{job.get('print_id', 'N/A')}</span>
                    </div>
                    <div class="ht-col ht-doc">{job.get('document_name', 'Document')}</div>
                    <div class="ht-col ht-pages">{job.get('pages', 0)}</div>
                    <div class="ht-col ht-copies">{job.get('copies', 1)}</div>
                    <div class="ht-col ht-cost">₹{cost:.2f}</div>
                    <div class="ht-col ht-status">
                        <span class="status-badge" style="background:{badge_color}20;color:{badge_color};">
                            {status_display}
                        </span>
                    </div>
                    <div class="ht-col ht-date">{job.get('created_at', '')[:10]}</div>
                </div>
                """),
                unsafe_allow_html=True,)
        with col_btn:
            st.markdown(_clean_html("<div style='height: 4px;'></div>"), unsafe_allow_html=True)
            if st.button("👁️ View", key=f"view_ai_{job.get('id')}", use_container_width=True):
                st.session_state["ai_analysis_job_id"] = job.get("id")
                st.session_state["current_page"] = "AI Analysis"
                st.rerun()
        
        # Add inline QR code pickup view
        import os
        qr_path = job.get("qr_code_path")
        if qr_path and os.path.exists(qr_path):
            with st.expander(f"📱 QR Code & Pickup details for {job.get('print_id')}"):
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.image(qr_path, width=120)
                with c2:
                    st.write(f"**Document**: {job.get('document_name')}")
                    st.write(f"**Print ID**: `{job.get('print_id')}`")
                    st.write(f"**Color Mode**: {job.get('color_mode', 'BW')}")
                    st.write(f"**Duplex**: {'Yes' if job.get('duplex') else 'No'}")
                    st.write(f"**Status**: {status_display}")
                    st.write("Scan this QR Code at the selected terminal scanner to start printing.")


    # ── Download receipt placeholder ─────────────────────────────────────
    st.markdown(_clean_html("<br>"), unsafe_allow_html=True)
    if st.button("📥  Download Receipt (Latest Job)", key="download_receipt"):
        if all_jobs:
            latest = all_jobs[0]
            receipt = _generate_receipt_text(latest)
            st.download_button(
                "💾 Save Receipt",
                data=receipt,
                file_name=f"receipt_{latest.get('print_id', 'unknown')}.txt",
                mime="text/plain",
                key="save_receipt_btn",
            )
        else:
            st.info("No jobs available for receipt download.")


def _generate_receipt_text(job: dict) -> str:
    """Generate a plain-text receipt for a job."""
    lines = [
        "═" * 40,
        "       SMARTPRINT AI - RECEIPT",
        "═" * 40,
        f"  Print ID   : {job.get('print_id', 'N/A')}",
        f"  Document   : {job.get('document_name', 'N/A')}",
        f"  Pages      : {job.get('pages', 0)}",
        f"  Copies     : {job.get('copies', 1)}",
        f"  Color Mode : {job.get('color_mode', 'B&W')}",
        f"  Paper Size : {job.get('paper_size', 'A4')}",
        f"  Cost       : ₹{job.get('cost', 0):.2f}",
        f"  Status     : {job.get('status', 'unknown').title()}",
        f"  Date       : {job.get('created_at', 'N/A')[:16]}",
        "═" * 40,
        "  Thank you for using SmartPrint AI!",
        "═" * 40,
    ]
    return "\n".join(lines)


def _status_badge_color(status: str) -> str:
    return {
        "pending": "#f59e0b",
        "payment_pending": "#f59e0b",
        "queued": "#3b82f6",
        "printing": "#39FF14",
        "completed": "#10b981",
        "ready": "#06b6d4",
        "failed": "#ef4444",
    }.get(status, "#6b7280")


# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════
def _history_css() -> str:
    return """
    <style>
    .hist-header { text-align: center; padding: 20px 0 10px; }
    .hist-icon { font-size: 3rem; margin-bottom: 8px; }
    .hist-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hist-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }

    .job-count {
        color: rgba(255,255,255,0.4);
        font-size: 0.85rem;
        margin: 8px 0 16px;
    }

    .empty-state {
        text-align: center;
        padding: 50px 20px;
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(255,255,255,0.1);
        border-radius: 16px;
    }

    /* Table header */
    .hist-table-header {
        display: flex;
        align-items: center;
        padding: 12px 18px;
        background: rgba(0,217,255,0.08);
        border-radius: 10px 10px 0 0;
        border: 1px solid rgba(0,217,255,0.15);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255,255,255,0.55);
    }

    .hist-table-row {
        display: flex;
        align-items: center;
        padding: 14px 18px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-top: none;
        font-size: 0.88rem;
        transition: background 0.2s ease;
    }
    .hist-table-row:last-child { border-radius: 0 0 10px 10px; }
    .hist-table-row:hover { background: rgba(255,255,255,0.05); }

    .ht-col { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ht-id { flex: 1.4; }
    .ht-doc { flex: 2; color: rgba(255,255,255,0.75); }
    .ht-pages { flex: 0.7; text-align: center; color: rgba(255,255,255,0.6); }
    .ht-copies { flex: 0.7; text-align: center; color: rgba(255,255,255,0.6); }
    .ht-cost { flex: 0.9; font-weight: 600; color: #00D9FF; }
    .ht-status { flex: 1.2; }
    .ht-date { flex: 1; text-align: right; color: rgba(255,255,255,0.35); font-size: 0.82rem; }

    .print-id-text {
        font-family: 'Courier New', monospace;
        color: #00D9FF; font-weight: 600; font-size: 0.82rem;
    }
    .status-badge {
        padding: 3px 12px;
        border-radius: 16px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    </style>
    """
