"""
IntelliPrint Nexus - Admin Payment Management
Complete payment history, transaction details, and financial overview.
"""

import streamlit as st
from datetime import datetime
from smartdb.crud import get_all_payments_with_jobs, get_all_printers


def show_admin_payment_mgmt():
    """Render the admin payment management page."""
    st.html(_pay_css())

    st.markdown("""
    <div class="pay-header">
        <div class="pay-title">💳 Payment Management</div>
        <div class="pay-subtitle">Complete transaction history and financial overview across all students</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────────
    payments = []
    printers_map = {}
    try:
        payments = get_all_payments_with_jobs() or []
        printers = get_all_printers() or []
        printers_map = {p["id"]: p["name"] for p in printers}
    except Exception as e:
        st.error(f"Error loading payments: {e}")
        return

    # ── Summary metrics ────────────────────────────────────────────────────
    total_revenue = sum(p.get("amount", 0) or 0 for p in payments)
    paid_count = sum(1 for p in payments if (p.get("payment_status") or "").lower() in ("completed", "paid", "success"))
    pending_count = sum(1 for p in payments if (p.get("payment_status") or "").lower() in ("pending",))
    failed_count = sum(1 for p in payments if (p.get("payment_status") or "").lower() in ("failed",))
    refunded_count = sum(1 for p in payments if (p.get("payment_status") or "").lower() in ("refunded",))

    m1, m2, m3, m4, m5 = st.columns(5)
    _pay_metric(m1, "💰 Total Revenue", f"₹{total_revenue:,.2f}", "#8B5CF6")
    _pay_metric(m2, "✅ Paid", paid_count, "#10b981")
    _pay_metric(m3, "⏳ Pending", pending_count, "#f59e0b")
    _pay_metric(m4, "❌ Failed", failed_count, "#ef4444")
    _pay_metric(m5, "💰 Refunded", refunded_count, "#06b6d4")

    st.markdown("---")

    # ── Search & Filters ──────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([3, 1, 1, 1])
    with f1:
        search = st.text_input("🔍 Search by Student, Document, or Transaction ID", placeholder="Type to search...", key="pm_search", label_visibility="collapsed")
    with f2:
        status_f = st.selectbox("Payment Status", ["All", "Completed", "Pending", "Failed", "Refunded"], key="pm_status")
    with f3:
        method_f = st.selectbox("Method", ["All", "UPI", "Card", "Cash", "Wallet"], key="pm_method")
    with f4:
        refund_f = st.selectbox("Refund Status", ["All", "Has Refund", "Refunded", "Refund Failed"], key="pm_refund")

    # ── Filter ────────────────────────────────────────────────────
    filtered = payments[:]
    if search:
        q = search.lower()
        filtered = [p for p in filtered if
                    q in (p.get("username") or "").lower() or
                    q in (p.get("document_name") or "").lower() or
                    q in (p.get("transaction_id") or "").lower() or
                    q in (p.get("print_id") or "").lower()]
    if status_f != "All":
        filtered = [p for p in filtered if (p.get("payment_status") or "").lower() == status_f.lower()]
    if method_f != "All":
        filtered = [p for p in filtered if (p.get("method") or "").lower() == method_f.lower()]
    if refund_f == "Has Refund":
        filtered = [p for p in filtered if p.get("refund_status")]
    elif refund_f == "Refunded":
        filtered = [p for p in filtered if (p.get("refund_status") or "").upper() == "REFUNDED"]
    elif refund_f == "Refund Failed":
        filtered = [p for p in filtered if (p.get("refund_status") or "").upper() == "FAILED"]

    st.markdown(f'<div class="pay-count">Showing <b>{len(filtered)}</b> of <b>{len(payments)}</b> transactions</div>', unsafe_allow_html=True)

    # ── Table header ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="pay-table-header">
        <span style="flex:0.7">Txn ID</span>
        <span style="flex:1.0">Student</span>
        <span style="flex:1.6">Document</span>
        <span style="flex:0.5">Pages</span>
        <span style="flex:0.5">Copies</span>
        <span style="flex:0.5">Color</span>
        <span style="flex:0.6">Priority</span>
        <span style="flex:0.7">Amount</span>
        <span style="flex:0.7">Method</span>
        <span style="flex:0.9">Pay Status</span>
        <span style="flex:0.9">Print Status</span>
        <span style="flex:1.3">Time</span>
        <span style="flex:0.5">Details</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Empty state ───────────────────────────────────────────────────────
    if not filtered:
        st.markdown("""
        <div class="pay-empty">
            <div style="font-size:3rem;">💸</div>
            <div class="pay-empty-title">No Transactions Found</div>
            <div class="pay-empty-desc">No payments match your current filters.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Pagination ────────────────────────────────────────────────────────
    page_size = 15
    total_pages_n = max(1, (len(filtered) + page_size - 1) // page_size)
    if "pm_page" not in st.session_state:
        st.session_state["pm_page"] = 0
    pg = min(st.session_state["pm_page"], total_pages_n - 1)
    page_items = filtered[pg * page_size:(pg + 1) * page_size]

    # ── Payment rows ──────────────────────────────────────────────────────
    for p in page_items:
        pay_status = p.get("payment_status", "Unknown")
        job_status = p.get("job_status", "Unknown")
        txn_id = str(p.get("transaction_id") or "")[:12]
        amount = p.get("amount", 0) or 0
        method = p.get("method", "—")
        color_mode = p.get("color_mode", "BW")
        priority = p.get("priority", "Normal")
        pages = p.get("total_pages", 0)
        copies = p.get("copies", 1)
        doc = (p.get("document_name") or "Unknown")[:24]
        student = p.get("username", f"User#{p.get('user_id')}")[:16]
        pay_time = str(p.get("payment_time") or "")[:16]
        pay_color = {"completed": "#10b981", "paid": "#10b981", "success": "#10b981",
                     "pending": "#f59e0b", "failed": "#ef4444"}.get(pay_status.lower(), "#6b7280")
        job_color = {"completed": "#10b981", "ready": "#06b6d4", "printing": "#A78BFA",
                     "queued": "#3b82f6", "pending": "#f59e0b"}.get(job_status.lower(), "#6b7280")

        payment_id = p.get("payment_id")
        print_id = p.get("print_id", "")

        # Refund badge inline
        refund_status_raw = p.get("refund_status") or ""
        refund_badge_html = ""
        if refund_status_raw:
            rs_upper = refund_status_raw.upper()
            rs_color = {"REFUNDED": "#10b981", "PENDING": "#f59e0b",
                        "FAILED": "#ef4444", "PROCESSING": "#3b82f6"}.get(rs_upper, "#6b7280")
            rs_label = {"REFUNDED": "REFUNDED", "PENDING": "REFUND PENDING",
                        "FAILED": "REFUND FAILED", "PROCESSING": "REFUND PROCESSING"}.get(rs_upper, rs_upper)
            refund_badge_html = (
                f'<span class="pay-badge" style="background:{rs_color}22;color:{rs_color};'
                f'border:1px solid {rs_color}44;">{rs_label}</span>'
            )

        st.markdown(f"""
        <div class="pay-row">
            <span class="pay-cell mono" style="flex:0.7;color:#3B82F6;">{txn_id}</span>
            <span class="pay-cell" style="flex:1.0;font-weight:600;">{student}</span>
            <span class="pay-cell" style="flex:1.6;color:rgba(255,255,255,.7);" title="{doc}">{doc}</span>
            <span class="pay-cell" style="flex:0.5;">{pages}</span>
            <span class="pay-cell" style="flex:0.5;">{copies}</span>
            <span class="pay-cell" style="flex:0.5;color:{'#3B82F6' if color_mode=='Color' else '#a0aec0'}">{color_mode}</span>
            <span class="pay-cell" style="flex:0.6;color:{'#f59e0b' if priority=='Priority' else '#6b7280'}">{priority}</span>
            <span class="pay-cell" style="flex:0.7;color:#8B5CF6;font-weight:700;">&#8377;{amount:.2f}</span>
            <span class="pay-cell" style="flex:0.7;color:rgba(255,255,255,.6);">{method}</span>
            <span class="pay-cell" style="flex:0.9;">
                <span class="pay-badge" style="background:{pay_color}22;color:{pay_color};border:1px solid {pay_color}44;">{pay_status}</span>
            </span>
            <span class="pay-cell" style="flex:0.9;">
                <span class="pay-badge" style="background:{job_color}22;color:{job_color};border:1px solid {job_color}44;">{job_status}</span>
                {refund_badge_html}
            </span>
            <span class="pay-cell" style="flex:1.3;font-size:.72rem;color:rgba(255,255,255,.4);">{pay_time}</span>
        </div>
        """, unsafe_allow_html=True)

        # Expandable detail
        detail_key = f"pm_detail_{payment_id}_{print_id}"
        if st.button("📋 Details", key=f"pm_btn_{payment_id}_{print_id}", help="View full transaction details"):
            st.session_state[detail_key] = not st.session_state.get(detail_key, False)

        if st.session_state.get(detail_key):
            printer_name = (printers_map.get(p.get("printer_id")) or "—")
            with st.expander(f"📄 Transaction Receipt — {txn_id}", expanded=True):
                r1, r2 = st.columns(2)
                with r1:
                    st.markdown(f"""
                    <div class="pay-receipt">
                        <div class="pay-receipt-title">🧾 Payment Receipt</div>
                        <div class="pay-receipt-row"><span>Transaction ID</span><b>{p.get('transaction_id','—')}</b></div>
                        <div class="pay-receipt-row"><span>Print Job ID</span><b>{print_id or '—'}</b></div>
                        <div class="pay-receipt-row"><span>Student</span><b>{student}</b></div>
                        <div class="pay-receipt-row"><span>Email</span><b>{p.get('email','—')}</b></div>
                        <div class="pay-receipt-row"><span>Payment Method</span><b>{method}</b></div>
                        <div class="pay-receipt-row"><span>Payment Status</span><b style="color:{pay_color};">{pay_status}</b></div>
                        <div class="pay-receipt-row"><span>Payment Time</span><b>{pay_time}</b></div>
                        <div class="pay-receipt-row"><span>Amount</span><b style="color:#8B5CF6;">₹{amount:.2f}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with r2:
                    completed_at = str(p.get("completed_at") or "\u2014")[:16]
                    submitted_at = str(p.get("submitted_at") or "\u2014")[:16]
                    st.markdown(f"""
                    <div class="pay-receipt">
                        <div class="pay-receipt-title">🖨️ Print Details</div>
                        <div class="pay-receipt-row"><span>Document</span><b>{p.get('document_name','\u2014')}</b></div>
                        <div class="pay-receipt-row"><span>Total Pages</span><b>{pages}</b></div>
                        <div class="pay-receipt-row"><span>Copies</span><b>{copies}</b></div>
                        <div class="pay-receipt-row"><span>Color Mode</span><b>{color_mode}</b></div>
                        <div class="pay-receipt-row"><span>Duplex</span><b>{'Yes' if p.get('duplex') else 'No'}</b></div>
                        <div class="pay-receipt-row"><span>Priority</span><b>{priority}</b></div>
                        <div class="pay-receipt-row"><span>Printer</span><b>{printer_name}</b></div>
                        <div class="pay-receipt-row"><span>Submitted</span><b>{submitted_at}</b></div>
                        <div class="pay-receipt-row"><span>Completed</span><b>{completed_at}</b></div>
                        <div class="pay-receipt-row"><span>Print Status</span><b style="color:{job_color};">{job_status}</b></div>
                        <div class="pay-receipt-row"><span>Ready for Pickup</span><b>{'\u2705 Yes' if job_status in ('Ready','Completed','Collected') else '\u23f3 Not yet'}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

                # Refund details panel (if any refund exists)
                refund_status_det = p.get("refund_status")
                if refund_status_det:
                    rs_col = {"REFUNDED": "#10b981", "PENDING": "#f59e0b",
                              "FAILED": "#ef4444", "PROCESSING": "#3b82f6"}.get(
                                  (refund_status_det or "").upper(), "#6b7280")
                    refund_reason_label = {
                        "STUDENT_CANCELLATION": "Student Cancellation (2% fee deducted)",
                        "POWER_FAILURE": "Power Failure (Full Refund)",
                    }.get(p.get("refund_reason") or "", p.get("refund_reason") or "\u2014")
                    orig_a = p.get("original_amount") or amount
                    pen_a  = p.get("penalty_amount") or 0
                    ref_a  = p.get("refund_amount") or 0
                    gw_id  = p.get("gateway_refund_id") or "\u2014"
                    r_init = (str(p.get("refund_initiated_at") or ""))[:16]
                    r_proc = (str(p.get("refund_processed_at") or ""))[:16]
                    fail_r = p.get("refund_failure_reason") or ""
                    st.markdown(f"""
                    <div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);
                                border-radius:12px;padding:14px 16px;margin-top:10px;">
                        <div style="font-size:.88rem;font-weight:700;color:#6EE7B7;margin-bottom:10px;">💰 Refund Details</div>
                        <div class="pay-receipt-row"><span>Refund Status</span><b style="color:{rs_col};">{(refund_status_det or '').upper()}</b></div>
                        <div class="pay-receipt-row"><span>Reason</span><b>{refund_reason_label}</b></div>
                        <div class="pay-receipt-row"><span>Original Amount</span><b>&#8377;{orig_a:.2f}</b></div>
                        <div class="pay-receipt-row"><span>Cancellation Fee</span><b style="color:#ef4444;">&#8377;{pen_a:.2f}</b></div>
                        <div class="pay-receipt-row"><span>Refunded Amount</span><b style="color:#10b981;">&#8377;{ref_a:.2f}</b></div>
                        <div class="pay-receipt-row"><span>Gateway Refund ID</span><b style="font-family:monospace;">{gw_id}</b></div>
                        <div class="pay-receipt-row"><span>Initiated At</span><b>{r_init}</b></div>
                        <div class="pay-receipt-row"><span>Processed At</span><b>{r_proc}</b></div>
                        {f'<div class="pay-receipt-row"><span>Failure Reason</span><b style="color:#ef4444;">{fail_r}</b></div>' if fail_r else ''}
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("✕ Close", key=f"pm_close_{payment_id}_{print_id}"):
                    st.session_state[detail_key] = False
                    st.rerun()

    # ── Pagination ────────────────────────────────────────────────────────
    if total_pages_n > 1:
        pc1, pc2, pc3 = st.columns([1, 3, 1])
        with pc1:
            if st.button("← Prev", key="pm_prev", disabled=pg == 0):
                st.session_state["pm_page"] = max(0, pg - 1)
                st.rerun()
        with pc2:
            st.markdown(f'<div style="text-align:center;color:rgba(255,255,255,.5);padding-top:8px;">Page {pg+1} of {total_pages_n}</div>', unsafe_allow_html=True)
        with pc3:
            if st.button("Next →", key="pm_next", disabled=pg >= total_pages_n - 1):
                st.session_state["pm_page"] = min(total_pages_n - 1, pg + 1)
                st.rerun()


def _pay_metric(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="pay-stat" style="border-left:3px solid {color};">
            <div class="pay-stat-label">{label}</div>
            <div class="pay-stat-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _pay_css() -> str:
    return """<style>
.pay-header { padding: 18px 0 12px; margin-bottom: 1rem; }
.pay-title { font-size: 1.9rem; font-weight: 800; color: #fff; }
.pay-subtitle { color: rgba(255,255,255,.45); font-size: .9rem; margin-top: 4px; }

.pay-stat {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
}
.pay-stat-label { font-size: .78rem; color: rgba(255,255,255,.45); font-weight: 600; text-transform: uppercase; }
.pay-stat-value { font-size: 1.55rem; font-weight: 800; margin-top: 2px; }

.pay-count { color: rgba(255,255,255,.4); font-size: .82rem; margin: 8px 0; }

.pay-table-header {
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

.pay-row {
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
.pay-row:hover { background: rgba(255,255,255,.04); }

.pay-cell { font-size: .8rem; color: rgba(255,255,255,.8); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mono { font-family: 'Courier New', monospace; font-size: .75rem; }

.pay-badge {
    padding: 2px 7px;
    border-radius: 10px;
    font-size: .66rem;
    font-weight: 700;
    text-transform: uppercase;
}

.pay-empty {
    text-align: center;
    padding: 60px 20px;
    background: rgba(255,255,255,.02);
    border: 1px solid rgba(255,255,255,.05);
    border-radius: 16px;
    margin: 20px 0;
}
.pay-empty-title { font-size: 1.2rem; font-weight: 700; color: #fff; margin: 10px 0 6px; }
.pay-empty-desc { color: rgba(255,255,255,.4); font-size: .88rem; }

.pay-receipt {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 16px;
}
.pay-receipt-title { font-size: .9rem; font-weight: 700; color: #3B82F6; margin-bottom: 10px; }
.pay-receipt-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid rgba(255,255,255,.04);
    font-size: .8rem;
    color: rgba(255,255,255,.5);
}
.pay-receipt-row b { color: #fff; font-weight: 600; }
</style>"""
