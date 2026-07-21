"""
SmartPrint AI - Payment Page
"""

import streamlit as st
import re
import uuid
import time
from smartdb.crud import get_job_by_id, update_job_status, create_payment
from smartutils.helpers import write_log


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_payment():
    """Render the payment page."""
    
    # We now handle batch jobs
    job_ids = st.session_state.get("payment_job_ids", [])
    batch_cost = st.session_state.get("payment_batch_cost", 0.0)

    st.html(_clean_html(_payment_css()))

    st.markdown(_clean_html("""
        <div class="pay-header">
            <div class="pay-icon">💳</div>
            <div class="pay-title">Batch Payment</div>
            <div class="pay-subtitle">Complete your payment to automatically start printing</div>
        </div>
        """), unsafe_allow_html=True)

    # ── Check for success state ──────────────────────────────────────────
    if st.session_state.get("payment_success"):
        _show_payment_success()
        return

    if not job_ids:
        st.warning("No jobs selected for payment. Please upload documents first.")
        if st.button("📤  Go to Upload", key="pay_upload"):
            st.session_state["current_page"] = "Submit Print Job"
            st.rerun()
        return

    # ── Order summary ────────────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1, 2.5, 1])
    with col_c:
        st.markdown(_clean_html(f"""
            <div class="order-card">
                <div class="oc-title">Order Summary</div>
                <div class="oc-row">
                    <span class="oc-label">Total Documents</span>
                    <span class="oc-value" style="font-family:monospace;color:#00D9FF;">{len(job_ids)} Files</span>
                </div>
                <div class="oc-divider"></div>
                <div class="oc-row oc-total-row">
                    <span class="oc-total-label">Total Amount</span>
                    <span class="oc-total-value">₹{batch_cost:.2f}</span>
                </div>
            </div>
            """), unsafe_allow_html=True)

        st.markdown(_clean_html("<br>"), unsafe_allow_html=True)

        # ── Payment method selection ─────────────────────────────────────
        st.markdown(_clean_html('<div class="section-title">💳 Payment Method</div>'), unsafe_allow_html=True)
        payment_method = st.radio(
            "Select Payment Method",
            options=["UPI (Google Pay / PhonePe)", "Credit / Debit Card", "Net Banking"],
            index=0, label_visibility="collapsed"
        )

        if "UPI" in payment_method:
            st.markdown(_clean_html('<div class="payment-method-card"><div class="pm-icon">📱</div><div class="pm-name">UPI Payment</div></div>'), unsafe_allow_html=True)
            upi_id = st.text_input("UPI ID", placeholder="yourname@upi")
        elif "Card" in payment_method:
            st.markdown(_clean_html('<div class="payment-method-card"><div class="pm-icon">💳</div><div class="pm-name">Card Payment</div></div>'), unsafe_allow_html=True)
            card_number = st.text_input("Card Number", placeholder="4242 4242 4242 4242")
            cc1, cc2 = st.columns(2)
            with cc1: expiry = st.text_input("Expiry (MM/YY)", placeholder="12/28")
            with cc2: cvv = st.text_input("CVV", type="password", placeholder="***", max_chars=4)
        else:
            st.markdown(_clean_html('<div class="payment-method-card"><div class="pm-icon">🏦</div><div class="pm-name">Net Banking</div></div>'), unsafe_allow_html=True)
            bank = st.selectbox("Select Bank", options=["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Other"])

        st.markdown(_clean_html("<br>"), unsafe_allow_html=True)

        st.markdown(_clean_html(f"""
            <div class="amount-display">
                <div class="amount-label">Amount to Pay</div>
                <div class="amount-value">₹{batch_cost:.2f}</div>
            </div>
            """), unsafe_allow_html=True)

        # ── Pay Now button ───────────────────────────────────────────────
        if st.button("🔒 Pay Now", use_container_width=True, type="primary"):
            write_log("PAYMENT_LOG", f"User initiating payment for Job IDs: {job_ids}. Total Cost: ₹{batch_cost:.2f}")
            with st.spinner("Processing payment and assigning queue..."):
                time.sleep(1.5)

            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            method_str = "UPI" if "UPI" in payment_method else ("Card" if "Card" in payment_method else "NetBanking")

            try:
                for j_id in job_ids:
                    job = get_job_by_id(j_id)
                    create_payment(
                        job_id=j_id,
                        user_id=st.session_state["user"]["id"],
                        amount=job.get('cost', 0),
                        method=method_str,
                        transaction_id=f"{txn_id}-{j_id}",
                        status="Success"
                    )
                    write_log("PAYMENT_LOG", f"Payment successful for Job ID={j_id}, Amount=₹{job.get('cost', 0):.2f}, Transaction ID={txn_id}-{j_id}")
                    # CRITICAL: Changing status to 'Queued' triggers the queue_manager daemon!
                    update_job_status(j_id, "Queued")
                    write_log("QUEUE_LOG", f"Job {job.get('print_id')} status updated to 'Queued' and assigned to printer queue.")
                    
                write_log("PAYMENT_LOG", f"Payment batch completed successfully. Txn ID prefix: {txn_id}")
                st.session_state["payment_success"] = True
                st.session_state["payment_success_amount"] = batch_cost
                st.rerun()
            except Exception as e:
                write_log("PAYMENT_LOG", f"Payment transaction recording failed for Job IDs: {job_ids}", e)
                st.error(f"Failed to record payment: {e}")



