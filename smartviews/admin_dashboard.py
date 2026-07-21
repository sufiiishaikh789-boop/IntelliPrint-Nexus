"""
SmartPrint AI - Admin Control Center
Refactored layout hierarchy following strict 5-section enterprise SaaS structure.
"""

import streamlit as st
import re
from datetime import datetime
import plotly.graph_objects as go

from smartdb.crud import get_dashboard_stats, get_all_printers, get_all_jobs
from smartai.gpu_utils import check_nvidia_gpu

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_admin_dashboard():
    """Render the admin control dashboard."""
    user = st.session_state.get("user", {})
    username = user.get("username", "Admin")
    email = user.get("email", "admin@smartprint.edu")

    st.html(_clean_html(_admin_css()))

    # ── SECTION 1: Header & Context ──────────────────────────────────────
    with st.container():
        st.markdown(_clean_html(f"""
            <div class="admin-welcome">
                <div class="admin-greeting">Control Console, <span class="admin-name">{username}</span> 🛡️</div>
                <div class="admin-user-info">📧 {email} &nbsp;•&nbsp; <span class="badge-admin">System Administrator</span></div>
                <div class="admin-date">{datetime.now().strftime('%A, %B %d, %Y  •  %I:%M %p')}</div>
            </div>
            """), unsafe_allow_html=True)

    # ── Fetch Stats Data ──────────────────────────────────────────────────
    stats = get_dashboard_stats() or {}
    total_users = stats.get("total_users", 0)
    total_jobs = stats.get("total_jobs", 0)
    revenue = stats.get("total_revenue", 0)
    pending = stats.get("pending", 0)
    printing = stats.get("printing", 0)
    completed = stats.get("completed", 0)

    # ── SECTION 2: Statistics Cards ──────────────────────────────────────
    with st.container():
        r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
        _admin_metric(r1c1, "👥", "Users", total_users, "#00D9FF")
        _admin_metric(r1c2, "📄", "Jobs", total_jobs, "#3b82f6")
        _admin_metric(r1c3, "⏳", "Pending", pending, "#f59e0b")
        _admin_metric(r1c4, "🖨️", "Printing", printing, "#39FF14")
        _admin_metric(r1c5, "✅", "Completed", completed, "#10b981")
        _admin_metric(r1c6, "💰", "Revenue", f"₹{revenue:,.0f}", "#06b6d4")

    # ── SECTION 2b: GPU / AI Hardware Monitor ────────────────────────────
    gpu = check_nvidia_gpu()
    gpu_name   = gpu.get("gpu_name", "N/A")
    cuda_ver   = gpu.get("cuda_version", "N/A")
    mem_used   = gpu.get("memory_used_mb", 0)
    mem_total  = gpu.get("memory_total_mb", 0)
    gpu_util   = gpu.get("utilization_percent", 0)
    tf_gpu     = gpu.get("tf_gpu_available", False)
    gpu_active = gpu.get("gpu_available", False)

    mem_pct    = int((mem_used / mem_total * 100) if mem_total > 0 else 0)
    hw_label   = gpu_name if gpu_active else "CPU Mode (No GPU Detected)"
    hw_color   = "#10b981" if gpu_active else "#f59e0b"
    cuda_label = f"CUDA {cuda_ver}" if gpu_active else "N/A"
    tf_label   = "✅ TensorFlow GPU" if tf_gpu else "⚠️ TensorFlow CPU"

    st.markdown(_clean_html('<div class="section-title">⚡ NVIDIA GPU / AI Hardware Monitor</div>'), unsafe_allow_html=True)
    with st.container():
        gc1, gc2, gc3, gc4, gc5 = st.columns(5)
        def _gpu_card(col, icon, label, val, color="#fff"):
            with col:
                st.markdown(_clean_html(f"""
                    <div class="admin-metric" style="border-left:3px solid {color};">
                        <div class="am-top">
                            <span class="am-icon">{icon}</span>
                            <span class="am-label">{label}</span>
                        </div>
                        <div class="am-value" style="font-size:1rem;color:{color};">{val}</div>
                    </div>"""), unsafe_allow_html=True)
        _gpu_card(gc1, "🖥️", "Hardware", hw_label[:18], hw_color)
        _gpu_card(gc2, "⚡", "CUDA Version", cuda_label, "#00D9FF" if gpu_active else "#6b7280")
        _gpu_card(gc3, "🧠", "TensorFlow", tf_label, "#10b981" if tf_gpu else "#f59e0b")
        _gpu_card(gc4, "📊", "VRAM Usage", f"{mem_used}MB / {mem_total}MB" if mem_total else "CPU RAM", "#00D9FF")
        _gpu_card(gc5, "📈", "GPU Utilization", f"{gpu_util}%" if gpu_active else "N/A", "#06b6d4")

    # ── SECTION 3: Quick Actions Grid ─────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">⚡ Quick Actions</div>'), unsafe_allow_html=True)
    with st.container():
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("📋 Queue Management", use_container_width=True, key="adm_qa_queue"):
                st.session_state["current_page"] = "Queue Management"
                st.rerun()
        with qa2:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("🖨️ Printer Terminals", use_container_width=True, key="adm_qa_printer"):
                st.session_state["current_page"] = "Printer Management"
                st.rerun()
        with qa3:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("📈 System Analytics", use_container_width=True, key="adm_qa_analytics"):
                st.session_state["current_page"] = "Analytics"
                st.rerun()
        with qa4:
            st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
            if st.button("⚙️ Admin Settings", use_container_width=True, key="adm_qa_settings"):
                st.session_state["current_page"] = "Admin Panel"
                st.rerun()

    # ── SECTION 4: Active Status & Printers Grid ──────────────────────────
    st.markdown(_clean_html('<div class="section-title">📊 Active Analytics & Printer Terminals</div>'), unsafe_allow_html=True)
    with st.container():
        col_chart, col_printers = st.columns([1.2, 1])
        
        with col_chart:
            st.markdown('<span class="admin-sub-card-marker" style="display:none;"></span>', unsafe_allow_html=True)
            _jobs_pie_chart(pending, printing, completed)

        with col_printers:
            st.markdown('<span class="admin-sub-card-marker" style="display:none;"></span>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.95rem; font-weight:700; color:#fff; margin-bottom:12px;">Active Printers</div>', unsafe_allow_html=True)
            printers = []
            try:
                printers = get_all_printers() or []
            except Exception:
                pass
            if not printers:
                printers = [
                    {"name": "HP LaserJet Pro", "status": "Online", "toner_level": 85},
                    {"name": "Canon imageRUNNER", "status": "Online", "toner_level": 42},
                    {"name": "Epson WF-C5790", "status": "Offline", "toner_level": 12},
                ]
            for p in printers[:4]:
                is_online = p.get("status", "").lower() == "online"
                status_color = "#10b981" if is_online else "#ef4444"
                st.markdown(_clean_html(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03);">
                        <div>
                            <span style="font-size:0.85rem; color:#fff; font-weight:600;">{p.get('name')}</span>
                            <div style="font-size:0.75rem; color:rgba(255,255,255,0.45);">Toner: {p.get('toner_level', 0)}%</div>
                        </div>
                        <span style="color:{status_color}; font-size:0.82rem; font-weight:700;">● {p.get('status')}</span>
                    </div>
                    """), unsafe_allow_html=True)

    # ── SECTION 5: Recent Activity Timeline ───────────────────────────────
    st.markdown(_clean_html('<div class="section-title">📋 Recent Activity Feed</div>'), unsafe_allow_html=True)
    with st.container():
        all_jobs = []
        try:
            all_jobs = get_all_jobs() or []
        except Exception:
            pass
        recent = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:6]

        if not recent:
            st.info("No system activity logged.")
        else:
            for job in recent:
                status = job.get("status", "unknown").capitalize()
                badge_color = {
                    "pending": "#f59e0b",
                    "payment_pending": "#f59e0b",
                    "queued": "#3b82f6",
                    "printing": "#39FF14",
                    "completed": "#10b981",
                    "ready": "#06b6d4",
                    "failed": "#ef4444",
                }.get(job.get("status", "").lower(), "#6b7280")

                st.markdown(_clean_html(f"""
                    <div class="activity-row">
                        <div class="act-id">{job.get('print_id', 'N/A')}</div>
                        <div class="act-user">User #{job.get('user_id', '?')}</div>
                        <div class="act-doc">{job.get('document_name', 'Document')}</div>
                        <span class="act-badge" style="background:{badge_color}20;color:{badge_color};">{status}</span>
                        <div class="act-time">{job.get('created_at', '')[:16]}</div>
                    </div>
                    """), unsafe_allow_html=True)


def _admin_metric(column, icon: str, label: str, value, color: str):
    with column:
        st.markdown(_clean_html(f"""
            <div class="admin-metric" style="border-left: 3px solid {color};">
                <div class="am-top">
                    <span class="am-icon">{icon}</span>
                    <span class="am-label">{label}</span>
                </div>
                <div class="am-value">{value}</div>
            </div>
            """), unsafe_allow_html=True)

def _jobs_pie_chart(pending: int, printing: int, completed: int):
    labels = ["Pending", "Printing", "Completed"]
    values = [pending, printing, completed]
    colors = ["#f59e0b", "#39FF14", "#10b981"]

    if sum(values) == 0:
        values = [1, 1, 1]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.3)", width=2)),
            textfont=dict(size=12, color="#fff"),
            hoverinfo="label+percent+value",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fff"),
        margin=dict(t=5, b=5, l=5, r=5),
        height=180,
        showlegend=True,
        legend=dict(font=dict(color="rgba(255,255,255,0.6)", size=10), orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _admin_css() -> str:
    return """
    <style>
    .admin-welcome {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    .admin-greeting { font-size: 1.8rem; font-weight: 800; color: #fff; margin-bottom: 4px; }
    .admin-name { background: linear-gradient(135deg, #00D9FF, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .admin-user-info { color: rgba(255,255,255,0.5); font-size: 0.88rem; margin-bottom: 6px; }
    .admin-date { color: rgba(255,255,255,0.35); font-size: 0.82rem; font-weight: 500; }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.85);
        margin: 1.5rem 0 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .admin-metric {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 14px;
        backdrop-filter: blur(10px);
        transition: transform 0.25s ease;
        width: 100%;
    }
    .admin-metric:hover { transform: translateY(-2px); }
    .am-top { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
    .am-icon { font-size: 1.25rem; }
    .am-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .am-value { font-size: 1.45rem; font-weight: 800; color: #fff; }

    .admin-sub-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        min-height: 220px;
        backdrop-filter: blur(10px);
    }

    .activity-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 18px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        margin-bottom: 6px;
        width: 100%;
    }
    .activity-row:hover { background: rgba(255, 255, 255, 0.04); }
    .act-id { font-family: 'Courier New', monospace; color: #00D9FF; font-weight: 600; font-size: 0.85rem; min-width: 120px; }
    .act-user { color: rgba(255, 255, 255, 0.5); font-size: 0.82rem; min-width: 80px; }
    .act-doc { flex: 1; color: rgba(255, 255, 255, 0.7); font-size: 0.88rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .act-badge { padding: 3px 12px; border-radius: 16px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .act-time { color: rgba(255, 255, 255, 0.3); font-size: 0.78rem; min-width: 120px; text-align: right; }
    </style>
    """;
