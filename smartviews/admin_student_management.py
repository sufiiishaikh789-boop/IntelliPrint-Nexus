"""
IntelliPrint Nexus - Admin Student Management
View, search, filter and manage all registered students.
"""

import streamlit as st
from smartdb.crud import get_all_users_with_stats


def show_student_management():
    """Render the student management page."""
    st.html(_sm_css())

    st.markdown("""
    <div class="sm-header">
        <div class="sm-title">👥 Student Management</div>
        <div class="sm-subtitle">View and manage all registered students and their print activity</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────────
    students = []
    try:
        students = get_all_users_with_stats() or []
    except Exception as e:
        st.error(f"Error loading students: {e}")
        return

    # ── Summary ───────────────────────────────────────────────────────────
    total_stu = len(students)
    active_stu = sum(1 for s in students if (s.get("status") or "").lower() == "active")
    total_prints = sum(s.get("total_prints", 0) for s in students)
    total_revenue = sum(s.get("total_amount", 0) for s in students)

    m1, m2, m3, m4 = st.columns(4)
    _sm_metric(m1, "👥 Total Students", total_stu, "#3B82F6")
    _sm_metric(m2, "✅ Active", active_stu, "#10b981")
    _sm_metric(m3, "📄 Total Prints", total_prints, "#8B5CF6")
    _sm_metric(m4, "💰 Total Revenue", f"₹{total_revenue:,.2f}", "#f59e0b")

    st.markdown("---")

    # ── Search & Filters ──────────────────────────────────────────────────
    s1, s2, s3 = st.columns([3, 1, 1])
    with s1:
        search = st.text_input("🔍 Search by name or email", placeholder="Type to search...", key="sm_search", label_visibility="collapsed")
    with s2:
        status_f = st.selectbox("Status", ["All", "Active", "Inactive"], key="sm_status")
    with s3:
        sort_f = st.selectbox("Sort by", ["Most Prints", "Most Spent", "Newest", "Name A-Z"], key="sm_sort")

    # ── Filter ────────────────────────────────────────────────────────────
    filtered = students[:]
    if search:
        q = search.lower()
        filtered = [s for s in filtered if
                    q in (s.get("username") or "").lower() or
                    q in (s.get("email") or "").lower()]
    if status_f != "All":
        filtered = [s for s in filtered if (s.get("status") or "").lower() == status_f.lower()]

    if sort_f == "Most Prints":
        filtered.sort(key=lambda x: x.get("total_prints", 0), reverse=True)
    elif sort_f == "Most Spent":
        filtered.sort(key=lambda x: x.get("total_amount", 0), reverse=True)
    elif sort_f == "Name A-Z":
        filtered.sort(key=lambda x: (x.get("username") or "").lower())

    st.markdown(f'<div class="sm-count">Showing <b>{len(filtered)}</b> of <b>{total_stu}</b> students</div>', unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="sm-empty">
            <div style="font-size:3rem;">👤</div>
            <div class="sm-empty-title">No Students Found</div>
            <div class="sm-empty-desc">No students match your search or filter.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Table header ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="sm-table-header">
        <span style="flex:0.5">#</span>
        <span style="flex:1.4">Name</span>
        <span style="flex:1.8">Email</span>
        <span style="flex:0.6">Status</span>
        <span style="flex:0.7">Prints</span>
        <span style="flex:0.7">Pages</span>
        <span style="flex:0.9">Spent</span>
        <span style="flex:0.6">Priority</span>
        <span style="flex:0.6">Cancelled</span>
        <span style="flex:0.7">Completed</span>
        <span style="flex:1.0">Last Print</span>
        <span style="flex:0.5">Details</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Pagination ────────────────────────────────────────────────────────
    page_size = 20
    total_pgs = max(1, (len(filtered) + page_size - 1) // page_size)
    if "sm_page" not in st.session_state:
        st.session_state["sm_page"] = 0
    pg = min(st.session_state["sm_page"], total_pgs - 1)
    page_items = filtered[pg * page_size:(pg + 1) * page_size]

    # ── Student rows ──────────────────────────────────────────────────────
    for i, s in enumerate(page_items, start=pg * page_size + 1):
        status = s.get("status", "Active")
        status_color = "#10b981" if status.lower() == "active" else "#6b7280"
        uid = s.get("id")

        st.markdown(f"""
        <div class="sm-row">
            <span class="sm-cell" style="flex:0.5;color:rgba(255,255,255,.35);">{i}</span>
            <span class="sm-cell" style="flex:1.4;font-weight:600;color:#fff;">{s.get('username','—')}</span>
            <span class="sm-cell" style="flex:1.8;color:rgba(255,255,255,.55);font-size:.78rem;">{s.get('email','—')}</span>
            <span class="sm-cell" style="flex:0.6;">
                <span class="sm-badge" style="background:{status_color}22;color:{status_color};">{status}</span>
            </span>
            <span class="sm-cell" style="flex:0.7;color:#3B82F6;font-weight:700;">{s.get('total_prints',0)}</span>
            <span class="sm-cell" style="flex:0.7;">{s.get('total_pages',0)}</span>
            <span class="sm-cell" style="flex:0.9;color:#8B5CF6;">₹{s.get('total_amount',0):.0f}</span>
            <span class="sm-cell" style="flex:0.6;color:#f59e0b;">{s.get('priority_prints',0)}</span>
            <span class="sm-cell" style="flex:0.6;color:#ef4444;">{s.get('cancelled_prints',0)}</span>
            <span class="sm-cell" style="flex:0.7;color:#10b981;">{s.get('completed_prints',0)}</span>
            <span class="sm-cell" style="flex:1.0;font-size:.75rem;color:rgba(255,255,255,.4);">{s.get('last_print_date','—')}</span>
        </div>
        """, unsafe_allow_html=True)

        # Detail expand button
        if st.button("📋", key=f"sm_detail_{uid}", help="View student details"):
            st.session_state[f"sm_open_{uid}"] = not st.session_state.get(f"sm_open_{uid}", False)

        if st.session_state.get(f"sm_open_{uid}"):
            _render_student_modal(s, uid, status, status_color)

    # ── Pagination ────────────────────────────────────────────────────────
    if total_pgs > 1:
        pc1, pc2, pc3 = st.columns([1, 3, 1])
        with pc1:
            if st.button("← Prev", key="sm_prev", disabled=pg == 0):
                st.session_state["sm_page"] = max(0, pg - 1)
                st.rerun()
        with pc2:
            st.markdown(f'<div style="text-align:center;color:rgba(255,255,255,.5);padding-top:8px;">Page {pg+1} of {total_pgs}</div>', unsafe_allow_html=True)
        with pc3:
            if st.button("Next →", key="sm_next", disabled=pg >= total_pgs - 1):
                st.session_state["sm_page"] = min(total_pgs - 1, pg + 1)
                st.rerun()


def _render_student_modal(s: dict, uid: int, status: str, status_color: str):
    """Render full professional student profile modal with job history."""
    from smartdb.crud import get_user_jobs, get_all_printers
    import os

    # Fetch student's jobs and printer names
    jobs = []
    printer_names = {}
    try:
        jobs = sorted(get_user_jobs(uid) or [], key=lambda j: j.get("created_at", ""), reverse=True)
        for p in (get_all_printers() or []):
            printer_names[p["id"]] = p.get("name", "Printer")
    except Exception:
        pass

    with st.expander(f"👤 {s.get('username', '—')} — Full Student Profile", expanded=True):
        # ── Profile + Stats ───────────────────────────────────────────────
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown(f"""
            <div class="sm-detail-card">
                <div class="sm-detail-title">👤 Student Profile</div>
                <div class="sm-detail-row"><span>Student ID</span><b>#{uid}</b></div>
                <div class="sm-detail-row"><span>Name</span><b>{s.get('username','—')}</b></div>
                <div class="sm-detail-row"><span>Email</span><b style="font-size:.78rem;">{s.get('email','—')}</b></div>
                <div class="sm-detail-row"><span>Role</span><b>{s.get('role','Student')}</b></div>
                <div class="sm-detail-row"><span>Department</span><b>{s.get('department','—')}</b></div>
                <div class="sm-detail-row"><span>Semester</span><b>{s.get('semester','—')}</b></div>
                <div class="sm-detail-row"><span>Phone</span><b>{s.get('phone','—')}</b></div>
                <div class="sm-detail-row"><span>Status</span><b style="color:{status_color};">{status}</b></div>
                <div class="sm-detail-row"><span>Registered</span><b>{str(s.get('created_at',''))[:10]}</b></div>
                <div class="sm-detail-row"><span>Last Login</span><b>{str(s.get('last_login',''))[:16] or '—'}</b></div>
            </div>
            """, unsafe_allow_html=True)
        with dc2:
            st.markdown(f"""
            <div class="sm-detail-card">
                <div class="sm-detail-title">📊 Print Statistics</div>
                <div class="sm-detail-row"><span>Total Prints</span><b style="color:#3B82F6;">{s.get('total_prints',0)}</b></div>
                <div class="sm-detail-row"><span>Total Pages</span><b>{s.get('total_pages',0)}</b></div>
                <div class="sm-detail-row"><span>Total Amount Paid</span><b style="color:#8B5CF6;">₹{s.get('total_amount',0):.2f}</b></div>
                <div class="sm-detail-row"><span>Priority Jobs</span><b style="color:#f59e0b;">{s.get('priority_prints',0)}</b></div>
                <div class="sm-detail-row"><span>Completed Jobs</span><b style="color:#10b981;">{s.get('completed_prints',0)}</b></div>
                <div class="sm-detail-row"><span>Cancelled Jobs</span><b style="color:#ef4444;">{s.get('cancelled_prints',0)}</b></div>
                <div class="sm-detail-row"><span>Last Print</span><b>{s.get('last_print_date','—')}</b></div>
            </div>
            """, unsafe_allow_html=True)
        with dc3:
            # Quick job status breakdown
            completed_c = sum(1 for j in jobs if (j.get("status") or "").lower() in ("completed","ready","collected"))
            queued_c    = sum(1 for j in jobs if (j.get("status") or "").lower() in ("queued","printing"))
            pending_c   = sum(1 for j in jobs if (j.get("status") or "").lower() in ("pending","payment_pending"))
            cancelled_c = sum(1 for j in jobs if (j.get("status") or "").lower() == "cancelled")
            total_paid  = sum(j.get("total_cost", j.get("cost", 0)) for j in jobs if (j.get("status") or "").lower() not in ("cancelled","failed","pending"))

            st.markdown(f"""
            <div class="sm-detail-card">
                <div class="sm-detail-title">⚡ Live Summary</div>
                <div class="sm-detail-row"><span>Total Documents</span><b>{len(jobs)}</b></div>
                <div class="sm-detail-row"><span>✅ Completed</span><b style="color:#10b981;">{completed_c}</b></div>
                <div class="sm-detail-row"><span>🔄 In Queue/Printing</span><b style="color:#3b82f6;">{queued_c}</b></div>
                <div class="sm-detail-row"><span>⏳ Pending Payment</span><b style="color:#f59e0b;">{pending_c}</b></div>
                <div class="sm-detail-row"><span>❌ Cancelled</span><b style="color:#ef4444;">{cancelled_c}</b></div>
                <div class="sm-detail-row"><span>💰 Revenue Generated</span><b style="color:#8B5CF6;">₹{total_paid:.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)

        # ── Recent Jobs Table ─────────────────────────────────────────────
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sm-detail-title" style="margin-bottom:10px;">📄 Recent Print Jobs</div>', unsafe_allow_html=True)

        if not jobs:
            st.info("No print jobs found for this student.")
        else:
            st.markdown("""
            <div class="sm-jobs-header">
                <span style="flex:1.2">Document</span>
                <span style="flex:0.9">Upload Date</span>
                <span style="flex:1.2">Printer</span>
                <span style="flex:0.5">Pages</span>
                <span style="flex:0.5">Copies</span>
                <span style="flex:0.8">Amount</span>
                <span style="flex:0.8">Pay Status</span>
                <span style="flex:0.9">Print Status</span>
                <span style="flex:1.2">Pickup ID</span>
                <span style="flex:0.5">QR</span>
                <span style="flex:0.8">Preview</span>
            </div>
            """, unsafe_allow_html=True)

            for j in jobs[:20]:
                j_status  = (j.get("status") or "").lower()
                j_sbadge  = {"pending":"#f59e0b","payment_pending":"#f59e0b","queued":"#3b82f6",
                             "printing":"#A78BFA","completed":"#10b981","ready":"#06b6d4",
                             "collected":"#059669","cancelled":"#ef4444","failed":"#dc2626"}.get(j_status,"#6b7280")
                pickup_id = j.get("pickup_id") or ""
                qr_path   = j.get("qr_code_path") or ""
                prev_path = j.get("preview_pdf_path") or ""
                doc       = (j.get("document_name") or "Document")[:22]
                p_name    = printer_names.get(j.get("printer_id"), "—")[:18]
                cost      = j.get("total_cost", j.get("cost", 0))
                created   = str(j.get("submitted_at", j.get("created_at", "")))[:10]

                col_row, col_qr, col_prev = st.columns([8, 0.8, 1])
                with col_row:
                    st.markdown(f"""
                    <div class="sm-job-row">
                        <span style="flex:1.2;font-size:.78rem;color:#fff;" title="{j.get('document_name','')}">{doc}</span>
                        <span style="flex:0.9;font-size:.72rem;color:rgba(255,255,255,.4);">{created}</span>
                        <span style="flex:1.2;font-size:.75rem;color:rgba(255,255,255,.6);">{p_name}</span>
                        <span style="flex:0.5;text-align:center;">{j.get('total_pages',0)}</span>
                        <span style="flex:0.5;text-align:center;">{j.get('copies',1)}</span>
                        <span style="flex:0.8;color:#8B5CF6;font-weight:600;">₹{cost:.2f}</span>
                        <span style="flex:0.8;"><span style="color:#10b981;font-size:.7rem;">{'✅ Paid' if pickup_id else '⏳ Pending'}</span></span>
                        <span style="flex:0.9;"><span style="background:{j_sbadge}22;color:{j_sbadge};padding:2px 6px;border-radius:6px;font-size:.68rem;">{(j.get('status') or '—').replace('_',' ').title()}</span></span>
                        <span style="flex:1.2;color:#8B5CF6;font-family:monospace;font-size:.75rem;">{pickup_id or '—'}</span>
                    </div>
                    """, unsafe_allow_html=True)

                with col_qr:
                    if qr_path and os.path.exists(qr_path):
                        st.image(qr_path, width=50)
                    else:
                        st.markdown('<div style="color:rgba(255,255,255,.2);font-size:.65rem;text-align:center;">—</div>', unsafe_allow_html=True)

                with col_prev:
                    if prev_path and os.path.exists(prev_path):
                        with open(prev_path, "rb") as pf:
                            st.download_button(
                                "🖨️",
                                data=pf.read(),
                                file_name=f"printready_{j.get('print_id','job')}.pdf",
                                mime="application/pdf",
                                key=f"admin_prev_{j.get('id')}",
                                help="Download Print-Ready PDF (with separator sheet)",
                            )
                    else:
                        file_path = j.get("file_path") or ""
                        if file_path and os.path.exists(file_path):
                            with open(file_path, "rb") as of:
                                st.download_button(
                                    "📎",
                                    data=of.read(),
                                    file_name=f"original_{j.get('print_id','job')}.pdf",
                                    mime="application/pdf",
                                    key=f"admin_orig_{j.get('id')}",
                                    help="Download Original PDF",
                                )
                        else:
                            st.markdown('<div style="color:rgba(255,255,255,.2);font-size:.65rem;">—</div>', unsafe_allow_html=True)

        if st.button("✕ Close Profile", key=f"sm_close_{uid}"):
            st.session_state[f"sm_open_{uid}"] = False
            st.rerun()


def _sm_metric(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="sm-stat" style="border-left:3px solid {color};">
            <div class="sm-stat-label">{label}</div>
            <div class="sm-stat-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _sm_css() -> str:
    return """<style>
.sm-header { padding: 18px 0 12px; margin-bottom: 1rem; }
.sm-title { font-size: 1.9rem; font-weight: 800; color: #fff; }
.sm-subtitle { color: rgba(255,255,255,.45); font-size: .9rem; margin-top: 4px; }

.sm-stat {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
}
.sm-stat-label { font-size: .78rem; color: rgba(255,255,255,.45); font-weight: 600; text-transform: uppercase; }
.sm-stat-value { font-size: 1.5rem; font-weight: 800; margin-top: 2px; }

.sm-count { color: rgba(255,255,255,.4); font-size: .82rem; margin: 8px 0; }

.sm-table-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: rgba(0,217,255,.06);
    border: 1px solid rgba(0,217,255,.12);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: .7rem;
    font-weight: 700;
    color: rgba(0,217,255,.8);
    text-transform: uppercase;
    letter-spacing: .4px;
    gap: 6px;
}
.sm-row {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    background: rgba(255,255,255,.02);
    border: 1px solid rgba(255,255,255,.05);
    border-radius: 8px;
    margin-bottom: 2px;
    gap: 6px;
}
.sm-row:hover { background: rgba(255,255,255,.04); }
.sm-cell { font-size: .82rem; color: rgba(255,255,255,.75); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sm-badge { padding: 2px 8px; border-radius: 10px; font-size: .68rem; font-weight: 700; }
.sm-empty { text-align:center; padding:60px 20px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.05); border-radius:16px; margin:20px 0; }
.sm-empty-title { font-size:1.2rem; font-weight:700; color:#fff; margin:10px 0 6px; }
.sm-empty-desc { color:rgba(255,255,255,.4); font-size:.88rem; }
.sm-detail-card { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:12px; padding:16px; }
.sm-detail-title { font-size:.9rem; font-weight:700; color:#3B82F6; margin-bottom:10px; }
.sm-detail-row { display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid rgba(255,255,255,.04); font-size:.82rem; color:rgba(255,255,255,.5); }
.sm-detail-row b { color:#fff; }
.sm-jobs-header { display:flex; align-items:center; padding:6px 10px; background:rgba(0,217,255,.04); border:1px solid rgba(0,217,255,.1); border-radius:8px; margin-bottom:4px; font-size:.65rem; font-weight:700; color:rgba(0,217,255,.7); text-transform:uppercase; letter-spacing:.3px; gap:4px; }
.sm-job-row { display:flex; align-items:center; padding:8px 10px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.04); border-radius:8px; margin-bottom:2px; gap:4px; font-size:.8rem; color:rgba(255,255,255,.7); }
.sm-job-row:hover { background:rgba(255,255,255,.035); }
</style>"""
