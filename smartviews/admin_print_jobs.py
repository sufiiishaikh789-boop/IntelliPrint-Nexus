"""
IntelliPrint Nexus - Admin Print Jobs Management
Enterprise-grade print job monitoring, control, and management.
"""

import streamlit as st
from datetime import datetime
from smartdb.crud import (
    get_all_jobs, get_all_printers, update_job_status,
    cancel_job, move_job_to_top
)


def show_print_jobs():
    """Render the admin print jobs management page."""
    st.html(_pj_css())

    st.markdown("""
    <div class="pj-header">
        <div class="pj-title">📋 Print Jobs Management</div>
        <div class="pj-subtitle">Monitor, control and manage all submitted print requests</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────────
    all_jobs = []
    printers_map = {}
    try:
        all_jobs = get_all_jobs() or []
        printers = get_all_printers() or []
        printers_map = {p["id"]: p["name"] for p in printers}
    except Exception as e:
        st.error(f"Error loading jobs: {e}")

    # ── Search & Filters ──────────────────────────────────────────────────
    col_s, col_f1, col_f2, col_f3 = st.columns([3, 1, 1, 1])
    with col_s:
        search = st.text_input("🔍 Search by Job ID, Document or Student", placeholder="Type to search...", key="pj_search", label_visibility="collapsed")
    with col_f1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Payment Pending", "Queued", "Printing", "Completed", "Ready", "Cancelled"], key="pj_status")
    with col_f2:
        priority_filter = st.selectbox("Priority", ["All", "Priority", "Normal"], key="pj_priority")
    with col_f3:
        sort_by = st.selectbox("Sort By", ["Newest", "Oldest", "Priority First"], key="pj_sort")

    # ── Filter logic ──────────────────────────────────────────────────────
    jobs = all_jobs[:]
    if search:
        q = search.lower()
        jobs = [j for j in jobs if
                q in (j.get("print_id") or "").lower() or
                q in (j.get("document_name") or "").lower() or
                q in str(j.get("user_id") or "")]
    if status_filter != "All":
        jobs = [j for j in jobs if (j.get("status") or "").lower() == status_filter.lower().replace(" ", "_")]
    if priority_filter != "All":
        jobs = [j for j in jobs if (j.get("priority") or "").lower() == priority_filter.lower()]
    if sort_by == "Oldest":
        jobs = sorted(jobs, key=lambda x: x.get("submitted_at") or "", reverse=False)
    elif sort_by == "Priority First":
        jobs = sorted(jobs, key=lambda x: 0 if (x.get("priority") or "").lower() == "priority" else 1)

    # ── Summary strip ─────────────────────────────────────────────────────
    total = len(all_jobs)
    pending_c = sum(1 for j in all_jobs if (j.get("status") or "").lower() in ("pending", "payment_pending"))
    printing_c = sum(1 for j in all_jobs if (j.get("status") or "").lower() == "printing")
    completed_c = sum(1 for j in all_jobs if (j.get("status") or "").lower() in ("completed", "ready", "collected"))
    cancelled_c = sum(1 for j in all_jobs if (j.get("status") or "").lower() in ("cancelled", "failed"))

    s1, s2, s3, s4, s5 = st.columns(5)
    _pj_stat(s1, "📄 Total", total, "#3B82F6")
    _pj_stat(s2, "⏳ Pending", pending_c, "#f59e0b")
    _pj_stat(s3, "🖨️ Printing", printing_c, "#A78BFA")
    _pj_stat(s4, "✅ Completed", completed_c, "#10b981")
    _pj_stat(s5, "❌ Cancelled", cancelled_c, "#ef4444")

    st.markdown(f'<div class="pj-count">Showing **{len(jobs)}** of **{total}** jobs</div>', unsafe_allow_html=True)

    # ── Empty state ───────────────────────────────────────────────────────
    if not jobs:
        st.markdown("""
        <div class="pj-empty">
            <div class="pj-empty-icon">📭</div>
            <div class="pj-empty-title">No Print Jobs Found</div>
            <div class="pj-empty-desc">No jobs match your current search or filter criteria.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Table header ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="pj-table-header">
        <span style="flex:1.2">Job ID</span>
        <span style="flex:0.7">Student</span>
        <span style="flex:1.8">Document</span>
        <span style="flex:0.5">Pages</span>
        <span style="flex:0.5">Copies</span>
        <span style="flex:0.6">Color</span>
        <span style="flex:0.6">Priority</span>
        <span style="flex:1.2">Printer</span>
        <span style="flex:0.6">Wait</span>
        <span style="flex:0.8">Amount</span>
        <span style="flex:0.9">Status</span>
        <span style="flex:1.4">Actions</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Pagination ────────────────────────────────────────────────────────
    page_size = 15
    total_pages = max(1, (len(jobs) + page_size - 1) // page_size)
    if "pj_page" not in st.session_state:
        st.session_state["pj_page"] = 0
    pg = st.session_state["pj_page"]
    page_jobs = jobs[pg * page_size:(pg + 1) * page_size]

    # ── Job rows ──────────────────────────────────────────────────────────
    for job in page_jobs:
        _render_job_row(job, printers_map)

    # ── Pagination controls ───────────────────────────────────────────────
    if total_pages > 1:
        pc1, pc2, pc3 = st.columns([1, 3, 1])
        with pc1:
            if st.button("← Prev", key="pj_prev", disabled=pg == 0):
                st.session_state["pj_page"] = max(0, pg - 1)
                st.rerun()
        with pc2:
            st.markdown(f'<div style="text-align:center;color:rgba(255,255,255,.5);padding-top:8px;">Page {pg+1} of {total_pages}</div>', unsafe_allow_html=True)
        with pc3:
            if st.button("Next →", key="pj_next", disabled=pg >= total_pages - 1):
                st.session_state["pj_page"] = min(total_pages - 1, pg + 1)
                st.rerun()


def _render_job_row(job: dict, printers_map: dict):
    """Render a single job row with action buttons."""
    status = job.get("status", "Unknown")
    priority = job.get("priority", "Normal")
    job_id = job.get("id")
    print_id = job.get("print_id", "N/A")
    doc_name = job.get("document_name", "Unknown")[:28]
    pages = job.get("total_pages", 0)
    copies = job.get("copies", 1)
    color = job.get("color_mode", "BW")
    wait = job.get("estimated_wait_time", 0) or 0
    amount = job.get("total_cost") or job.get("cost") or 0.0
    printer_id = job.get("printer_id")
    printer_name = printers_map.get(printer_id, "Unassigned")[:16]
    user_id = job.get("user_id", "?")

    status_color = {
        "pending": "#f59e0b", "payment_pending": "#f59e0b",
        "queued": "#3b82f6", "printing": "#A78BFA",
        "completed": "#10b981", "ready": "#06b6d4",
        "collected": "#10b981", "cancelled": "#ef4444", "failed": "#ef4444",
    }.get((status or "").lower(), "#6b7280")

    priority_color = "#f59e0b" if (priority or "").lower() == "priority" else "#6b7280"

    # Progress estimate
    progress = 0
    if (status or "").lower() == "printing":
        progress = min(95, max(10, 50))  # placeholder

    with st.container():
        st.markdown(f"""
        <div class="pj-row">
            <span class="pj-cell mono" style="flex:1.2;color:#3B82F6;">{print_id}</span>
            <span class="pj-cell" style="flex:0.7;color:rgba(255,255,255,.6);">#{user_id}</span>
            <span class="pj-cell" style="flex:1.8;" title="{doc_name}">{doc_name}</span>
            <span class="pj-cell" style="flex:0.5;">{pages}</span>
            <span class="pj-cell" style="flex:0.5;">{copies}</span>
            <span class="pj-cell" style="flex:0.6;color:{'#3B82F6' if color=='Color' else '#a0aec0'};">{color}</span>
            <span class="pj-cell" style="flex:0.6;color:{priority_color};">{priority}</span>
            <span class="pj-cell" style="flex:1.2;font-size:.75rem;">{printer_name}</span>
            <span class="pj-cell" style="flex:0.6;">{wait}m</span>
            <span class="pj-cell" style="flex:0.8;color:#8B5CF6;">₹{amount:.0f}</span>
            <span class="pj-cell" style="flex:0.9;">
                <span class="pj-badge" style="background:{status_color}22;color:{status_color};border:1px solid {status_color}44;">{status}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        a1, a2, a3, a4, a5, a6, _ = st.columns([1, 1, 1, 1, 1, 1, 3])
        with a1:
            if st.button("👁️", key=f"pj_view_{job_id}", help="View Details"):
                st.session_state[f"pj_detail_{job_id}"] = True
        with a2:
            if st.button("⏸️", key=f"pj_pause_{job_id}", help="Pause Job"):
                if job_id:
                    update_job_status(job_id, "Queued")
                    st.rerun()
        with a3:
            if st.button("▶️", key=f"pj_resume_{job_id}", help="Resume Job"):
                if job_id:
                    update_job_status(job_id, "Printing")
                    st.rerun()
        with a4:
            if st.button("❌", key=f"pj_cancel_{job_id}", help="Cancel Job"):
                if job_id:
                    cancel_job(job_id)
                    st.success(f"Job {print_id} cancelled.")
                    st.rerun()
        with a5:
            if st.button("⬆️", key=f"pj_top_{job_id}", help="Move to Top"):
                if job_id:
                    move_job_to_top(job_id)
                    st.success(f"Job {print_id} moved to top.")
                    st.rerun()
        with a6:
            if st.button("🚨", key=f"pj_emg_{job_id}", help="Emergency Print"):
                if job_id:
                    update_job_status(job_id, "Printing")
                    move_job_to_top(job_id)
                    st.success(f"Emergency print initiated for {print_id}.")
                    st.rerun()

        # Detail expander
        if st.session_state.get(f"pj_detail_{job_id}"):
            with st.expander(f"📄 Details — {print_id}", expanded=True):
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    st.markdown(f"""
                    <div class="pj-detail-card">
                        <div class="pj-detail-title">📄 Document Info</div>
                        <div class="pj-detail-row"><span>Name</span><b>{job.get('document_name','—')}</b></div>
                        <div class="pj-detail-row"><span>Pages</span><b>{pages}</b></div>
                        <div class="pj-detail-row"><span>Copies</span><b>{copies}</b></div>
                        <div class="pj-detail-row"><span>Color</span><b>{color}</b></div>
                        <div class="pj-detail-row"><span>Duplex</span><b>{'Yes' if job.get('duplex') else 'No'}</b></div>
                        <div class="pj-detail-row"><span>Paper</span><b>{job.get('paper_size','A4')}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with d2:
                    st.markdown(f"""
                    <div class="pj-detail-card">
                        <div class="pj-detail-title">🖨️ Print Info</div>
                        <div class="pj-detail-row"><span>Priority</span><b>{priority}</b></div>
                        <div class="pj-detail-row"><span>Printer</span><b>{printer_name}</b></div>
                        <div class="pj-detail-row"><span>Est. Wait</span><b>{wait} min</b></div>
                        <div class="pj-detail-row"><span>Submitted</span><b>{str(job.get('submitted_at',''))[:16]}</b></div>
                        <div class="pj-detail-row"><span>Completed</span><b>{str(job.get('completed_at',''))[:16] or '—'}</b></div>
                        <div class="pj-detail-row"><span>Status</span><b style="color:{status_color};">{status}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with d3:
                    st.markdown(f"""
                    <div class="pj-detail-card">
                        <div class="pj-detail-title">💰 Cost Info</div>
                        <div class="pj-detail-row"><span>Cost/Page</span><b>₹{job.get('cost_per_page',2.0):.2f}</b></div>
                        <div class="pj-detail-row"><span>Total Pages</span><b>{pages} × {copies}</b></div>
                        <div class="pj-detail-row"><span>Base Cost</span><b>₹{(pages*copies*(job.get('cost_per_page') or 2.0)):.2f}</b></div>
                        <div class="pj-detail-row"><span>Priority Fee</span><b>{'₹5.00' if (priority or '').lower()=='priority' else '₹0.00'}</b></div>
                        <div class="pj-detail-row"><span>Total</span><b style="color:#8B5CF6;">₹{amount:.2f}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with d4:
                    import os as _os
                    pickup_id_val  = job.get("pickup_id") or ""
                    qr_path_val    = job.get("qr_code_path") or ""
                    preview_path   = job.get("preview_pdf_path") or ""
                    orig_path      = job.get("file_path") or ""

                    st.markdown("""
                    <div class="pj-detail-card">
                        <div class="pj-detail-title">🔑 Pickup & PDFs</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if pickup_id_val:
                        st.markdown(f"""
                        <div style="background:rgba(124,255,0,.06);border:1px solid rgba(124,255,0,.25);
                                    border-radius:10px;padding:10px;margin:6px 0;">
                            <div style="font-size:.65rem;color:rgba(255,255,255,.4);
                                        text-transform:uppercase;letter-spacing:.4px;">Pickup ID</div>
                            <div style="font-size:1rem;font-weight:800;color:#8B5CF6;
                                        font-family:monospace;margin-top:4px;">{pickup_id_val}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if qr_path_val and _os.path.exists(qr_path_val):
                            st.image(qr_path_val, width=100, caption="QR Code")
                    else:
                        st.markdown("""
                        <div style="color:#f59e0b;font-size:.78rem;padding:8px 0;">
                            ⏳ Pickup ID generated after payment
                        </div>
                        """, unsafe_allow_html=True)

                    # Download print-ready PDF
                    if preview_path and _os.path.exists(preview_path):
                        with open(preview_path, "rb") as pf:
                            st.download_button(
                                "🖨️ Print-Ready PDF",
                                data=pf.read(),
                                file_name=f"printready_{print_id}.pdf",
                                mime="application/pdf",
                                key=f"admin_pj_prev_{job_id}",
                                use_container_width=True,
                            )
                    # Download original PDF
                    if orig_path and _os.path.exists(orig_path):
                        with open(orig_path, "rb") as of:
                            st.download_button(
                                "📄 Original PDF",
                                data=of.read(),
                                file_name=f"original_{print_id}.pdf",
                                mime="application/pdf",
                                key=f"admin_pj_orig_{job_id}",
                                use_container_width=True,
                            )

                if st.button("✕ Close Details", key=f"pj_close_{job_id}"):
                    st.session_state[f"pj_detail_{job_id}"] = False
                    st.rerun()


def _pj_stat(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="pj-stat-card" style="border-left:3px solid {color};">
            <div class="pj-stat-label">{label}</div>
            <div class="pj-stat-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _pj_css() -> str:
    return """<style>
.pj-header { padding: 18px 0 12px; margin-bottom: 1rem; }
.pj-title { font-size: 1.9rem; font-weight: 800; color: #fff; }
.pj-subtitle { color: rgba(255,255,255,.45); font-size: .9rem; margin-top: 4px; }

.pj-stat-card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 12px;
}
.pj-stat-label { font-size: .78rem; color: rgba(255,255,255,.45); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.pj-stat-value { font-size: 1.6rem; font-weight: 800; margin-top: 2px; }

.pj-count { color: rgba(255,255,255,.4); font-size: .82rem; margin: 4px 0 8px; }

.pj-table-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: rgba(0,217,255,.06);
    border: 1px solid rgba(0,217,255,.12);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: .72rem;
    font-weight: 700;
    color: rgba(0,217,255,.8);
    text-transform: uppercase;
    letter-spacing: .4px;
    gap: 6px;
}

.pj-row {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    background: rgba(255,255,255,.02);
    border: 1px solid rgba(255,255,255,.05);
    border-radius: 8px;
    margin-bottom: 2px;
    gap: 6px;
    transition: background .15s;
}
.pj-row:hover { background: rgba(255,255,255,.04); }

.pj-cell { font-size: .82rem; color: rgba(255,255,255,.8); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mono { font-family: 'Courier New', monospace; font-size: .78rem; }

.pj-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: .68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .3px;
}

.pj-empty {
    text-align: center;
    padding: 60px 20px;
    background: rgba(255,255,255,.02);
    border: 1px solid rgba(255,255,255,.05);
    border-radius: 16px;
    margin: 20px 0;
}
.pj-empty-icon { font-size: 3rem; margin-bottom: 12px; }
.pj-empty-title { font-size: 1.2rem; font-weight: 700; color: #fff; margin-bottom: 6px; }
.pj-empty-desc { color: rgba(255,255,255,.4); font-size: .88rem; }

.pj-detail-card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 16px;
}
.pj-detail-title { font-size: .88rem; font-weight: 700; color: #3B82F6; margin-bottom: 10px; }
.pj-detail-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,.04); font-size: .82rem; color: rgba(255,255,255,.6); }
.pj-detail-row b { color: #fff; }
</style>"""
