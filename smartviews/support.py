"""
IntelliPrint Nexus - Support Center (Phase 3)
FAQ accordion, common issues, support ticket form.
"""

import streamlit as st
from datetime import datetime

_FAQS = [
    ("How do I upload a document for printing?",
     "Go to 'Upload & Print' from the dock or dashboard. Select your PDF file, configure copies, colour mode, paper size, and priority, then proceed to payment."),
    ("Why is my print job stuck in 'Queued' status?",
     "Your job is waiting for the assigned printer to become available. All active jobs are processed in priority order. You can check your queue position on the 'Track Queue' page."),
    ("Can I cancel my print job after payment?",
     "Cancellation is only possible before printing starts (status: Pending, Queued, or Waiting). Once printing begins, cancellation is not available. Contact the print center for urgent assistance."),
    ("How do I collect my document?",
     "Once your document shows 'Ready for Pickup', go to the printer location and show your QR code or Pickup ID to the staff. You can find these in 'My Print Jobs' or 'Dashboard'."),
    ("What file formats are supported?",
     "Currently only PDF files are supported. For other formats (DOCX, XLSX, PPTX), please convert them to PDF before uploading."),
    ("Why is the print quality low?",
     "Low quality is usually caused by a low-resolution source PDF. Ensure your document is exported at 300 DPI or higher for best results. Our AI analysis will flag quality issues before payment."),
    ("How is the cost calculated?",
     "Base cost is ₹2/page for B&W and ₹5/page for colour. Duplex printing saves approximately 35% on paper cost. Final cost = pages × copies × rate, adjusted for duplex."),
    ("What is a Pickup ID?",
     "A unique identifier generated after successful payment. It is embedded in the print-ready PDF along with a QR code and is required to collect your printed document."),
    ("Can I reprint a document?",
     "Yes! In 'My Print Jobs', each completed job has a 'Print Again' button that pre-fills all your previous settings. Just confirm and pay again."),
    ("What does the AI analysis do?",
     "The AI scans your document for quality issues including blur, skew, low resolution, and blank pages. It also provides paper and print recommendations before you commit to payment."),
    ("How do I change my default print settings?",
     "Go to Settings (⚙️) in the dock and configure your defaults for copies, colour mode, paper size, duplex, and priority. These will be pre-filled on every new upload."),
    ("I forgot my password. What do I do?",
     "You can change your password in the Profile (👤) page under 'Change Password'. If you're locked out, contact the print center admin."),
]

_COMMON_ISSUES = [
    ("🖨️", "Printer Offline",       "The selected printer may be temporarily offline. Go to 'Track Queue' and check printer status. Your job will resume automatically when the printer comes back online."),
    ("📄", "Document Not Printing",  "Check your job status in 'My Print Jobs'. If it's stuck for >15 minutes, use the support ticket form below to report it."),
    ("💳", "Payment Failed",         "If your payment failed but money was deducted, it will be refunded within 5-7 business days. Submit a ticket with your transaction ID."),
    ("📥", "Receipt Not Downloading", "Try refreshing the page and downloading again. If the issue persists, clear your browser cache or try a different browser."),
    ("📱", "QR Code Not Working",    "Ensure the QR code is fully visible and not damaged. The print center staff can also verify your job using the Pickup ID directly."),
    ("🔒", "Login Issues",           "Clear your browser cookies and try again. If you still cannot log in, use the support ticket form to contact admin."),
]


