"""
SmartPrint AI - Student Dashboard
Refactored layout hierarchy following strict 5-section enterprise SaaS structure.
"""

import streamlit as st
import re
from datetime import datetime
import pandas as pd
import numpy as np

from smartdb.crud import get_user_jobs

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_student_dashboard():
    """Render the student dashboard."""
    user = st.session_state.get("user", {})
    username = user.get("username", "Student")
    email = user.get("email", "student@smartprint.edu")
    user_id = user.get("id", 0)

    st.html(_clean_html(_dashboard_css()))

    # ── SECTION 1: Header & Greeting ─────────────────────────────────────
    with st.container():
        st.markdown(_clean_html(f"""
            <div class="dash-welcome">
                <div class="dash-greeting">Welcome back, <span class="dash-name">{username}</span> 👋</div>
                <div class="dash-user-info">📧 {email} &nbsp;•&nbsp; <span class="badge-student">Student Account</span></div>
                <div class="dash-date">{datetime.now().strftime('%A, %B %d, %Y')}</div>
            </div>
            """), unsafe_allow_html=True)

    # ── SECTION 2: Statistics Cards ──────────────────────────────────────
    with st.container():
        all_jobs = get_user_jobs(user_id) or []
        total = len(all_jobs)
        pending = sum(1 for j in all_jobs if j.get("status", "").lower() in ("pending", "payment_pending"))
        printing = sum(1 for j in all_jobs if j.get("status", "").lower() in ("queued", "printing"))
        completed = sum(1 for j in all_jobs if j.get("status", "").lower() in ("completed", "ready"))
        total_spent = sum(j.get("cost", 0) for j in all_jobs)

        m1, m2, m3, m4, m5 = st.columns(5)
        _metric_card(m1, "📄", "Total Jobs", total, "#00D9FF")
        _metric_card(m2, "⏳", "Pending", pending, "#f59e0b")
        _metric_card(m3, "🖨️", "Printing", printing, "#39FF14")
        _metric_card(m4, "✅", "Completed", completed, "#10b981")
        _metric_card(m5, "💰", "Total Spent", f"₹{total_spent:.0f}", "#06b6d4")

    # ── SECTION 3: Quick Actions ─────────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">⚡ Quick Actions</div>'), unsafe_allow_html=True)
    with st.container():
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("📤 Upload Documents", use_container_width=True, key="qa_upload_btn"):
                st.session_state["current_page"] = "Submit Print Job"
                st.rerun()
        with qa2:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("📋 Track Queue", use_container_width=True, key="qa_queue_btn"):
                st.session_state["current_page"] = "Track Order"
                st.rerun()
        with qa3:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("📜 Print History", use_container_width=True, key="qa_history_btn"):
                st.session_state["current_page"] = "My Print Jobs"
                st.rerun()
        with qa4:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("🔔 Notifications", use_container_width=True, key="qa_notif_btn"):
                st.session_state["current_page"] = "Notifications"
                st.rerun()

    # ── SECTION 4: Active Jobs & Live Printer Status ──────────────────────
    st.markdown(_clean_html('<div class="section-title">🖨️ Active Jobs & Live Printer Status</div>'), unsafe_allow_html=True)
    with st.container():
        col_active, col_printers = st.columns([1.5, 1])
        
        with col_active:
            st.markdown('<span class="active-jobs-sub-card-marker" style="display:none;"></span>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.95rem; font-weight:700; color:#fff; margin-bottom:12px;">Active Queue Details</div>', unsafe_allow_html=True)
            active_jobs = [j for j in all_jobs if j.get("status", "").lower() in ("pending", "payment_pending", "queued", "printing")]
            if not active_jobs:
                st.markdown('<div style="color:rgba(255,255,255,0.4); padding:10px 0; font-size:0.88rem;">No active print jobs currently in the queue.</div>', unsafe_allow_html=True)
            else:
                for j in active_jobs[:3]:
                    status = j.get("status", "Pending").title()
                    wait_time = j.get("estimated_wait_time", 0)
                    st.markdown(_clean_html(f"""
                        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-family:monospace; color:#00D9FF; font-weight:700; font-size:0.85rem;">{j.get('print_id')}</span>
                                <div style="font-size:0.82rem; color:rgba(255,255,255,0.6); margin-top:2px;">{j.get('document_name')[:25]}...</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.82rem; font-weight:700; color:#f59e0b;">⏳ {wait_time} min</div>
                                <span style="font-size:0.75rem; text-transform:uppercase; color:rgba(255,255,255,0.4); font-weight:600;">{status}</span>
                            </div>
                        </div>
                        """), unsafe_allow_html=True)

        with col_printers:
            st.markdown('<span class="printers-sub-card-marker" style="display:none;"></span>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.95rem; font-weight:700; color:#fff; margin-bottom:12px;">Printer Terminals</div>', unsafe_allow_html=True)
            printers = []
            try:
                from smartdb.crud import get_all_printers
                printers = get_all_printers() or []
            except Exception:
                pass
            if not printers:
                st.markdown('<div style="color:rgba(255,255,255,0.4); padding:10px 0; font-size:0.88rem;">No printers configured.</div>', unsafe_allow_html=True)
            else:
                for p in printers[:3]:
                    is_online = p.get("status") == "Online"
                    status_color = "#10b981" if is_online else "#ef4444"
                    st.markdown(_clean_html(f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03);">
                            <span style="font-size:0.85rem; color:rgba(255,255,255,0.8); font-weight:500;">{p.get('name')}</span>
                            <span style="color:{status_color}; font-size:0.82rem; font-weight:700;">● {p.get('status')}</span>
                        </div>
                        """), unsafe_allow_html=True)

    # ── SECTION 4.5: QR Pickup Codes ─────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">📱 QR Pickup Codes</div>'), unsafe_allow_html=True)
    with st.container():
        import os
        pickup_jobs = [j for j in all_jobs if j.get("qr_code_path") and os.path.exists(j.get("qr_code_path")) and j.get("status", "").lower() in ("ready", "completed", "queued", "printing")]
        if not pickup_jobs:
            st.info("No documents currently processing or ready for pickup. Upload files and make payment to generate your pickup QR codes.")
        else:
            cols = st.columns(min(4, len(pickup_jobs)))
            for idx, job in enumerate(pickup_jobs[:4]):
                with cols[idx % len(cols)]:
                    status_display = job.get('status', '').title()
                    status_color = "#10b981" if job.get('status', '').lower() in ("ready", "completed") else "#f59e0b"
                    st.markdown(_clean_html(f"""
                        <div class="qr-pickup-card">
                            <div class="qr-pickup-id">{job.get('print_id')}</div>
                            <div class="qr-pickup-doc">{job.get('document_name')[:20]}...</div>
                            <div class="qr-pickup-status" style="color:{status_color};">{status_display}</div>
                        </div>
                        """), unsafe_allow_html=True)
                    st.image(job.get("qr_code_path"), use_container_width=True)

    # ── SECTION 5: Recent Jobs Timeline ──────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">📋 Recent Jobs Timeline</div>'), unsafe_allow_html=True)

    with st.container():
        recent_jobs = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:5]
        if not recent_jobs:
            st.info("No recent print history found.")
        else:
            for job in recent_jobs:
                status = job.get("status", "unknown").capitalize()
                badge_color = _status_color(status.lower())
                st.markdown(_clean_html(f"""
                    <div class="job-row">
                        <div class="job-id">{job.get('print_id', 'N/A')}</div>
                        <div class="job-doc">{job.get('document_name', 'Document')}</div>
                        <div class="job-badge" style="background:{badge_color};">{status}</div>
                        <div class="job-date">{job.get('created_at', '')[:16]}</div>
                    </div>
                    """), unsafe_allow_html=True)


def _metric_card(column, icon: str, label: str, value, color: str):
    with column:
        st.markdown(_clean_html(f"""
            <div class="metric-card" style="border-top: 3px solid {color};">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """), unsafe_allow_html=True)

def _status_color(status: str) -> str:
    mapping = {
        "pending": "rgba(245,158,11,0.25)",
        "payment_pending": "rgba(245,158,11,0.25)",
        "queued": "rgba(59,130,246,0.25)",
        "printing": "rgba(0,217,255,0.25)",
        "completed": "rgba(16,185,129,0.25)",
        "ready": "rgba(16,185,129,0.3)",
        "failed": "rgba(239,68,68,0.25)",
    }
    return mapping.get(status, "rgba(255,255,255,0.1)")

def _dashboard_css() -> str:
    return """
    <style>
    .dash-welcome {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    .dash-greeting { font-size: 1.8rem; font-weight: 800; color: #fff; margin-bottom: 4px; }
    .dash-name { background: linear-gradient(135deg, #00D9FF, #7CFF00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .dash-user-info { color: rgba(255,255,255,0.5); font-size: 0.88rem; margin-bottom: 6px; }
    .dash-date { color: rgba(255,255,255,0.35); font-size: 0.82rem; font-weight: 500; }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.85);
        margin: 1.5rem 0 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        backdrop-filter: blur(12px);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        width: 100%;
    }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,217,255,0.12); }
    .metric-icon { font-size: 1.8rem; margin-bottom: 6px; }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #fff; }
    .metric-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }
    
    .active-jobs-sub-card, .printers-sub-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        min-height: 180px;
        backdrop-filter: blur(10px);
    }
    
    .job-row {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 20px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        margin-bottom: 8px;
        transition: background 0.2s ease;
        width: 100%;
    }
    .job-row:hover { background: rgba(255, 255, 255, 0.05); }
    .job-id { font-family: 'Courier New', monospace; color: #00D9FF; font-weight: 600; min-width: 130px; font-size: 0.88rem; }
    .job-doc { flex: 1; color: rgba(255, 255, 255, 0.75); font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .job-badge { padding: 3px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; color: #fff; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; min-width: 90px; }
    .job-date { color: rgba(255, 255, 255, 0.35); font-size: 0.8rem; min-width: 130px; text-align: right; }
    
    .qr-pickup-card {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        text-align: center !important;
        margin-bottom: 6px !important;
        backdrop-filter: blur(10px) !important;
    }
    .qr-pickup-id { font-family: monospace !important; font-weight: 700 !important; color: #00D9FF !important; font-size: 0.9rem !important; }
    .qr-pickup-doc { font-size: 0.75rem !important; color: rgba(255,255,255,0.6) !important; margin-top: 2px !important; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .qr-pickup-status { font-size: 0.72rem !important; font-weight: 700 !important; text-transform: uppercase !important; margin-top: 4px !important; }
    </style>
    """