def _show_payment_success():
    amount = st.session_state.get("payment_success_amount", 0)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(_clean_html(f"""
            <div class="success-card">
                <div style="font-size:4rem;margin-bottom:16px;">🎉</div>
                <div class="success-title">Payment Successful!</div>
                <div class="success-subtitle">Your jobs are now automatically printing</div>
                <div class="success-detail">
                    <div class="sd-row">
                        <span class="sd-label">Amount Paid:</span>
                        <span class="sd-value">₹{amount:.2f}</span>
                    </div>
                    <div class="sd-row">
                        <span class="sd-label">Status:</span>
                        <span class="sd-value" style="color:#f59e0b;">Queued & Printing...</span>
                    </div>
                </div>
            </div>
            """), unsafe_allow_html=True)

        st.markdown(_clean_html("<br>"), unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📋 Track Queue", use_container_width=True, type="secondary"):
                _clear_payment_state()
                st.session_state["current_page"] = "Dashboard"
                st.rerun()
        with b2:
            if st.button("🏠 Dashboard", use_container_width=True, type="secondary"):
                _clear_payment_state()
                st.session_state["current_page"] = "Dashboard"
                st.rerun()


def _clear_payment_state():
    for key in ["payment_success", "payment_success_amount", "payment_job_ids", "payment_batch_cost"]:
        st.session_state.pop(key, None)

def _payment_css() -> str:
    return """
    <style>
    .pay-header { text-align: center; padding: 20px 0 10px; }
    .pay-icon { font-size: 3rem; margin-bottom: 8px; }
    .pay-title { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #00D9FF, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .pay-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    .section-title { font-size: 1.15rem; font-weight: 700; color: rgba(255,255,255,0.85); margin-bottom: 12px; }
    .order-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px 28px; backdrop-filter: blur(10px); }
    .oc-title { font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 16px; }
    .oc-row { display: flex; justify-content: space-between; padding: 8px 0; }
    .oc-label { color: rgba(255,255,255,0.5); font-size: 0.9rem; }
    .oc-value { color: #fff; font-weight: 600; font-size: 0.9rem; }
    .oc-divider { border-top: 1px solid rgba(255,255,255,0.08); margin: 12px 0; }
    .oc-total-row { padding-top: 12px; }
    .oc-total-label { font-size: 1.05rem; font-weight: 700; color: #fff; }
    .oc-total-value { font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #00D9FF, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .payment-method-card { display: flex; align-items: center; gap: 12px; background: rgba(0,217,255,0.06); border: 1px solid rgba(0,217,255,0.15); border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; }
    .pm-icon { font-size: 1.6rem; }
    .pm-name { font-weight: 600; color: #fff; font-size: 0.95rem; }
    .amount-display { background: linear-gradient(135deg, rgba(0,217,255,0.12), rgba(0,255,170,0.12)); border: 1px solid rgba(0,217,255,0.2); border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .amount-label { color: rgba(255,255,255,0.5); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .amount-value { font-size: 2.4rem; font-weight: 800; background: linear-gradient(135deg, #00D9FF, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 4px; }
    .success-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(16,185,129,0.2); border-radius: 20px; padding: 40px 30px; text-align: center; backdrop-filter: blur(12px); }
    .success-title { font-size: 1.8rem; font-weight: 800; color: #10b981; margin-bottom: 6px; }
    .success-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-bottom: 20px; }
    .success-detail { background: rgba(255,255,255,0.04); border-radius: 12px; padding: 16px 24px; display: inline-block; text-align: left; }
    .sd-row { display: flex; gap: 16px; padding: 6px 0; }
    .sd-label { color: rgba(255,255,255,0.45); font-size: 0.88rem; min-width: 110px; }
    .sd-value { color: #fff; font-weight: 700; font-size: 0.92rem; }
    </style>
    """
