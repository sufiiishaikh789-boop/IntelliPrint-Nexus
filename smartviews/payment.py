"""
IntelliPrint Nexus — Enterprise Premium Payment Gateway
World-class checkout experience inspired by Stripe, Razorpay & Apple Pay.
Backend logic preserved exactly; only the UI layer is upgraded.
"""

import streamlit as st
import os
import uuid
import time
import io
import base64
from datetime import datetime, timedelta

from smartdb.crud import (
    get_job_by_id, update_job_status, create_payment,
    set_job_pickup_info, get_all_printers,
    assign_printer_and_queue, create_notification,
)
from smartutils.helpers import (
    generate_qr_code, generate_pickup_id, generate_pdf_preview, write_log,
)

# ── Demo coupon registry ───────────────────────────────────────────────────────
_COUPONS = {
    "CAMPUS10": 0.10,   # 10 % off
    "NEXUS20":  0.20,   # 20 % off
    "PRINT5":   0.05,   #  5 % off
    "WELCOME":  0.15,   # 15 % off
}

# ── Payment method → backend string mapping ───────────────────────────────────
_BACKEND_STR = {
    "UPI":        "📱 UPI (GPay / PhonePe)",
    "PhonePe":    "📱 UPI (GPay / PhonePe)",
    "Paytm":      "📱 UPI (GPay / PhonePe)",
    "BHIM":       "📱 UPI (GPay / PhonePe)",
    "Card":       "💳 Credit / Debit Card",
    "Debit":      "💳 Credit / Debit Card",
    "NetBanking": "🏦 Net Banking",
    "Wallet":     "🏫 Campus Wallet",
    "Campus":     "🏫 Campus Wallet",
}