def show_support():
    """Render the support center page."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)
    username = user.get("username", "Student")
    email    = user.get("email", "")

    st.html(_support_css())

    st.html("""
    <div class="sup-header">
        <div class="sup-title">🆘 Support Center</div>
        <div class="sup-sub">Find answers, resolve issues, or contact our team</div>
    </div>
    """)

    # ── Quick links ───────────────────────────────────────────────────────────
    ql = st.columns(4)
    for col, (icon, label, page) in zip(ql, [
        ("📤", "New Print Job", "Submit Print Job"),
        ("📋", "Track Queue",   "Track Order"),
        ("📜", "My Jobs",       "My Print Jobs"),
        ("🔔", "Notifications", "Notifications"),
    ]):
        with col:
            if st.button(f"{icon} {label}", use_container_width=True, key=f"sup_ql_{page}"):
                st.session_state["current_page"] = page
                st.rerun()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_faq, tab_issues, tab_ticket, tab_contact = st.tabs([
        "❓ FAQ",
        "🔧 Common Issues",
        "📝 Submit Ticket",
        "📞 Contact",
    ])

    with tab_faq:
        st.html('<div class="sup-section">Frequently Asked Questions</div>')
        for i, (question, answer) in enumerate(_FAQS):
            with st.expander(f"❓ {question}", expanded=False):
                st.markdown(answer)

    with tab_issues:
        st.html('<div class="sup-section">Common Issues & Solutions</div>')
        for icon, issue, solution in _COMMON_ISSUES:
            st.html(f"""
            <div class="issue-card">
                <div class="issue-icon">{icon}</div>
                <div class="issue-body">
                    <div class="issue-title">{issue}</div>
                    <div class="issue-desc">{solution}</div>
                </div>
            </div>
            """)

    with tab_ticket:
        st.html('<div class="sup-section">Submit a Support Ticket</div>')
        st.caption("Your ticket will be sent to the print center admin as a notification.")

        with st.form("support_ticket_form", clear_on_submit=True):
            t1, t2 = st.columns(2)
            with t1:
                ticket_name = st.text_input("Your Name", value=username, key="sup_name")
                ticket_email = st.text_input("Email", value=email, key="sup_email")
            with t2:
                ticket_category = st.selectbox(
                    "Issue Category",
                    ["Payment Problem", "Print Quality", "Document Not Printing",
                     "Pickup / Collection", "Account Access", "Printer Offline",
                     "Receipt / Download", "Other"],
                    key="sup_category",
                )
                ticket_job_id = st.text_input(
                    "Job / Print ID (optional)",
                    placeholder="e.g. SP2026-AB12",
                    key="sup_job_id",
                )
            ticket_desc = st.text_area(
                "Describe your issue *",
                placeholder="Please provide as much detail as possible...",
                height=120,
                key="sup_desc",
            )
            submitted = st.form_submit_button("📤 Submit Ticket", use_container_width=True)
            if submitted:
                if not ticket_desc.strip():
                    st.error("Please describe your issue before submitting.")
                else:
                    try:
                        from smartdb.crud_ext import create_notification
                        # Find admin user IDs to notify
                        try:
                            from smartdb.crud import get_all_users
                            admins = [u["id"] for u in (get_all_users() or [])
                                      if (u.get("role") or "").lower() == "admin"]
                        except Exception:
                            admins = []

                        ticket_msg = (
                            f"From: {ticket_name} ({ticket_email})\n"
                            f"Category: {ticket_category}\n"
                            f"Job ID: {ticket_job_id or 'N/A'}\n"
                            f"Message: {ticket_desc[:300]}"
                        )
                        for admin_id in admins:
                            create_notification(
                                admin_id,
                                f"🎫 Support Ticket — {ticket_category}",
                                ticket_msg,
                                notification_type="warning",
                            )
                        # Also notify student
                        create_notification(
                            user_id,
                            "✅ Support Ticket Submitted",
                            f"Your ticket '{ticket_category}' has been received. We'll respond within 24 hours.",
                            notification_type="success",
                        )
                        st.success("✅ Your support ticket has been submitted! We'll respond within 24 hours.")
                    except Exception as e:
                        st.error(f"Could not submit ticket: {e}")

    with tab_contact:
        st.html("""
        <div class="contact-grid">
            <div class="contact-item">
                <div class="ci-icon">📧</div>
                <div class="ci-label">Email</div>
                <div class="ci-val">support@smartprint.edu</div>
            </div>
            <div class="contact-item">
                <div class="ci-icon">📞</div>
                <div class="ci-label">Phone</div>
                <div class="ci-val">+91 98765 43210</div>
            </div>
            <div class="contact-item">
                <div class="ci-icon">🕐</div>
                <div class="ci-label">Hours</div>
                <div class="ci-val">Mon–Fri: 8am–8pm</div>
            </div>
            <div class="contact-item">
                <div class="ci-icon">📍</div>
                <div class="ci-label">Location</div>
                <div class="ci-val">Library Ground Floor, Block A</div>
            </div>
        </div>
        <div class="contact-note">
            For urgent issues outside office hours, submit a support ticket above and
            it will be addressed on the next business day.
        </div>
        """)


def _support_css() -> str:
    return """<style>
.sup-header { padding:14px 0 10px; margin-bottom:1rem; }
.sup-title {
    font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.sup-sub { color:rgba(255,255,255,.4); font-size:.88rem; margin-top:4px; }
.sup-section {
    font-size:.9rem; font-weight:700; color:rgba(255,255,255,.6);
    text-transform:uppercase; letter-spacing:.5px;
    margin:12px 0 10px; padding-bottom:5px;
    border-bottom:1px solid rgba(255,255,255,.06);
}

.issue-card {
    display:flex; gap:14px; align-items:flex-start;
    background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:14px 16px; margin-bottom:8px;
}
.issue-icon { font-size:1.6rem; flex-shrink:0; }
.issue-title { font-size:.9rem; font-weight:700; color:#fff; margin-bottom:4px; }
.issue-desc  { font-size:.8rem; color:rgba(255,255,255,.55); line-height:1.5; }

.contact-grid {
    display:grid; grid-template-columns:1fr 1fr;
    gap:12px; margin:12px 0;
}
.contact-item {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:16px; text-align:center;
}
.ci-icon  { font-size:1.8rem; margin-bottom:6px; }
.ci-label { font-size:.68rem; color:rgba(255,255,255,.4);
            text-transform:uppercase; letter-spacing:.4px; }
.ci-val   { font-size:.92rem; font-weight:600; color:#fff; margin-top:4px; }
.contact-note {
    color:rgba(255,255,255,.4); font-size:.78rem;
    text-align:center; margin-top:12px; line-height:1.5;
}
</style>"""
