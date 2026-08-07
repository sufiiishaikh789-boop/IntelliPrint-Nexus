"""
IntelliPrint Nexus - Enhanced Print History
Per-job: Pickup ID, QR Code, PDF Preview, Print Status, Download Receipt.
"""

import streamlit as st
import os
import re
from datetime import datetime

from smartdb.crud import get_user_jobs, get_all_printers, get_job_timeline
from smartdb.crud import get_payment_by_job
try:
    from smartdb.crud_ext import bookmark_job as _bookmark_job
except ImportError:
    _bookmark_job = None


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


def show_print_history():
    """Render the enhanced print history page."""

    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_history_css())

    st.markdown("""
    <div class="hist-header">
        <div class="hist-title">📜 My Print History</div>
        <div class="hist-subtitle">View, download and track all your print jobs</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch jobs ────────────────────────────────────────────────────────
    all_jobs = get_user_jobs(user_id) or []
    all_jobs = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)

    # Fetch printer names for display
    printer_names = {}
    try:
        for p in (get_all_printers() or []):
            printer_names[p["id"]] = p.get("name", "Printer")
    except Exception:
        pass

    # ── Filter bar ────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([3, 1, 1])
    with f1:
        search = st.text_input("🔍 Search by document name or ID", placeholder="Search...",
                               key="hist_search", label_visibility="collapsed")
    with f2:
        status_f = st.selectbox("Status", ["All", "Pending", "Queued", "Printing",
                                           "Completed", "Ready", "Collected", "Failed"],
                                key="hist_status_f")
    with f3:
        if st.button("🔄 Refresh", key="hist_refresh", use_container_width=True):
            st.rerun()

    # Apply filters
    if search:
        q = search.lower()
        all_jobs = [j for j in all_jobs if
                    q in (j.get("document_name") or "").lower() or
                    q in (j.get("print_id") or "").lower()]
    if status_f != "All":
        all_jobs = [j for j in all_jobs if (j.get("status") or "").lower() == status_f.lower()]

    st.markdown(f'<div class="hist-count">{len(all_jobs)} job(s) found</div>', unsafe_allow_html=True)

    if not all_jobs:
        st.markdown("""
        <div class="hist-empty">
            <div style="font-size:3rem;">📭</div>
            <div class="hist-empty-title">No print jobs found</div>
            <div class="hist-empty-sub">Upload a document to create your first print job</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Job list ──────────────────────────────────────────────────────────
    for job in all_jobs:
        _render_job_row(job, printer_names, user_id)


def _render_job_row(job: dict, printer_names: dict, user_id: int = 0):
    """Render one job row with expandable detail panel."""
    job_id      = job.get("id")
    print_id    = job.get("print_id", "N/A")
    doc         = job.get("document_name", "Document")
    status      = (job.get("status") or "unknown")
    status_disp = status.replace("_", " ").title()
    badge_color = _status_color(status.lower())
    cost        = job.get("total_cost", job.get("cost", 0))
    pages       = job.get("total_pages", job.get("pages", 0))
    copies      = job.get("copies", 1)
    created     = str(job.get("created_at", ""))[:16]
    pickup_id   = job.get("pickup_id")
    qr_path     = job.get("qr_code_path")
    preview_path = job.get("preview_pdf_path")
    file_path   = job.get("file_path")
    printer_id  = job.get("printer_id")
    printer_name = printer_names.get(printer_id, "—")
    is_bookmarked = bool(job.get("is_bookmarked", False))

    has_pickup  = bool(pickup_id)
    pickup_icon = "🔑" if has_pickup else "⏳"
    bk_icon     = "⭐" if is_bookmarked else "☆"

    # Main row — 8 columns: id, doc, pages, cost, status, date, bookmark, view
    r1, r2, r3, r4, r5, r6, r7, r8 = st.columns([1.4, 1.8, 0.7, 0.7, 1.0, 1.1, 0.55, 0.9])
    with r1:
        st.markdown(f'<div style="font-family:monospace;color:#3B82F6;font-size:.8rem;font-weight:700;padding-top:8px;">{print_id}</div>', unsafe_allow_html=True)
    with r2:
        st.markdown(f'<div style="color:rgba(255,255,255,.8);font-size:.85rem;padding-top:8px;" title="{doc}">{doc[:24]}{"…" if len(doc)>24 else ""}</div>', unsafe_allow_html=True)
    with r3:
        st.markdown(f'<div style="color:rgba(255,255,255,.55);font-size:.82rem;padding-top:8px;">{pages}p×{copies}</div>', unsafe_allow_html=True)
    with r4:
        st.markdown(f'<div style="color:#3B82F6;font-weight:600;font-size:.85rem;padding-top:8px;">₹{cost:.2f}</div>', unsafe_allow_html=True)
    with r5:
        st.markdown(f'<div style="padding-top:6px;"><span style="background:{badge_color}22;color:{badge_color};padding:3px 10px;border-radius:10px;font-size:.72rem;font-weight:700;">{status_disp}</span></div>', unsafe_allow_html=True)
    with r6:
        st.markdown(f'<div style="color:rgba(255,255,255,.35);font-size:.78rem;padding-top:8px;">{created}</div>', unsafe_allow_html=True)
    with r7:
        # Bookmark toggle button
        if _bookmark_job and job_id:
            if st.button(bk_icon, key=f"bk_{job_id}", help="Toggle Bookmark"):
                _bookmark_job(job_id, user_id, state=not is_bookmarked)
                st.rerun()
        else:
            st.markdown(f'<div style="padding-top:8px;color:rgba(255,255,255,.25);">{bk_icon}</div>', unsafe_allow_html=True)
    with r8:
        expand_label = f"{pickup_icon} {'Details' if has_pickup else 'View'}"
        expand_key   = f"hist_exp_{job_id}"
        if st.button(expand_label, key=f"hist_btn_{job_id}", use_container_width=True):
            st.session_state[expand_key] = not st.session_state.get(expand_key, False)

    # Expandable detail panel
    if st.session_state.get(f"hist_exp_{job_id}", False):
        _render_job_detail(job, printer_name, pickup_id, qr_path, preview_path, file_path, badge_color, status_disp, user_id)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,.05);margin:2px 0;">', unsafe_allow_html=True)