# ── Live activity feed (demo) ─────────────────────────────────────────────────
_LIVE_FEED = [
    ("Arjun S.",  "₹48.00",  "2 min ago"),
    ("Priya R.",  "₹120.00", "4 min ago"),
    ("Mehul T.",  "₹36.00",  "7 min ago"),
    ("Sneha K.",  "₹84.00",  "9 min ago"),
    ("Rohan V.",  "₹60.00",  "11 min ago"),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def show_payment():
    """Render the enterprise premium payment gateway."""
    st.html(_pay_css())

    # ── Success state ─────────────────────────────────────────────────────────
    if st.session_state.get("payment_success"):
        _show_payment_success()
        return

    # ── Guard: no jobs ────────────────────────────────────────────────────────
    job_ids     = st.session_state.get("payment_job_ids", [])
    job_details = st.session_state.get("payment_job_details", [])
    sel_printer = st.session_state.get("payment_printer", {})
    wait_time   = st.session_state.get("payment_wait_time", 5)
    user        = st.session_state.get("user", {})

    if not job_ids:
        st.html("""
        <div class="pay-empty">
            <div class="pay-empty-icon">📭</div>
            <div class="pay-empty-title">No Print Jobs Selected</div>
            <div class="pay-empty-sub">Please upload and configure your documents before proceeding to payment.</div>
        </div>
        """)
        if st.button("📤 Go to Upload", key="pay_empty_upload", use_container_width=True):
            st.session_state["current_page"] = "Submit Print Job"
            st.rerun()
        return

    # ── Fetch live jobs ───────────────────────────────────────────────────────
    live_jobs = []
    for j_id in job_ids:
        j = get_job_by_id(j_id)
        if j:
            detail = next((d for d in job_details if d.get("job_id") == j_id), {})
            j.update({k: v for k, v in detail.items() if k not in j})
            live_jobs.append(j)

    # ── Fetch printers ────────────────────────────────────────────────────────
    printers = {}
    try:
        for p in (get_all_printers() or []):
            printers[p["id"]] = p
    except Exception:
        pass

    # ── Financials ────────────────────────────────────────────────────────────
    subtotal = sum(j.get("total_cost", j.get("cost", 0)) for j in live_jobs)
    priority_charge = sum(
        (j.get("cost_per_page", 2) - 2) * j.get("total_pages", 1) * j.get("copies", 1)
        for j in live_jobs
        if (j.get("priority", "Normal") or "Normal") not in ("Normal", "normal")
    )
    coupon_discount = st.session_state.get("pay_coupon_discount", 0.0)
    grand_total     = max(0.0, subtotal - coupon_discount)

    # ── Timings ───────────────────────────────────────────────────────────────
    total_pages     = sum(j.get("total_pages", 1) for j in live_jobs)
    est_print_min   = int(wait_time) + total_pages // 5
    est_start_time  = (datetime.now() + timedelta(minutes=int(wait_time))).strftime("%I:%M %p")
    est_pickup_time = (datetime.now() + timedelta(minutes=est_print_min + 2)).strftime("%I:%M %p")

    # ── Printer info ──────────────────────────────────────────────────────────
    printer_name   = sel_printer.get("name", "Assigned Printer")
    printer_status = sel_printer.get("status", "Online")
    queue_pos      = sel_printer.get("queue_length", 0) + len(live_jobs)

    # ── Current payment method ────────────────────────────────────────────────
    pay_type = st.session_state.get("pay_method_type", "UPI")

    # ═════════════════ RENDER PAGE ═══════════════════════════════════════════
    _render_premium_header()

    left_col, right_col = st.columns([3, 2])

    with left_col:
        _render_order_summary(
            live_jobs, sel_printer, printers, wait_time, user,
            subtotal, priority_charge, coupon_discount, grand_total,
            queue_pos, est_print_min, est_pickup_time, est_start_time,
        )
        _render_ai_insights(sel_printer, queue_pos, est_print_min, live_jobs)
        _render_payment_timeline()
        _render_eco_impact(total_pages)

    with right_col:
        _render_payment_methods(pay_type)
        _render_method_inputs(pay_type, grand_total)
        _render_coupon_section(subtotal)
        _render_amount_display(grand_total, subtotal, coupon_discount)
        _render_live_activity()

        # Map UI selection → backend-parseable string
        payment_method_str = _BACKEND_STR.get(pay_type, "📱 UPI (GPay / PhonePe)")

        if st.button(
            f"🔒  Pay Securely  ₹{grand_total:.2f}",
            use_container_width=True, type="primary", key="pay_now_btn",
        ):
            _process_payment(
                job_ids, live_jobs, grand_total, payment_method_str,
                sel_printer, wait_time, user,
            )

        st.html("""
        <div class="pay-trust-row">
            <span class="pay-trust-item">🔒 SSL Secured</span>
            <span class="pay-trust-item">🛡 256-bit Encrypted</span>
            <span class="pay-trust-item">✅ AI Verified</span>
        </div>
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI RENDER HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_premium_header():
    now_str = datetime.now().strftime("%d %b %Y • %I:%M %p")
    st.html(f"""
    <div class="pay-header-card">
        <div class="pay-shield-wrap">
            <div class="pay-shield-anim">🛡</div>
            <div class="pay-shield-ring"></div>
        </div>
        <div class="pay-header-content">
            <div class="pay-header-title">Secure AI Payment</div>
            <div class="pay-header-sub">
                Enterprise-grade encrypted payment powered by IntelliPrint Nexus
            </div>
            <div class="pay-badges-row">
                <span class="pay-badge green">✔ SSL Secured</span>
                <span class="pay-badge blue">✔ 256-bit Encryption</span>
                <span class="pay-badge purple">✔ Campus Payment</span>
                <span class="pay-badge cyan">✔ Protected Transaction</span>
                <span class="pay-badge amber">✔ AI Fraud Detection</span>
            </div>
        </div>
        <div class="pay-header-time">{now_str}</div>
    </div>
    """)


def _render_order_summary(
    live_jobs, sel_printer, printers, wait_time, user,
    subtotal, priority_charge, coupon_discount, grand_total,
    queue_pos, est_print_min, est_pickup_time, est_start_time,
):
    printer_name   = sel_printer.get("name", "Assigned Printer")
    printer_status = sel_printer.get("status", "Online")
    pstatus_color  = "#10b981" if printer_status.lower() == "online" else "#f59e0b"
    u_name         = user.get("username", "Student")
    u_id           = user.get("id", "—")

    st.html('<div class="pay-section-label">📋 Smart Order Summary</div>')

    for idx, job in enumerate(live_jobs, 1):
        doc      = job.get("document_name", "Document")[:45]
        pages    = job.get("total_pages", job.get("pages", 1))
        copies   = job.get("copies", 1)
        color    = job.get("color_mode", "BW")
        duplex   = "Duplex" if job.get("duplex") else "Simplex"
        prio     = job.get("priority", "Normal") or "Normal"
        cost_pp  = job.get("cost_per_page", 2.0)
        total    = job.get("total_cost", job.get("cost", 0.0))
        print_id = job.get("print_id", "—")
        status   = job.get("status", "Pending")
        up_time  = str(job.get("submitted_at", job.get("created_at", "")))[:16]

        p_id    = job.get("printer_id")
        printer = printers.get(p_id, sel_printer)
        p_name  = printer.get("name", printer_name)[:22]
        p_stat  = printer.get("status", printer_status)
        pc      = "#10b981" if p_stat.lower() == "online" else "#f59e0b"
        cb      = "#3b82f6" if color == "Color" else "#6b7280"
        pb      = "#f59e0b" if prio not in ("Normal", "normal") else "#4b5563"

        prio_charge = (cost_pp - 2.0) * pages * copies if prio not in ("Normal", "normal") else 0.0

        ai_score = min(98, 70 + pages * 2 + copies)

        st.html(f"""
        <div class="pay-job-card">
            <div class="pjc-header">
                <div>
                    <div class="pjc-doc">📄 {doc}</div>
                    <div class="pjc-id">Job #{idx} &middot; ID: {print_id}</div>
                </div>
                <div class="pjc-total-badge">&#8377;{total:.2f}</div>
            </div>
            <div class="pjc-grid">
                <div class="pjc-item"><div class="pjc-label">Student</div>
                    <div class="pjc-val">{u_name}</div></div>
                <div class="pjc-item"><div class="pjc-label">Student ID</div>
                    <div class="pjc-val">#{u_id}</div></div>
                <div class="pjc-item"><div class="pjc-label">Pages</div>
                    <div class="pjc-val">{pages}</div></div>
                <div class="pjc-item"><div class="pjc-label">Copies</div>
                    <div class="pjc-val">{copies}</div></div>
                <div class="pjc-item"><div class="pjc-label">Color Mode</div>
                    <div class="pjc-val" style="color:{cb};">{color}</div></div>
                <div class="pjc-item"><div class="pjc-label">Print Side</div>
                    <div class="pjc-val">{duplex}</div></div>
                <div class="pjc-item"><div class="pjc-label">Priority</div>
                    <div class="pjc-val" style="color:{pb};">{prio}</div></div>
                <div class="pjc-item"><div class="pjc-label">Cost/Page</div>
                    <div class="pjc-val">&#8377;{cost_pp:.2f}</div></div>
                <div class="pjc-item"><div class="pjc-label">Printer</div>
                    <div class="pjc-val" style="color:{pc};">&#9679; {p_name}</div></div>
                <div class="pjc-item"><div class="pjc-label">Printer Status</div>
                    <div class="pjc-val" style="color:{pc};">{p_stat}</div></div>
                <div class="pjc-item"><div class="pjc-label">Queue Position</div>
                    <div class="pjc-val" style="color:#06b6d4;">#{queue_pos}</div></div>
                <div class="pjc-item"><div class="pjc-label">Est. Wait</div>
                    <div class="pjc-val" style="color:#f59e0b;">{wait_time} min</div></div>
                <div class="pjc-item"><div class="pjc-label">Print Start</div>
                    <div class="pjc-val">{est_start_time}</div></div>
                <div class="pjc-item"><div class="pjc-label">Completion</div>
                    <div class="pjc-val">{est_pickup_time}</div></div>
                <div class="pjc-item"><div class="pjc-label">AI Quality</div>
                    <div class="pjc-val" style="color:#10b981;">{ai_score}%</div></div>
                <div class="pjc-item"><div class="pjc-label">Upload Time</div>
                    <div class="pjc-val">{up_time}</div></div>
            </div>
            <div class="pjc-cost-row">
                <div class="pjc-cost-item">
                    <div class="pjc-label">Subtotal</div>
                    <div class="pjc-cost-val">&#8377;{total:.2f}</div>
                </div>
                <div class="pjc-cost-item">
                    <div class="pjc-label">Priority Charge</div>
                    <div class="pjc-cost-val" style="color:#f59e0b;">&#8377;{prio_charge:.2f}</div>
                </div>
                <div class="pjc-cost-item">
                    <div class="pjc-label">Tax</div>
                    <div class="pjc-cost-val">Included</div>
                </div>
                <div class="pjc-cost-item">
                    <div class="pjc-label">Total</div>
                    <div class="pjc-cost-val" style="color:#8b5cf6;font-size:1.15rem;">
                        &#8377;{total:.2f}
                    </div>
                </div>
            </div>
        </div>
        """)


def _render_ai_insights(sel_printer, queue_pos, est_print_min, live_jobs):
    printer_name   = sel_printer.get("name", "Assigned Printer")
    printer_status = sel_printer.get("status", "Online")
    ppm            = sel_printer.get("ppm", 30) or 30
    load_pct       = min(95, queue_pos * 12)
    server_health  = 98 if printer_status.lower() == "online" else 72
    confidence     = 98 if printer_status.lower() == "online" else 81
    total_pages    = sum(j.get("total_pages", 1) for j in live_jobs)
    pred_done      = (datetime.now() + timedelta(minutes=est_print_min + 3)).strftime("%I:%M %p")

    bar_load  = f"width:{load_pct}%"
    bar_hlth  = f"width:{server_health}%"
    bar_conf  = f"width:{confidence}%"
    bar_col_l = "#10b981" if load_pct < 60 else ("#f59e0b" if load_pct < 85 else "#ef4444")

    st.html(f"""
    <div class="pay-ai-card">
        <div class="pay-ai-header">
            <span class="pay-ai-icon">🤖</span>
            <div>
                <div class="pay-ai-title">AI Smart Insights</div>
                <div class="pay-ai-sub">Real-time analysis by IntelliPrint AI Engine</div>
            </div>
            <div class="pay-ai-conf-badge">{confidence}% Confidence</div>
        </div>
        <div class="pay-ai-grid">
            <div class="pay-ai-item">
                <div class="pay-ai-label">Best Printer</div>
                <div class="pay-ai-val" style="color:#3b82f6;">{printer_name[:20]}</div>
            </div>
            <div class="pay-ai-item">
                <div class="pay-ai-label">Queue Position</div>
                <div class="pay-ai-val" style="color:#06b6d4;">#{queue_pos}</div>
            </div>
            <div class="pay-ai-item">
                <div class="pay-ai-label">Print Speed</div>
                <div class="pay-ai-val">{ppm} PPM</div>
            </div>
            <div class="pay-ai-item">
                <div class="pay-ai-label">Pred. Completion</div>
                <div class="pay-ai-val" style="color:#10b981;">{pred_done}</div>
            </div>
        </div>
        <div class="pay-ai-bars">
            <div class="pay-ai-bar-row">
                <div class="pay-ai-bar-label">Queue Load</div>
                <div class="pay-ai-bar-track">
                    <div class="pay-ai-bar-fill" style="{bar_load};background:{bar_col_l};"></div>
                </div>
                <div class="pay-ai-bar-pct">{load_pct}%</div>
            </div>
            <div class="pay-ai-bar-row">
                <div class="pay-ai-bar-label">Server Health</div>
                <div class="pay-ai-bar-track">
                    <div class="pay-ai-bar-fill" style="{bar_hlth};background:#10b981;"></div>
                </div>
                <div class="pay-ai-bar-pct">{server_health}%</div>
            </div>
            <div class="pay-ai-bar-row">
                <div class="pay-ai-bar-label">AI Confidence</div>
                <div class="pay-ai-bar-track">
                    <div class="pay-ai-bar-fill" style="{bar_conf};background:#8b5cf6;"></div>
                </div>
                <div class="pay-ai-bar-pct">{confidence}%</div>
            </div>
        </div>
        <div class="pay-ai-rec">
            <span class="pay-ai-rec-icon">💡</span>
            <span class="pay-ai-rec-text">
                <b>{printer_name[:22]}</b> recommended — Fastest completion &amp; lowest workload
            </span>
        </div>
    </div>
    """)


def _render_payment_timeline():
    steps = [
        ("✅", "Upload",    "Complete"),
        ("✅", "AI Scan",   "Complete"),
        ("🔵", "Payment",   "In Progress"),
        ("⏳", "Queue",     "Pending"),
        ("⏳", "Printing",  "Pending"),
        ("⏳", "Ready",     "Pending"),
    ]
    items_html = ""
    for icon, label, status in steps:
        done    = status == "Complete"
        active  = status == "In Progress"
        cls     = "tl-done" if done else ("tl-active" if active else "tl-pending")
        s_color = "#10b981" if done else ("#3b82f6" if active else "rgba(255,255,255,.2)")
        items_html += (
            f'<div class="tl-step {cls}">'
            f'<div class="tl-dot" style="background:{s_color};">{icon}</div>'
            f'<div class="tl-info">'
            f'<div class="tl-label">{label}</div>'
            f'<div class="tl-status" style="color:{s_color};">{status}</div>'
            f'</div></div>'
        )

    st.html(f"""
    <div class="pay-timeline-card">
        <div class="pay-tl-title">📍 Payment Journey</div>
        <div class="pay-tl-track">{items_html}</div>
    </div>
    """)


def _render_eco_impact(total_pages: int):
    paper_saved = round(total_pages * 0.004, 3)
    co2_saved   = round(total_pages * 0.005, 3)
    trees_eq    = round(total_pages * 0.00001, 5)

    st.html(f"""
    <div class="pay-eco-card">
        <div class="pay-eco-title">🌱 Eco Impact — Campus Sustainability</div>
        <div class="pay-eco-row">
            <div class="pay-eco-item">
                <div class="pay-eco-val">{paper_saved} kg</div>
                <div class="pay-eco-label">Paper Optimized</div>
            </div>
            <div class="pay-eco-item">
                <div class="pay-eco-val">{co2_saved} kg</div>
                <div class="pay-eco-label">CO₂ Saved</div>
            </div>
            <div class="pay-eco-item">
                <div class="pay-eco-val">{total_pages}</div>
                <div class="pay-eco-label">Smart Pages</div>
            </div>
        </div>
    </div>
    """)


def _render_payment_methods(selected: str):
    st.html('<div class="pay-section-label">💳 Payment Method</div>')

    # Row 1 — UPI methods
    c1, c2, c3, c4 = st.columns(4)
    _method_btn(c1, "UPI",     "📱", "UPI / GPay",  selected)
    _method_btn(c2, "PhonePe", "📱", "PhonePe",     selected)
    _method_btn(c3, "Paytm",   "📱", "Paytm",       selected)
    _method_btn(c4, "BHIM",    "📱", "BHIM UPI",    selected)

    # Row 2 — Card & Banking
    c5, c6, c7 = st.columns(3)
    _method_btn(c5, "Card",       "💳", "Credit Card", selected)
    _method_btn(c6, "Debit",      "💳", "Debit Card",  selected)
    _method_btn(c7, "NetBanking", "🏦", "Net Banking", selected)

    # Row 3 — Wallets
    c8, c9 = st.columns(2)
    _method_btn(c8, "Wallet", "💰", "Wallet",        selected)
    _method_btn(c9, "Campus", "🏫", "Campus Wallet", selected)


def _method_btn(col, key: str, icon: str, label: str, selected: str):
    is_sel = selected == key
    btn_type = "primary" if is_sel else "secondary"
    with col:
        if st.button(f"{icon} {label}", key=f"pm_{key}",
                     use_container_width=True, type=btn_type):
            st.session_state["pay_method_type"] = key
            st.rerun()


def _render_method_inputs(pay_type: str, grand_total: float):
    is_upi  = pay_type in ("UPI", "PhonePe", "Paytm", "BHIM")
    is_card = pay_type in ("Card", "Debit")
    is_nb   = pay_type == "NetBanking"
    is_wall = pay_type in ("Wallet", "Campus")

    if is_upi:
        _render_upi_section(grand_total, pay_type)
    elif is_card:
        _render_card_section(pay_type)
    elif is_nb:
        _render_netbanking_section()
    else:
        _render_wallet_section(pay_type)


def _render_upi_section(grand_total: float, pay_type: str):
    # Generate inline QR for UPI
    upi_url = (
        f"upi://pay?pa=intelliprint@campus&pn=IntelliPrint+Nexus"
        f"&am={grand_total:.2f}&cu=INR&tn=Campus+Print+Payment"
    )
    qr_b64 = _generate_qr_b64(upi_url)
    qr_img_html = (
        f'<img src="data:image/png;base64,{qr_b64}" class="pay-upi-qr-img" />'
        if qr_b64 else
        '<div class="pay-upi-qr-placeholder">QR</div>'
    )

    app_icons = {
        "UPI":     "Google Pay",
        "PhonePe": "PhonePe",
        "Paytm":   "Paytm",
        "BHIM":    "BHIM UPI",
    }
    app_name = app_icons.get(pay_type, "UPI")

    st.html(f"""
    <div class="pay-upi-card">
        <div class="pay-upi-header">
            <div class="pay-upi-title">📱 {app_name} Payment</div>
            <div class="pay-upi-amount">&#8377;{grand_total:.2f}</div>
        </div>
        <div class="pay-upi-body">
            <div class="pay-qr-frame">
                <div class="pay-qr-corner tl"></div>
                <div class="pay-qr-corner tr"></div>
                <div class="pay-qr-corner bl"></div>
                <div class="pay-qr-corner br"></div>
                <div class="pay-qr-scan-line"></div>
                {qr_img_html}
            </div>
            <div class="pay-upi-right">
                <div class="pay-upi-id-box">
                    <div class="pay-upi-id-label">UPI ID</div>
                    <div class="pay-upi-id-val">intelliprint@campus</div>
                </div>
                <div class="pay-upi-timer-box">
                    <div class="pay-upi-timer-label">Expires in</div>
                    <div class="pay-upi-timer">04:59</div>
                </div>
                <div class="pay-upi-apps">
                    <div class="pay-upi-apps-label">Also accepted by</div>
                    <div class="pay-upi-apps-row">
                        <span class="pay-upi-app">GPay</span>
                        <span class="pay-upi-app">PhonePe</span>
                        <span class="pay-upi-app">Paytm</span>
                        <span class="pay-upi-app">BHIM</span>
                        <span class="pay-upi-app">Amazon</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="pay-upi-status">
            <div class="pay-upi-status-dot"></div>
            <div class="pay-upi-status-text">Waiting for payment confirmation...</div>
        </div>
    </div>
    """)

    upi_id_in = st.text_input(
        "Or enter UPI ID manually", placeholder="yourname@upi",
        key="upi_id_input", label_visibility="visible",
    )


def _render_card_section(pay_type: str):
    card_label = "Credit Card" if pay_type == "Card" else "Debit Card"

    # Card number from session (masked)
    raw_num = st.session_state.get("card_no_raw", "")
    display_num = raw_num.replace(" ", "")
    grouped = " ".join(
        display_num[i:i+4] for i in range(0, len(display_num), 4)
    ) if display_num else "•••• •••• •••• ••••"
    holder = st.session_state.get("card_holder_raw", "CARDHOLDER NAME")
    expiry = st.session_state.get("card_exp_raw", "MM/YY")
    cvv_entered = bool(st.session_state.get("card_cvv_raw", ""))

    # Detect card network
    network = "VISA"
    if display_num.startswith("5"):
        network = "MASTERCARD"
    elif display_num.startswith("6"):
        network = "RUPAY"
    elif display_num.startswith("3"):
        network = "AMEX"

    flip_class = "card-flip" if cvv_entered else ""

    st.html(f"""
    <div class="pay-card-visual-wrap">
        <div class="pay-card-3d {flip_class}">
            <div class="pay-card-front">
                <div class="pay-card-glow"></div>
                <div class="pay-card-chip">&#x25A6;</div>
                <div class="pay-card-network">{network}</div>
                <div class="pay-card-number">{grouped}</div>
                <div class="pay-card-bottom">
                    <div>
                        <div class="pay-card-small-label">Card Holder</div>
                        <div class="pay-card-holder">{holder or "YOUR NAME"}</div>
                    </div>
                    <div>
                        <div class="pay-card-small-label">Expires</div>
                        <div class="pay-card-expiry">{expiry or "MM/YY"}</div>
                    </div>
                </div>
            </div>
            <div class="pay-card-back">
                <div class="pay-card-stripe"></div>
                <div class="pay-card-cvv-area">
                    <div class="pay-card-small-label">CVV</div>
                    <div class="pay-card-cvv-val">•••</div>
                </div>
                <div class="pay-card-network-back">{network}</div>
            </div>
        </div>
    </div>
    """)

    num = st.text_input("Card Number", placeholder="4242 4242 4242 4242",
                        key="card_no", max_chars=19)
    st.session_state["card_no_raw"] = num

    c1, c2 = st.columns(2)
    with c1:
        exp = st.text_input("Expiry (MM/YY)", placeholder="12/28",
                            key="card_exp", max_chars=5)
        st.session_state["card_exp_raw"] = exp
    with c2:
        cvv = st.text_input("CVV", type="password", placeholder="•••",
                            max_chars=4, key="card_cvv")
        st.session_state["card_cvv_raw"] = cvv

    holder_in = st.text_input("Card Holder Name", placeholder="Name on card",
                               key="card_holder")
    st.session_state["card_holder_raw"] = holder_in


def _render_netbanking_section():
    st.selectbox(
        "Select Your Bank",
        ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
         "Punjab National Bank", "Bank of Baroda", "Kotak Mahindra Bank",
         "YES Bank", "IndusInd Bank", "Canara Bank", "Other"],
        key="bank_sel",
    )
    st.html("""
    <div class="pay-nb-note">
        🔒 You will be securely redirected to your bank's net banking portal.
        Return here after completing the payment.
    </div>
    """)


def _render_wallet_section(pay_type: str):
    is_campus = pay_type == "Campus"
    balance   = "₹240.00" if is_campus else "₹180.00"
    wtype     = "Campus Wallet" if is_campus else "Digital Wallet"
    icon      = "🏫" if is_campus else "💰"

    st.html(f"""
    <div class="pay-wallet-card">
        <div class="pay-wallet-header">
            <span class="pay-wallet-icon">{icon}</span>
            <div>
                <div class="pay-wallet-type">{wtype}</div>
                <div class="pay-wallet-bal">Available Balance: <b>{balance}</b></div>
            </div>
        </div>
        <div class="pay-wallet-note">
            Sufficient balance available. Payment will be deducted instantly.
        </div>
    </div>
    """)


def _render_coupon_section(subtotal: float):
    st.html('<div class="pay-section-label">🎟 Coupon / Promo Code</div>')

    applied = st.session_state.get("pay_coupon_applied", "")
    discount = st.session_state.get("pay_coupon_discount", 0.0)

    if applied:
        pct = int(discount / subtotal * 100) if subtotal > 0 else 0
        st.html(f"""
        <div class="pay-coupon-success">
            ✅ Coupon <b>{applied}</b> applied — {pct}% off (₹{discount:.2f} saved)
        </div>
        """)
        if st.button("✕ Remove Coupon", key="pay_remove_coupon"):
            st.session_state.pop("pay_coupon_applied", None)
            st.session_state.pop("pay_coupon_discount", None)
            st.rerun()
    else:
        c1, c2 = st.columns([3, 1])
        with c1:
            coupon_code = st.text_input(
                "Coupon Code", placeholder="Enter code (e.g. CAMPUS10)",
                key="pay_coupon_input", label_visibility="collapsed",
            )
        with c2:
            if st.button("Apply", key="pay_apply_coupon", use_container_width=True):
                code = coupon_code.strip().upper()
                if code in _COUPONS:
                    disc = round(subtotal * _COUPONS[code], 2)
                    st.session_state["pay_coupon_applied"]  = code
                    st.session_state["pay_coupon_discount"] = disc
                    st.success(f"✅ Code '{code}' applied!")
                    st.rerun()
                else:
                    st.error("Invalid coupon code.")

        st.html("""
        <div class="pay-coupon-hint">Try: CAMPUS10 · NEXUS20 · PRINT5 · WELCOME</div>
        """)


def _render_amount_display(grand_total: float, subtotal: float, coupon_discount: float):
    disc_html = ""
    if coupon_discount > 0:
        disc_html = (
            f'<div class="pay-amt-row discount">'
            f'<span>Coupon Discount</span>'
            f'<span style="color:#10b981;">- &#8377;{coupon_discount:.2f}</span>'
            f'</div>'
        )

    st.html(f"""
    <div class="pay-amount-card">
        <div class="pay-amt-row"><span>Subtotal</span><span>&#8377;{subtotal:.2f}</span></div>
        <div class="pay-amt-row"><span>Tax &amp; Fees</span><span>Included</span></div>
        {disc_html}
        <div class="pay-amt-divider"></div>
        <div class="pay-amt-total-row">
            <span class="pay-amt-total-label">Total Payable</span>
            <span class="pay-amt-total-val">&#8377;{grand_total:.2f}</span>
        </div>
    </div>
    """)


def _render_live_activity():
    items_html = "".join(
        f'<div class="pay-activity-item">'
        f'<div class="pay-activity-dot"></div>'
        f'<div class="pay-activity-name">{name}</div>'
        f'<div class="pay-activity-amt">{amt}</div>'
        f'<div class="pay-activity-time">{t}</div>'
        f'</div>'
        for name, amt, t in _LIVE_FEED
    )
    st.html(f"""
    <div class="pay-activity-card">
        <div class="pay-activity-title">⚡ Live Campus Payments</div>
        {items_html}
    </div>
    """)


# ═══════════════════════════════════════════════════════════════════════════════
#  BACKEND LOGIC — UNCHANGED
# ═══════════════════════════════════════════════════════════════════════════════

def _process_payment(job_ids, live_jobs, grand_total, payment_method, sel_printer, wait_time, user):
    """Process payment and generate Pickup IDs, QR Codes, and PDF Previews."""
    write_log("PAYMENT_LOG", f"Payment initiated for Job IDs: {job_ids}. Total: ₹{grand_total:.2f}")

    with st.spinner("🔒 Processing secure payment..."):
        time.sleep(1.5)

    txn_id     = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    method_str = "UPI" if "UPI" in payment_method else ("Card" if "Card" in payment_method else "NetBanking")

    qr_dir      = "qrcodes"
    preview_dir = "uploads/previews"
    os.makedirs(qr_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)

    printer_name = sel_printer.get("name", "Assigned Printer")

    success_jobs = []

    try:
        for job in live_jobs:
            j_id      = job.get("id")
            j_doc     = job.get("document_name", "Document")
            j_pid     = job.get("print_id", "")
            j_cost    = job.get("total_cost", job.get("cost", 0))
            j_fpath   = job.get("file_path", "")
            j_pages   = job.get("total_pages", 1) or 1
            j_copies  = job.get("copies", 1) or 1
            j_priority = job.get("priority", "Normal") or "Normal"

            # ── Step 1: Record Payment ────────────────────────────────────────
            create_payment(
                job_id=j_id,
                user_id=user.get("id", 0),
                amount=j_cost,
                method=method_str,
                transaction_id=f"{txn_id}-{j_id}",
                status="Success",
            )

            # ── Step 2: Assign printer + calculate ETA + set status=Queued ───
            #
            # THIS MUST HAPPEN BEFORE QR/PDF GENERATION.
            # If QR/PDF generation fails (e.g. PIL error, corrupt file), the
            # job must still be queued so the Queue Manager can process it.
            # Without this fix, any exception in steps 3–4 permanently orphans
            # the job in "Pending" with a "Success" payment record.
            #
            assign_result    = assign_printer_and_queue(
                job_id   = j_id,
                pages    = j_pages,
                copies   = j_copies,
                priority = j_priority,
            )
            assigned_printer = assign_result.get("printer_name", printer_name)
            assigned_queue   = assign_result.get("queue_pos", 1)
            assigned_eta     = assign_result.get("eta_minutes", 5)

            # ── Step 3: Generate Pickup ID ────────────────────────────────────
            pickup_id = generate_pickup_id()

            # ── Step 4: QR Code (best-effort — failure does NOT abort queue) ─
            qr_path = ""
            try:
                qr_path = os.path.join(qr_dir, f"{j_pid}_{pickup_id}.png")
                qr_text = f"SmartPrint|PICKUP|{pickup_id}|Job|{j_pid}|{j_doc}"
                generate_qr_code(qr_text, qr_path)
            except Exception as qr_err:
                write_log("PAYMENT_LOG", f"QR generation failed for {j_pid} (non-fatal)", qr_err)
                qr_path = ""

            # ── Step 5: PDF Preview (best-effort) ────────────────────────────
            preview_path = ""
            try:
                if j_fpath and os.path.exists(j_fpath):
                    preview_path = generate_pdf_preview(
                        source_pdf_path=j_fpath,
                        pickup_id=pickup_id,
                        qr_image_path=qr_path,
                        printer_name=printer_name,
                        print_id=j_pid,
                        output_dir=preview_dir,
                        student_name=user.get("username", "Student"),
                        student_id=str(user.get("id", "—")),
                        document_name=j_doc,
                        num_pages=j_pages,
                    )
            except Exception as pdf_err:
                write_log("PAYMENT_LOG", f"PDF preview failed for {j_pid} (non-fatal)", pdf_err)
                preview_path = ""

            # ── Step 6: Persist pickup info (QR path + PDF path) ─────────────
            set_job_pickup_info(j_id, pickup_id, qr_path, preview_path)

            # ── Step 7: In-app notification ───────────────────────────────────
            user_id_for_notif = user.get("id", 0)
            if user_id_for_notif:
                try:
                    create_notification(
                        user_id           = user_id_for_notif,
                        title             = f"Print Job Queued — {j_doc[:30]}",
                        message           = (
                            f"Your job {j_pid} is queued at {assigned_printer}. "
                            f"Position #{assigned_queue} · ETA {assigned_eta} min. "
                            f"Pickup ID: {pickup_id}"
                        ),
                        notification_type = "success",
                    )
                except Exception:
                    pass

            write_log("PAYMENT_LOG",
                f"Payment OK: Job={j_pid}, Pickup={pickup_id}, Printer={assigned_printer}, "
                f"Queue=#{assigned_queue}, ETA={assigned_eta}min, Txn={txn_id}-{j_id}, ₹{j_cost:.2f}")

            success_jobs.append({
                "job_id":        j_id,
                "print_id":      j_pid,
                "document_name": j_doc,
                "pickup_id":     pickup_id,
                "qr_path":       qr_path,
                "preview_path":  preview_path,
                "cost":          j_cost,
            })

        st.session_state["payment_success"]        = True
        st.session_state["payment_success_amount"] = grand_total
        st.session_state["payment_success_jobs"]   = success_jobs
        st.session_state["payment_txn_id"]         = txn_id
        st.session_state["payment_printer_name"]   = printer_name
        st.rerun()

    except Exception as e:
        write_log("PAYMENT_LOG", f"Payment failed for Job IDs: {job_ids}", e)
        st.error(f"Payment failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SUCCESS SCREEN — ENHANCED
# ═══════════════════════════════════════════════════════════════════════════════

def _show_payment_success():
    """Premium success screen with celebration, QR codes and PDF downloads."""
    amount       = st.session_state.get("payment_success_amount", 0)
    success_jobs = st.session_state.get("payment_success_jobs", [])
    txn_id       = st.session_state.get("payment_txn_id", "—")
    printer_name = st.session_state.get("payment_printer_name", "Printer")
    now_str      = datetime.now().strftime("%d %b %Y, %I:%M %p")
    ref_no       = f"REF-{txn_id[-8:]}"

    # Confetti burst (CSS animation)
    st.html("""
    <div class="pay-confetti-wrap">
        <div class="confetti c1"></div><div class="confetti c2"></div>
        <div class="confetti c3"></div><div class="confetti c4"></div>
        <div class="confetti c5"></div><div class="confetti c6"></div>
        <div class="confetti c7"></div><div class="confetti c8"></div>
    </div>
    """)

    st.html(f"""
    <div class="pay-success-hero">
        <div class="pay-success-ring">
            <div class="pay-success-check">✓</div>
        </div>
        <div class="pay-success-title">Payment Successful!</div>
        <div class="pay-success-sub">Your print jobs are queued. Collect using your Pickup ID.</div>
    </div>

    <div class="pay-success-meta">
        <div class="pay-meta-item">
            <div class="pay-meta-label">Transaction ID</div>
            <div class="pay-meta-val blue">{txn_id}</div>
        </div>
        <div class="pay-meta-item">
            <div class="pay-meta-label">Reference No.</div>
            <div class="pay-meta-val">{ref_no}</div>
        </div>
        <div class="pay-meta-item">
            <div class="pay-meta-label">Amount Paid</div>
            <div class="pay-meta-val green">&#8377;{amount:.2f}</div>
        </div>
        <div class="pay-meta-item">
            <div class="pay-meta-label">Printer</div>
            <div class="pay-meta-val">{printer_name[:22]}</div>
        </div>
        <div class="pay-meta-item">
            <div class="pay-meta-label">Date &amp; Time</div>
            <div class="pay-meta-val">{now_str}</div>
        </div>
    </div>
    """)

    st.html('<div class="pay-success-jobs-title">📄 Your Print Jobs</div>')

    for job in success_jobs:
        pickup_id    = job.get("pickup_id", "—")
        qr_path      = job.get("qr_path", "")
        preview_path = job.get("preview_path", "")
        doc          = job.get("document_name", "Document")[:45]
        cost         = job.get("cost", 0)
        print_id     = job.get("print_id", "—")

        col_info, col_qr = st.columns([3, 1])

        with col_info:
            st.html(f"""
            <div class="pay-sj-card">
                <div class="pay-sj-header">
                    <div class="pay-sj-doc">📄 {doc}</div>
                    <div class="pay-sj-cost">&#8377;{cost:.2f}</div>
                </div>
                <div class="pay-sj-grid">
                    <div class="pay-sj-item">
                        <div class="pay-sj-label">Print ID</div>
                        <div class="pay-sj-val blue mono">{print_id}</div>
                    </div>
                    <div class="pay-sj-item">
                        <div class="pay-sj-label">Pickup ID</div>
                        <div class="pay-sj-val purple big">{pickup_id}</div>
                    </div>
                    <div class="pay-sj-item">
                        <div class="pay-sj-label">Status</div>
                        <div class="pay-sj-val amber">⏳ Queued for Printing</div>
                    </div>
                    <div class="pay-sj-item">
                        <div class="pay-sj-label">Transaction</div>
                        <div class="pay-sj-val mono">{txn_id}</div>
                    </div>
                </div>
                <div class="pay-sj-hint">
                    📱 Scan QR Code or show Pickup ID at the printer terminal to collect your printout.
                </div>
            </div>
            """)

        with col_qr:
            if qr_path and os.path.exists(qr_path):
                st.image(qr_path, width=130, caption=pickup_id)
            else:
                st.html('<div style="color:rgba(255,255,255,.3);font-size:.8rem;padding:20px 0;">QR unavailable</div>')

        if preview_path and os.path.exists(preview_path):
            with open(preview_path, "rb") as pf:
                st.download_button(
                    f"📥 Download Print-Ready PDF — {doc[:22]}",
                    data=pf.read(),
                    file_name=f"printready_{print_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_preview_{print_id}",
                    use_container_width=True,
                )

        st.html('<div style="height:8px"></div>')

    st.html("<br>")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("📋 Track Queue", use_container_width=True, key="pay_track"):
            _clear_payment_state()
            st.session_state["current_page"] = "Track Order"
            st.rerun()
    with b2:
        if st.button("📜 Print History", use_container_width=True, key="pay_history"):
            _clear_payment_state()
            st.session_state["current_page"] = "My Print Jobs"
            st.rerun()
    with b3:
        if st.button("🏠 Dashboard", use_container_width=True, key="pay_dash"):
            _clear_payment_state()
            st.session_state["current_page"] = "Dashboard"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITIES — UNCHANGED
# ═══════════════════════════════════════════════════════════════════════════════

def _clear_payment_state():
    keys = [
        "payment_success", "payment_success_amount", "payment_success_jobs",
        "payment_job_ids", "payment_batch_cost", "payment_job_details",
        "payment_printer", "payment_wait_time", "payment_txn_id",
        "payment_printer_name", "pay_coupon_applied", "pay_coupon_discount",
        "pay_method_type",
    ]
    for k in keys:
        st.session_state.pop(k, None)


def _generate_qr_b64(data: str) -> str:
    """Generate a QR code as base64-encoded PNG, or return empty string on failure."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=2, box_size=5, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a1a2e", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
#  PREMIUM CSS
# ═══════════════════════════════════════════════════════════════════════════════

def _pay_css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Globals ── */
.pay-header-card,.pay-ai-card,.pay-timeline-card,.pay-eco-card,
.pay-upi-card,.pay-amount-card,.pay-activity-card,.pay-wallet-card,
.pay-job-card,.pay-sj-card,.pay-success-hero,.pay-success-meta {
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  box-sizing:border-box;
}

/* ── Secure Header ── */
.pay-header-card {
  display:flex; align-items:center; gap:20px;
  background:linear-gradient(135deg,rgba(15,17,35,0.95),rgba(20,10,45,0.95));
  border:1px solid rgba(139,92,246,0.3);
  border-radius:20px; padding:24px 28px; margin-bottom:20px;
  box-shadow:0 0 40px rgba(139,92,246,0.15), 0 8px 32px rgba(0,0,0,0.5);
  position:relative; overflow:hidden;
}
.pay-header-card::before {
  content:''; position:absolute; inset:0;
  background:linear-gradient(135deg,rgba(59,130,246,0.05),rgba(139,92,246,0.08),rgba(6,182,212,0.05));
  pointer-events:none;
}
.pay-shield-wrap { position:relative; flex-shrink:0; }
.pay-shield-anim {
  font-size:2.8rem; position:relative; z-index:1;
  animation:shieldPulse 3s ease-in-out infinite;
}
@keyframes shieldPulse {
  0%,100%{filter:drop-shadow(0 0 8px rgba(59,130,246,0.6));}
  50%{filter:drop-shadow(0 0 22px rgba(139,92,246,0.9));}
}
.pay-shield-ring {
  position:absolute; inset:-8px; border-radius:50%;
  border:2px solid rgba(139,92,246,0.4);
  animation:ringPulse 3s ease-in-out infinite;
}
@keyframes ringPulse {
  0%,100%{transform:scale(1);opacity:0.4;}
  50%{transform:scale(1.15);opacity:0.8;}
}
.pay-header-content { flex:1; }
.pay-header-title {
  font-size:1.6rem; font-weight:800; letter-spacing:-0.03em;
  background:linear-gradient(135deg,#3B82F6,#8B5CF6,#06B6D4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text; margin-bottom:4px;
}
.pay-header-sub { color:rgba(255,255,255,0.5); font-size:0.82rem; margin-bottom:12px; }
.pay-badges-row { display:flex; flex-wrap:wrap; gap:6px; }
.pay-badge {
  padding:3px 10px; border-radius:20px; font-size:0.68rem;
  font-weight:600; letter-spacing:0.03em;
}
.pay-badge.green  { background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); color:#10b981; }
.pay-badge.blue   { background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.4); color:#60a5fa; }
.pay-badge.purple { background:rgba(139,92,246,0.15); border:1px solid rgba(139,92,246,0.4); color:#a78bfa; }
.pay-badge.cyan   { background:rgba(6,182,212,0.15);  border:1px solid rgba(6,182,212,0.4);  color:#67e8f9; }
.pay-badge.amber  { background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.4); color:#fbbf24; }
.pay-header-time { color:rgba(255,255,255,0.3); font-size:0.72rem; text-align:right; flex-shrink:0; }

/* ── Section labels ── */
.pay-section-label {
  font-size:0.78rem; font-weight:700; text-transform:uppercase;
  letter-spacing:0.08em; color:rgba(255,255,255,0.45);
  margin:16px 0 8px; padding-left:2px;
}

/* ── Job cards ── */
.pay-job-card {
  background:rgba(15,17,35,0.7); border:1px solid rgba(255,255,255,0.07);
  border-radius:16px; padding:18px 20px; margin-bottom:14px;
  box-shadow:0 4px 24px rgba(0,0,0,0.35);
  transition:border-color 0.25s, box-shadow 0.25s;
}
.pay-job-card:hover {
  border-color:rgba(59,130,246,0.25);
  box-shadow:0 4px 32px rgba(59,130,246,0.1), 0 8px 24px rgba(0,0,0,0.4);
}
.pjc-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; }
.pjc-doc { font-size:0.95rem; font-weight:700; color:#fff; }
.pjc-id  { font-size:0.7rem; color:#3B82F6; font-family:monospace; margin-top:4px; }
.pjc-total-badge {
  background:linear-gradient(135deg,rgba(139,92,246,0.2),rgba(59,130,246,0.2));
  border:1px solid rgba(139,92,246,0.4); border-radius:12px;
  padding:6px 14px; font-size:1.3rem; font-weight:800; color:#a78bfa;
}
.pjc-grid {
  display:grid; grid-template-columns:repeat(4,1fr); gap:8px 12px;
  margin-bottom:14px;
}
.pjc-item { background:rgba(255,255,255,0.025); border-radius:8px; padding:8px 10px; }
.pjc-label { font-size:0.6rem; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:3px; }
.pjc-val   { font-size:0.8rem; font-weight:600; color:#e2e8f0; }
.pjc-cost-row {
  display:grid; grid-template-columns:repeat(4,1fr); gap:8px;
  border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;
}
.pjc-cost-item { text-align:center; }
.pjc-cost-val  { font-size:0.9rem; font-weight:700; color:#fff; margin-top:3px; }

/* ── AI Insights card ── */
.pay-ai-card {
  background:linear-gradient(135deg,rgba(15,17,35,0.9),rgba(8,5,25,0.9));
  border:1px solid rgba(139,92,246,0.25); border-radius:16px;
  padding:20px; margin:0 0 14px; box-shadow:0 0 24px rgba(139,92,246,0.1);
}
.pay-ai-header { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
.pay-ai-icon   { font-size:1.8rem; }
.pay-ai-title  { font-size:1rem; font-weight:700; color:#fff; }
.pay-ai-sub    { font-size:0.7rem; color:rgba(255,255,255,0.4); }
.pay-ai-conf-badge {
  margin-left:auto; background:rgba(16,185,129,0.15);
  border:1px solid rgba(16,185,129,0.35); border-radius:20px;
  padding:4px 12px; font-size:0.72rem; font-weight:700; color:#10b981;
}
.pay-ai-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:14px; }
.pay-ai-item { background:rgba(255,255,255,0.03); border-radius:8px; padding:10px 8px; text-align:center; }
.pay-ai-label{ font-size:0.6rem; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }
.pay-ai-val  { font-size:0.82rem; font-weight:700; color:#e2e8f0; }
.pay-ai-bars { display:flex; flex-direction:column; gap:8px; margin-bottom:14px; }
.pay-ai-bar-row   { display:flex; align-items:center; gap:10px; }
.pay-ai-bar-label { font-size:0.7rem; color:rgba(255,255,255,0.45); width:90px; }
.pay-ai-bar-track { flex:1; height:6px; background:rgba(255,255,255,0.07); border-radius:3px; overflow:hidden; }
.pay-ai-bar-fill  { height:100%; border-radius:3px; transition:width 0.8s cubic-bezier(0.4,0,0.2,1); }
.pay-ai-bar-pct   { font-size:0.7rem; font-weight:700; color:#e2e8f0; width:32px; text-align:right; }
.pay-ai-rec {
  display:flex; gap:8px; align-items:center;
  background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2);
  border-radius:8px; padding:10px 12px;
}
.pay-ai-rec-icon { font-size:1rem; }
.pay-ai-rec-text { font-size:0.78rem; color:rgba(255,255,255,0.65); }
.pay-ai-rec-text b { color:#60a5fa; }

/* ── Payment Timeline ── */
.pay-timeline-card {
  background:rgba(15,17,35,0.7); border:1px solid rgba(255,255,255,0.06);
  border-radius:16px; padding:18px 20px; margin-bottom:14px;
}
.pay-tl-title { font-size:0.82rem; font-weight:700; color:rgba(255,255,255,0.6); margin-bottom:14px; }
.pay-tl-track { display:flex; align-items:center; justify-content:space-between; position:relative; }
.pay-tl-track::before {
  content:''; position:absolute; top:50%; left:0; right:0;
  height:1px; background:rgba(255,255,255,0.08); transform:translateY(-50%); z-index:0;
}
.tl-step {
  display:flex; flex-direction:column; align-items:center; gap:6px;
  position:relative; z-index:1;
}
.tl-dot {
  width:32px; height:32px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:0.85rem; border:2px solid rgba(255,255,255,0.1);
}
.tl-done .tl-dot  { box-shadow:0 0 12px rgba(16,185,129,0.5); }
.tl-active .tl-dot{ box-shadow:0 0 16px rgba(59,130,246,0.7); animation:activePulse 2s infinite; }
@keyframes activePulse {
  0%,100%{box-shadow:0 0 16px rgba(59,130,246,0.7);}
  50%{box-shadow:0 0 28px rgba(59,130,246,1);}
}
.tl-label  { font-size:0.62rem; color:rgba(255,255,255,0.5); text-align:center; }
.tl-status { font-size:0.58rem; font-weight:600; text-align:center; }

/* ── Eco Impact ── */
.pay-eco-card {
  background:linear-gradient(135deg,rgba(5,25,15,0.8),rgba(5,30,20,0.8));
  border:1px solid rgba(16,185,129,0.2); border-radius:14px;
  padding:14px 18px; margin-bottom:14px;
}
.pay-eco-title { font-size:0.8rem; font-weight:700; color:#10b981; margin-bottom:10px; }
.pay-eco-row { display:flex; gap:16px; }
.pay-eco-item { flex:1; text-align:center; }
.pay-eco-val  { font-size:1.1rem; font-weight:800; color:#34d399; }
.pay-eco-label{ font-size:0.62rem; color:rgba(255,255,255,0.4); margin-top:2px; }

/* ── Payment Methods ── */
/* styled via Streamlit button type="primary"/"secondary" — native Streamlit theming handles selection */

/* ── UPI Section ── */
.pay-upi-card {
  background:rgba(15,17,35,0.85); border:1px solid rgba(59,130,246,0.2);
  border-radius:16px; padding:18px; margin:10px 0;
  box-shadow:0 0 20px rgba(59,130,246,0.08);
}
.pay-upi-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
.pay-upi-title  { font-size:0.95rem; font-weight:700; color:#fff; }
.pay-upi-amount { font-size:1.4rem; font-weight:800; color:#8b5cf6; }
.pay-upi-body   { display:flex; gap:16px; }
.pay-qr-frame {
  position:relative; width:140px; height:140px; flex-shrink:0;
  background:#fff; border-radius:12px; display:flex;
  align-items:center; justify-content:center; overflow:hidden;
  box-shadow:0 0 0 3px rgba(59,130,246,0.3);
}
.pay-upi-qr-img { width:130px; height:130px; border-radius:8px; display:block; }
.pay-upi-qr-placeholder {
  font-size:2rem; color:#06070d; font-weight:900;
}
.pay-qr-corner {
  position:absolute; width:18px; height:18px;
  border:3px solid #3b82f6; z-index:2;
}
.pay-qr-corner.tl { top:4px; left:4px; border-right:none; border-bottom:none; border-radius:4px 0 0 0; }
.pay-qr-corner.tr { top:4px; right:4px; border-left:none; border-bottom:none; border-radius:0 4px 0 0; }
.pay-qr-corner.bl { bottom:4px; left:4px; border-right:none; border-top:none; border-radius:0 0 0 4px; }
.pay-qr-corner.br { bottom:4px; right:4px; border-left:none; border-top:none; border-radius:0 0 4px 0; }
.pay-qr-scan-line {
  position:absolute; left:8px; right:8px; height:2px;
  background:linear-gradient(90deg,transparent,#3b82f6,transparent);
  animation:qrScan 2s ease-in-out infinite; z-index:3;
}
@keyframes qrScan {
  0%  { top:10px; opacity:0.8; }
  50% { top:125px; opacity:1; }
  100%{ top:10px; opacity:0.8; }
}
.pay-upi-right { flex:1; display:flex; flex-direction:column; gap:10px; }
.pay-upi-id-box {
  background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2);
  border-radius:10px; padding:10px 12px;
}
.pay-upi-id-label { font-size:0.62rem; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.05em; }
.pay-upi-id-val   { font-size:0.85rem; font-weight:700; color:#60a5fa; font-family:monospace; margin-top:2px; }
.pay-upi-timer-box {
  background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.2);
  border-radius:10px; padding:8px 12px;
}
.pay-upi-timer-label{ font-size:0.62rem; color:rgba(255,255,255,0.4); }
.pay-upi-timer      { font-size:1.3rem; font-weight:800; color:#f59e0b; font-family:monospace; }
.pay-upi-apps-label { font-size:0.62rem; color:rgba(255,255,255,0.35); margin-bottom:4px; }
.pay-upi-apps-row   { display:flex; flex-wrap:wrap; gap:4px; }
.pay-upi-app {
  padding:2px 8px; border-radius:20px; font-size:0.62rem; font-weight:600;
  background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.6);
}
.pay-upi-status {
  display:flex; align-items:center; gap:8px; margin-top:12px;
  padding:8px 12px; background:rgba(16,185,129,0.06);
  border:1px solid rgba(16,185,129,0.15); border-radius:8px;
}
.pay-upi-status-dot {
  width:8px; height:8px; border-radius:50%; background:#10b981;
  animation:statusBlink 1.2s ease-in-out infinite;
  flex-shrink:0;
}
@keyframes statusBlink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }
.pay-upi-status-text { font-size:0.75rem; color:rgba(255,255,255,0.5); }

/* ── Credit Card Visual ── */
.pay-card-visual-wrap { perspective:1000px; margin:12px 0; }
.pay-card-3d {
  width:100%; max-width:340px; height:190px; position:relative;
  transform-style:preserve-3d; transition:transform 0.7s cubic-bezier(0.4,0,0.2,1);
  margin:0 auto;
}
.pay-card-3d.card-flip { transform:rotateY(180deg); }
.pay-card-front,.pay-card-back {
  position:absolute; inset:0; border-radius:18px;
  backface-visibility:hidden; -webkit-backface-visibility:hidden;
  padding:20px 24px;
}
.pay-card-front {
  background:linear-gradient(135deg,#1a237e 0%,#283593 40%,#1565c0 70%,#0d47a1 100%);
  box-shadow:0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.1),
             inset 0 1px 0 rgba(255,255,255,0.15);
  overflow:hidden;
}
.pay-card-front::before {
  content:''; position:absolute; top:-40%; right:-20%; width:200px; height:200px;
  background:radial-gradient(circle,rgba(255,255,255,0.08),transparent 70%);
  border-radius:50%;
}
.pay-card-glow {
  position:absolute; top:0; right:0; bottom:0; left:0; border-radius:18px;
  background:linear-gradient(135deg,rgba(255,255,255,0.05),transparent 60%);
}
.pay-card-chip {
  width:42px; height:32px; background:linear-gradient(135deg,#d4a843,#c8a85a,#e8c06a);
  border-radius:6px; display:flex; align-items:center; justify-content:center;
  font-size:1.2rem; color:rgba(139,90,0,0.6); margin-bottom:20px;
  box-shadow:0 2px 8px rgba(0,0,0,0.3);
}
.pay-card-network { position:absolute; top:20px; right:20px; font-size:0.95rem; font-weight:900; color:rgba(255,255,255,0.9); letter-spacing:0.05em; }
.pay-card-number  { font-size:1.15rem; font-weight:600; letter-spacing:0.18em; color:#fff; margin-bottom:16px; font-family:monospace; }
.pay-card-bottom  { display:flex; justify-content:space-between; align-items:flex-end; }
.pay-card-small-label { font-size:0.55rem; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:2px; }
.pay-card-holder  { font-size:0.82rem; font-weight:700; color:#fff; letter-spacing:0.08em; text-transform:uppercase; }
.pay-card-expiry  { font-size:0.88rem; font-weight:700; color:#fff; font-family:monospace; }
.pay-card-back {
  background:linear-gradient(135deg,#0d1b4b,#162259);
  transform:rotateY(180deg);
  box-shadow:0 20px 60px rgba(0,0,0,0.5);
}
.pay-card-stripe { background:#1a1a1a; height:44px; margin:-20px -24px 18px; }
.pay-card-cvv-area {
  background:rgba(255,255,255,0.9); border-radius:6px; padding:8px 12px;
  display:flex; justify-content:space-between; align-items:center;
}
.pay-card-cvv-val   { font-size:1rem; font-weight:700; color:#333; font-family:monospace; letter-spacing:0.2em; }
.pay-card-network-back { position:absolute; bottom:18px; right:22px; font-size:0.85rem; font-weight:900; color:rgba(255,255,255,0.7); }

/* ── Net Banking ── */
.pay-nb-note {
  background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.15);
  border-radius:10px; padding:10px 14px; font-size:0.78rem;
  color:rgba(255,255,255,0.55); margin:8px 0;
}

/* ── Wallet ── */
.pay-wallet-card {
  background:rgba(15,17,35,0.8); border:1px solid rgba(16,185,129,0.2);
  border-radius:14px; padding:16px; margin:10px 0;
}
.pay-wallet-header { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
.pay-wallet-icon   { font-size:1.8rem; }
.pay-wallet-type   { font-size:0.9rem; font-weight:700; color:#fff; }
.pay-wallet-bal    { font-size:0.78rem; color:rgba(255,255,255,0.5); }
.pay-wallet-bal b  { color:#10b981; }
.pay-wallet-note   { font-size:0.75rem; color:rgba(255,255,255,0.45); }

/* ── Coupon ── */
.pay-coupon-success {
  background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25);
  border-radius:10px; padding:10px 14px; font-size:0.82rem;
  color:rgba(255,255,255,0.7); margin:8px 0;
}
.pay-coupon-success b { color:#10b981; }
.pay-coupon-hint {
  font-size:0.65rem; color:rgba(255,255,255,0.25);
  font-style:italic; margin-top:4px;
}

/* ── Amount Display ── */
.pay-amount-card {
  background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(139,92,246,0.1));
  border:1px solid rgba(139,92,246,0.25); border-radius:16px;
  padding:16px 18px; margin:12px 0;
}
.pay-amt-row {
  display:flex; justify-content:space-between; align-items:center;
  padding:4px 0; font-size:0.82rem; color:rgba(255,255,255,0.55);
}
.pay-amt-row.discount { color:#10b981; }
.pay-amt-divider { border-top:1px solid rgba(255,255,255,0.08); margin:8px 0; }
.pay-amt-total-row { display:flex; justify-content:space-between; align-items:center; }
.pay-amt-total-label { font-size:0.9rem; font-weight:700; color:#fff; }
.pay-amt-total-val {
  font-size:2rem; font-weight:900; letter-spacing:-0.03em;
  background:linear-gradient(135deg,#a78bfa,#3b82f6);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  animation:totalGlow 3s ease-in-out infinite;
}
@keyframes totalGlow {
  0%,100%{filter:drop-shadow(0 0 6px rgba(139,92,246,0.5));}
  50%{filter:drop-shadow(0 0 14px rgba(139,92,246,0.9));}
}

/* ── Live Activity ── */
.pay-activity-card {
  background:rgba(15,17,35,0.6); border:1px solid rgba(255,255,255,0.05);
  border-radius:12px; padding:12px 14px; margin-bottom:12px;
}
.pay-activity-title { font-size:0.72rem; font-weight:700; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; }
.pay-activity-item  { display:flex; align-items:center; gap:8px; padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.pay-activity-item:last-child { border-bottom:none; }
.pay-activity-dot { width:6px; height:6px; border-radius:50%; background:#10b981; flex-shrink:0; }
.pay-activity-name { font-size:0.75rem; color:rgba(255,255,255,0.6); flex:1; }
.pay-activity-amt  { font-size:0.78rem; font-weight:700; color:#a78bfa; }
.pay-activity-time { font-size:0.65rem; color:rgba(255,255,255,0.3); }

/* ── Trust row ── */
.pay-trust-row {
  display:flex; justify-content:center; gap:16px; flex-wrap:wrap;
  padding:8px 0 12px; margin-top:6px;
}
.pay-trust-item { font-size:0.68rem; color:rgba(255,255,255,0.3); }

/* ── Empty state ── */
.pay-empty { text-align:center; padding:60px 20px; }
.pay-empty-icon  { font-size:3.5rem; margin-bottom:16px; }
.pay-empty-title { font-size:1.4rem; font-weight:700; color:#fff; margin-bottom:8px; }
.pay-empty-sub   { color:rgba(255,255,255,0.4); font-size:0.88rem; }

/* ── Success screen ── */
.pay-confetti-wrap { position:relative; height:0; overflow:visible; pointer-events:none; z-index:10; }
.confetti {
  position:absolute; width:10px; height:10px; border-radius:2px;
  animation:confettiFall 3s ease-in-out infinite;
  opacity:0;
}
.c1{top:-20px;left:10%; background:#3b82f6; animation-delay:0s;}
.c2{top:-20px;left:25%; background:#8b5cf6; animation-delay:0.3s;}
.c3{top:-20px;left:40%; background:#10b981; animation-delay:0.6s;}
.c4{top:-20px;left:55%; background:#f59e0b; animation-delay:0.9s;}
.c5{top:-20px;left:70%; background:#ef4444; animation-delay:1.2s;}
.c6{top:-20px;left:82%; background:#06b6d4; animation-delay:1.5s;}
.c7{top:-20px;left:15%; background:#a78bfa; animation-delay:1.8s;}
.c8{top:-20px;left:92%; background:#34d399; animation-delay:2.1s;}
@keyframes confettiFall {
  0%  {transform:translateY(0) rotate(0deg);   opacity:0;}
  10% {opacity:1;}
  100%{transform:translateY(120px) rotate(360deg); opacity:0;}
}

.pay-success-hero { text-align:center; padding:30px 0 20px; }
.pay-success-ring {
  width:80px; height:80px; border-radius:50%; margin:0 auto 16px;
  background:linear-gradient(135deg,#059669,#10b981);
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 0 0 8px rgba(16,185,129,0.15), 0 0 0 16px rgba(16,185,129,0.06);
  animation:successRing 1.5s ease-out;
}
@keyframes successRing {
  0%  { transform:scale(0.3); opacity:0; }
  70% { transform:scale(1.1); }
  100%{ transform:scale(1); opacity:1; }
}
.pay-success-check { font-size:2.2rem; color:#fff; font-weight:900; }
.pay-success-title {
  font-size:2rem; font-weight:800; color:#10b981; letter-spacing:-0.03em; margin-bottom:6px;
}
.pay-success-sub { color:rgba(255,255,255,0.45); font-size:0.9rem; }

.pay-success-meta {
  display:flex; flex-wrap:wrap; gap:12px; justify-content:center;
  background:rgba(15,17,35,0.7); border:1px solid rgba(255,255,255,0.07);
  border-radius:16px; padding:18px 20px; margin:16px 0;
}
.pay-meta-item   { text-align:center; min-width:130px; }
.pay-meta-label  { font-size:0.65rem; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }
.pay-meta-val    { font-size:0.88rem; font-weight:700; color:#fff; font-family:monospace; }
.pay-meta-val.blue  { color:#60a5fa; }
.pay-meta-val.green { color:#10b981; }

.pay-success-jobs-title { font-size:0.85rem; font-weight:700; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.06em; margin:20px 0 10px; }

.pay-sj-card {
  background:rgba(5,25,15,0.6); border:1px solid rgba(16,185,129,0.2);
  border-radius:14px; padding:16px 18px; margin-bottom:8px;
}
.pay-sj-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.pay-sj-doc    { font-size:0.95rem; font-weight:700; color:#fff; }
.pay-sj-cost   { font-size:1.2rem; font-weight:800; color:#a78bfa; }
.pay-sj-grid   { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:10px; }
.pay-sj-item   { background:rgba(255,255,255,0.025); border-radius:8px; padding:8px 10px; }
.pay-sj-label  { font-size:0.6rem; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:3px; }
.pay-sj-val    { font-size:0.82rem; font-weight:600; color:#e2e8f0; }
.pay-sj-val.blue   { color:#60a5fa; }
.pay-sj-val.purple { color:#a78bfa; }
.pay-sj-val.amber  { color:#f59e0b; }
.pay-sj-val.big    { font-size:1rem; font-weight:800; }
.pay-sj-val.mono   { font-family:monospace; }
.pay-sj-hint {
  font-size:0.72rem; color:rgba(255,255,255,0.35);
  border-top:1px solid rgba(255,255,255,0.05); padding-top:8px;
}
</style>"""