def _render_job_detail(job, printer_name, pickup_id, qr_path, preview_path, file_path, badge_color, status_disp, user_id=0):
    """Render the expanded detail panel for a job."""
    print_id  = job.get("print_id", "—")
    doc       = job.get("document_name", "Document")
    pages     = job.get("total_pages", job.get("pages", 0))
    copies    = job.get("copies", 1)
    color_mode = job.get("color_mode", "BW")
    duplex    = "Duplex" if job.get("duplex") else "Simplex"
    priority  = job.get("priority", "Normal") or "Normal"
    cost      = job.get("total_cost", job.get("cost", 0))
    created   = str(job.get("created_at", ""))[:16]
    wait      = job.get("estimated_wait_time", 0) or 0
    fingerprint = job.get("document_fingerprint")

    fp_html = (
        f'<div><span style="color:rgba(255,255,255,.4);">SHA-256:</span> '
        f'<span style="color:rgba(0,217,255,.5);font-family:monospace;font-size:.69rem;">'
        f'{fingerprint[:20]}…</span></div>'
        if fingerprint else ""
    )

    with st.container():
        st.markdown('<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px 18px;margin:4px 0 10px;">', unsafe_allow_html=True)

        d1, d2, d3 = st.columns([1, 1, 1])

        with d1:
            st.markdown(f"""
            <div style="font-size:.8rem;color:rgba(255,255,255,.5);margin-bottom:10px;font-weight:700;text-transform:uppercase;">📋 Job Information</div>
            <div style="font-size:.82rem;line-height:2.0;">
                <div><span style="color:rgba(255,255,255,.4);">Print ID:</span> <span style="color:#3B82F6;font-family:monospace;">{print_id}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Document:</span> <span style="color:#fff;">{doc}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Pages:</span> <span style="color:#fff;">{pages} × {copies} copies</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Color:</span> <span style="color:#fff;">{color_mode}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Side:</span> <span style="color:#fff;">{duplex}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Priority:</span> <span style="color:{'#f59e0b' if priority!='Normal' else '#fff'};">{priority}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Printer:</span> <span style="color:#fff;">{printer_name}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Est. Wait:</span> <span style="color:#f59e0b;">{wait} min</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Uploaded:</span> <span style="color:#fff;">{created}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Status:</span> <span style="background:{badge_color}22;color:{badge_color};padding:1px 8px;border-radius:6px;font-size:.72rem;">{status_disp}</span></div>
                <div><span style="color:rgba(255,255,255,.4);">Total Cost:</span> <span style="color:#8B5CF6;font-weight:700;">₹{cost:.2f}</span></div>
                {fp_html}
            </div>
            """, unsafe_allow_html=True)

        with d2:
            st.markdown("""
            <div style="font-size:.8rem;color:rgba(255,255,255,.5);margin-bottom:10px;font-weight:700;text-transform:uppercase;">🔑 Pickup Details</div>
            """, unsafe_allow_html=True)

            if pickup_id:
                st.markdown(f"""
                <div style="background:rgba(124,255,0,.05);border:1px solid rgba(124,255,0,.2);border-radius:10px;padding:12px;margin-bottom:10px;">
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.4px;">Pickup ID</div>
                    <div style="font-size:1.1rem;font-weight:800;color:#8B5CF6;font-family:monospace;margin-top:4px;">{pickup_id}</div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.35);margin-top:6px;">Show this ID at the printer terminal</div>
                </div>
                """, unsafe_allow_html=True)

                if qr_path and os.path.exists(qr_path):
                    st.image(qr_path, width=130, caption="Scan to collect printout")
                else:
                    st.markdown('<div style="color:rgba(255,255,255,.3);font-size:.8rem;">QR Code unavailable</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(245,158,11,.05);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:12px;">
                    <div style="font-size:.8rem;color:#f59e0b;">⏳ Pickup ID &amp; QR Code generated after payment.</div>
                </div>
                """, unsafe_allow_html=True)

        with d3:
            st.markdown("""
            <div style="font-size:.8rem;color:rgba(255,255,255,.5);margin-bottom:10px;font-weight:700;text-transform:uppercase;">📥 Downloads</div>
            """, unsafe_allow_html=True)

            # ── PDF Receipt ──────────────────────────────────────────────
            job_id = job.get("id")
            payment = None
            try:
                payment = get_payment_by_job(job_id) if job_id else None
            except Exception:
                payment = None
            payment_id = payment.get("transaction_id", "") if payment else ""
            amount = float(payment.get("amount", 0)) if payment else float(job.get("total_cost", 0) or 0)

            try:
                from smartutils.receipt_generator import generate_receipt
                import os as _os
                receipt_dir = "uploads/receipts"
                receipt_path = _os.path.join(receipt_dir, f"receipt_{print_id}.pdf")
                if not _os.path.exists(receipt_path):
                    receipt_path = generate_receipt(
                        output_dir=receipt_dir,
                        student_name=user.get("username", "Student"),
                        student_id=str(user.get("id", "—")),
                        document_name=job.get("document_name", "—"),
                        printer_name=printer_name,
                        pages=job.get("total_pages", 1) or 1,
                        copies=job.get("copies", 1) or 1,
                        color_mode=job.get("color_mode", "BW"),
                        duplex=bool(job.get("duplex")),
                        paper_size=job.get("paper_size", "A4"),
                        priority=job.get("priority", "Normal"),
                        amount=amount,
                        payment_id=payment_id,
                        pickup_id=pickup_id or "Pending",
                        qr_image_path=job.get("qr_code_path", "") or "",
                        print_id=print_id,
                        status=job.get("status", ""),
                    )
                if receipt_path and _os.path.exists(receipt_path):
                    with open(receipt_path, "rb") as rf:
                        st.download_button(
                            "🧾 Download Receipt (PDF)",
                            data=rf.read(),
                            file_name=f"receipt_{print_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_receipt_{job_id}",
                            use_container_width=True,
                        )
            except Exception as rex:
                # Fallback to text receipt
                receipt_text = _generate_receipt(job, printer_name, pickup_id)
                st.download_button(
                    "🧾 Download Receipt",
                    data=receipt_text,
                    file_name=f"receipt_{print_id}.txt",
                    mime="text/plain",
                    key=f"dl_receipt_txt_{job_id}",
                    use_container_width=True,
                )

            # Download original PDF
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button(
                        "📄 Download Original PDF",
                        data=f.read(),
                        file_name=f"original_{print_id}.pdf",
                        mime="application/pdf",
                        key=f"dl_orig_{job.get('id')}",
                        use_container_width=True,
                    )

            # Download print-ready PDF (post-payment, has separator sheet)
            if preview_path and os.path.exists(preview_path):
                with open(preview_path, "rb") as f:
                    st.download_button(
                        "🖨️ Download Print-Ready PDF",
                        data=f.read(),
                        file_name=f"printready_{print_id}.pdf",
                        mime="application/pdf",
                        key=f"dl_prev_{job.get('id')}",
                        use_container_width=True,
                    )
            elif pickup_id:
                st.markdown('<div style="color:rgba(255,255,255,.25);font-size:.75rem;margin-top:6px;">Print-Ready PDF generating...</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:rgba(255,255,255,.25);font-size:.75rem;margin-top:6px;">Print-Ready PDF available after payment</div>', unsafe_allow_html=True)

        # ── Timeline viewer (full width below the 3 columns) ─────────────
        timeline_events = []
        try:
            timeline_events = get_job_timeline(job.get("id")) or []
        except Exception:
            timeline_events = []

        if timeline_events:
            with st.expander(f"📅 Job Timeline — {len(timeline_events)} events", expanded=False):
                for ev in reversed(timeline_events):
                    t = ev.get("time", "")
                    icon_ev = ev.get("icon", "●")
                    event_name = ev.get("event", "")
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;
                                padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);">
                        <span style="font-size:.75rem;color:rgba(255,255,255,.3);
                                     font-family:monospace;min-width:45px;">{t}</span>
                        <span style="font-size:.9rem;">{icon_ev}</span>
                        <span style="font-size:.82rem;color:rgba(255,255,255,.7);">{event_name}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Action buttons ────────────────────────────────────────────────
        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
        act1, act2, act3 = st.columns([1, 1, 1])
        with act1:
            if st.button("🔁 Print Again", key=f"reprint_{job.get('id')}", use_container_width=True,
                         help="Queue this document again with the same settings"):
                st.session_state["reprint_prefill"] = {
                    "file_path":  file_path,
                    "doc_name":   doc,
                    "copies":     copies,
                    "color_mode": color_mode,
                    "duplex":     job.get("duplex", False),
                    "paper_size": job.get("paper_size", "A4"),
                    "priority":   priority,
                }
                st.session_state["current_page"] = "Submit Print Job"
                st.success("✅ Redirecting to upload with same settings...")
                st.rerun()
        with act2:
            if st.button("📍 Track Live", key=f"track_{job.get('id')}", use_container_width=True):
                st.session_state["track_job_id"] = print_id
                st.session_state["current_page"] = "Track Order"
                st.rerun()
        with act3:
            bk_state = bool(job.get("is_bookmarked", False))
            bk_label = "★ Bookmarked" if bk_state else "☆ Bookmark"
            if _bookmark_job and st.button(bk_label, key=f"bk_detail_{job.get('id')}", use_container_width=True):
                _bookmark_job(job.get("id"), user_id, state=not bk_state)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


def _generate_receipt(job: dict, printer_name: str, pickup_id: str) -> str:
    """Generate a plain-text receipt."""
    lines = [
        "=" * 48,
        "         IntelliPrint Nexus — OFFICIAL RECEIPT",
        "=" * 48,
        f"  Print ID     : {job.get('print_id', 'N/A')}",
        f"  Pickup ID    : {pickup_id or 'Pending Payment'}",
        f"  Document     : {job.get('document_name', 'N/A')}",
        f"  Pages        : {job.get('total_pages', job.get('pages', 0))}",
        f"  Copies       : {job.get('copies', 1)}",
        f"  Color Mode   : {job.get('color_mode', 'BW')}",
        f"  Print Side   : {'Duplex' if job.get('duplex') else 'Simplex'}",
        f"  Priority     : {job.get('priority', 'Normal') or 'Normal'}",
        f"  Printer      : {printer_name}",
        f"  Cost/Page    : ₹{job.get('cost_per_page', 2.0):.2f}",
        f"  Total Cost   : ₹{job.get('total_cost', job.get('cost', 0)):.2f}",
        f"  Status       : {(job.get('status') or 'N/A').replace('_', ' ').title()}",
        f"  Uploaded At  : {str(job.get('submitted_at', job.get('created_at', '')))[:16]}",
        "=" * 48,
        "  IntelliPrint Nexus — Thank you for using our service!",
        "  Scan QR or show Pickup ID at the printer terminal.",
        "=" * 48,
    ]
    return "\n".join(lines)


def _status_color(status: str) -> str:
    return {
        "pending": "#f59e0b", "payment_pending": "#f59e0b",
        "queued": "#3b82f6", "printing": "#A78BFA",
        "completed": "#10b981", "ready": "#06b6d4",
        "collected": "#059669", "failed": "#ef4444",
    }.get(status, "#6b7280")


def _history_css() -> str:
    return """<style>
.hist-header { padding:18px 0 12px; }
.hist-title { font-size:1.9rem; font-weight:800; background:linear-gradient(135deg,#3B82F6,#60A5FA); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hist-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }
.hist-count { color:rgba(255,255,255,.35); font-size:.82rem; margin:8px 0 14px; }
.hist-empty { text-align:center; padding:50px 20px; background:rgba(255,255,255,.02); border:1px dashed rgba(255,255,255,.08); border-radius:16px; }
.hist-empty-title { font-size:1.1rem; font-weight:600; color:rgba(255,255,255,.6); margin:10px 0 4px; }
.hist-empty-sub { font-size:.85rem; color:rgba(255,255,255,.3); }
</style>"""
