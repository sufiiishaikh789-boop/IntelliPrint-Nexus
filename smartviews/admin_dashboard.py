"""
IntelliPrint Nexus - Admin Control Center
Refactored layout hierarchy following strict 5-section enterprise SaaS structure.
"""

import streamlit as st
import re
from datetime import datetime
import plotly.graph_objects as go

from smartdb.crud import get_dashboard_stats, get_all_printers, get_all_jobs, get_today_stats
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

    # ── TODAY's Business Dashboard ────────────────────────────────────────
    today = {}
    try:
        today = get_today_stats() or {}
    except Exception:
        pass

    st.markdown(_clean_html('<div class="section-title">📅 Today\'s Business Summary</div>'), unsafe_allow_html=True)
    with st.container():
        td1, td2, td3, td4, td5, td6, td7, td8, td9 = st.columns(9)
        _admin_metric(td1, "💰", "Revenue", f"₹{today.get('today_revenue', 0):,.0f}", "#10B981")
        _admin_metric(td2, "📄", "Docs Today", today.get("today_docs", 0), "#60A5FA")
        _admin_metric(td3, "📃", "Pages Today", today.get("today_pages", 0), "#3B82F6")
        _admin_metric(td4, "⏱️", "Avg Wait", f"{today.get('avg_wait', 0)}m", "#F59E0B")
        _admin_metric(td5, "🌟", "Priority", today.get("today_priority", 0), "#A78BFA")
        _admin_metric(td6, "❌", "Cancelled", today.get("today_cancelled", 0), "#EF4444")
        _admin_metric(td7, "👥", "Students", today.get("active_students", 0), "#34D399")
        _admin_metric(td8, "🟢", "Online", today.get("online_printers", 0), "#10B981")
        _admin_metric(td9, "🔴", "Offline", today.get("offline_printers", 0), "#EF4444")

    with st.container():
        r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
        _admin_metric(r1c1, "👥", "Users", total_users, "#60A5FA")
        _admin_metric(r1c2, "📄", "Jobs", total_jobs, "#3B82F6")
        _admin_metric(r1c3, "⏳", "Pending", pending, "#F59E0B")
        _admin_metric(r1c4, "🖨️", "Printing", printing, "#A78BFA")
        _admin_metric(r1c5, "✅", "Completed", completed, "#10B981")
        _admin_metric(r1c6, "💰", "Revenue", f"₹{revenue:,.0f}", "#34D399")

    # ── SECTION 2b: GPU / AI Hardware Monitor ────────────────────────────
    from smartai.gpu_utils import get_gpu_extended_stats, get_system_resources
    gpu = check_nvidia_gpu()
    gpu_ext = get_gpu_extended_stats()
    sysres  = get_system_resources()

    gpu_name   = gpu.get("gpu_name", "N/A")
    cuda_ver   = gpu.get("cuda_version", "N/A")
    mem_used   = gpu.get("memory_used_mb", 0)
    mem_total  = gpu.get("memory_total_mb", 0)
    gpu_util   = gpu.get("utilization_percent", 0)
    tf_gpu     = gpu.get("tf_gpu_available", False)
    gpu_active = gpu.get("gpu_available", False)
    gpu_temp   = gpu_ext.get("temperature_c", "N/A")
    gpu_power  = gpu_ext.get("power_draw_w", "N/A")
    gpu_fan    = gpu_ext.get("fan_speed_pct", "N/A")

    mem_pct    = int((mem_used / mem_total * 100) if mem_total > 0 else 0)
    hw_label   = gpu_name if gpu_active else "CPU Mode"
    hw_color   = "#10b981" if gpu_active else "#f59e0b"
    mode_icon  = "🚀" if gpu_active else "⚙️"
    cuda_label = f"CUDA {cuda_ver}" if (gpu_active and cuda_ver != "N/A") else ("N/A" if not gpu_active else cuda_ver)
    tf_label   = "✅ TF GPU" if tf_gpu else "⚠️ TF CPU"
    vram_label = f"{mem_used}MB / {mem_total}MB" if mem_total else "N/A"
    util_label = f"{gpu_util}%" if gpu_active else "N/A"
    temp_label = f"{gpu_temp}°C" if isinstance(gpu_temp, int) else "N/A"
    power_label = f"{gpu_power:.1f}W" if isinstance(gpu_power, float) else "N/A"

    cpu_pct  = sysres.get("cpu_percent", "N/A")
    ram_used = sysres.get("ram_used_gb", "N/A")
    ram_tot  = sysres.get("ram_total_gb", "N/A")
    ram_pct  = sysres.get("ram_percent", "N/A")
    disk_pct = sysres.get("disk_percent", "N/A")

    def _pbar_color(pct):
        if not isinstance(pct, (int, float)): return "#6b7280"
        if pct < 60: return "#10b981"
        if pct < 80: return "#f59e0b"
        return "#ef4444"

    def _pbar(pct, color):
        w = f"{pct}%" if isinstance(pct, (int, float)) else "0%"
        return f'<div style="background:rgba(255,255,255,.08);border-radius:4px;height:5px;margin-top:4px;"><div style="width:{w};background:{color};height:5px;border-radius:4px;transition:width .5s;"></div></div>'

    st.markdown(_clean_html('<div class="section-title">⚡ AI Hardware Monitor — Live</div>'), unsafe_allow_html=True)
    with st.container():
        gc1, gc2, gc3, gc4, gc5, gc6 = st.columns(6)

        def _gpu_card(col, icon, label, val, color="#fff", sub=""):
            with col:
                sub_html = f'<div style="font-size:.65rem;color:rgba(255,255,255,.35);margin-top:3px;">{sub}</div>' if sub else ""
                st.markdown(_clean_html(f"""
                    <div class="admin-metric" style="border-left:3px solid {color};">
                        <div class="am-top">
                            <span class="am-icon">{icon}</span>
                            <span class="am-label">{label}</span>
                        </div>
                        <div class="am-value" style="font-size:.92rem;color:{color};">{val}</div>
                        {sub_html}
                    </div>"""), unsafe_allow_html=True)

        _gpu_card(gc1, mode_icon, "Hardware Mode",  hw_label[:16], hw_color, "GPU" if gpu_active else "CPU Fallback")
        _gpu_card(gc2, "⚡",        "CUDA Version",  cuda_label,    "#3B82F6" if gpu_active else "#6b7280", f"TF: {'GPU' if tf_gpu else 'CPU'}")
        _gpu_card(gc3, "🌡️",       "GPU Temp",      temp_label,    "#06b6d4" if isinstance(gpu_temp,int) and gpu_temp<80 else "#f59e0b", f"Fan: {gpu_fan}%" if isinstance(gpu_fan, int) else "Fan: N/A")
        _gpu_card(gc4, "⚡",        "GPU Power",     power_label,   "#8B5CF6" if isinstance(gpu_power, float) else "#6b7280", "Power Draw")
        _gpu_card(gc5, "📊",        "VRAM",          vram_label,    "#3B82F6", f"{mem_pct}% used")
        _gpu_card(gc6, "📈",        "GPU Util",      util_label,    "#06b6d4" if gpu_active else "#6b7280", "Real-time")

    # ── Live System Resources ─────────────────────────────────────────────
    with st.container():
        st.markdown(_clean_html(f"""
        <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px 18px;margin-top:10px;">
            <div style="font-size:.78rem;font-weight:700;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;">⚙️ Live System Resources</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">CPU Usage</div>
                    <div style="font-size:1rem;font-weight:700;color:{'#10b981' if isinstance(cpu_pct,float) and cpu_pct<70 else '#f59e0b'};">{cpu_pct}{'%' if isinstance(cpu_pct,(int,float)) else ''}</div>
                    {_pbar(cpu_pct, _pbar_color(cpu_pct))}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">RAM Usage</div>
                    <div style="font-size:1rem;font-weight:700;color:{'#10b981' if isinstance(ram_pct,(int,float)) and ram_pct<75 else '#f59e0b'};">{ram_used} GB / {ram_tot} GB</div>
                    {_pbar(ram_pct, _pbar_color(ram_pct))}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">Disk Usage</div>
                    <div style="font-size:1rem;font-weight:700;color:{'#10b981' if isinstance(disk_pct,(int,float)) and disk_pct<80 else '#f59e0b'};">{disk_pct}{'%' if isinstance(disk_pct,(int,float)) else ''}</div>
                    {_pbar(disk_pct, _pbar_color(disk_pct))}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">GPU VRAM</div>
                    <div style="font-size:1rem;font-weight:700;color:{'#10b981' if mem_pct<75 else '#f59e0b'};">{mem_pct}% {'used' if mem_total else 'N/A'}</div>
                    {_pbar(mem_pct, _pbar_color(mem_pct))}
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    # ── SECTION 3: Quick Actions Grid ─────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">⚡ Quick Actions</div>'), unsafe_allow_html=True)
    with st.container():
        qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)
        for col, (label, page) in zip(
            [qa1, qa2, qa3, qa4, qa5, qa6],
            [
                ("📋 Queue",        "Queue Management"),
                ("🖨️ Printers",    "Printer Management"),
                ("🖥️ Digital Twin","Digital Twin"),
                ("📡 Activity Log", "Activity Log"),
                ("📊 Reports",      "Reports"),
                ("👥 Students",     "Student Management"),
            ],
        ):
            with col:
                st.markdown('<span class="quick-action-marker" style="display:none;"></span>', unsafe_allow_html=True)
                if st.button(label, use_container_width=True, key=f"adm_qa_{page.replace(' ','_').lower()}"):
                    st.session_state["current_page"] = page
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
                    "pending":         "#F59E0B",
                    "payment_pending": "#F59E0B",
                    "queued":          "#3B82F6",
                    "printing":        "#A78BFA",
                    "completed":       "#10B981",
                    "ready":           "#06B6D4",
                    "failed":          "#EF4444",
                }.get(job.get("status", "").lower(), "#94A3B8")

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
    colors = ["#F59E0B", "#A78BFA", "#10B981"]

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
        background: linear-gradient(145deg, rgba(59,130,246,.06), rgba(139,92,246,.03));
        border: 1px solid rgba(59,130,246,.18);
        border-radius: 16px;
        padding: 22px 28px;
        margin-bottom: 1.2rem;
    }
    .admin-greeting { font-size: 1.75rem; font-weight: 800; color: #F8FAFC;
                      letter-spacing: -0.02em; margin-bottom: 5px; }
    .admin-name {
        background: linear-gradient(135deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .admin-user-info { color: rgba(255,255,255,.42); font-size: 0.85rem; margin-bottom: 5px; }
    .admin-date { color: rgba(255,255,255,.28); font-size: 0.8rem; font-weight: 500; }
    .badge-admin {
        background: rgba(59,130,246,.12); color: #60A5FA;
        border: 1px solid rgba(59,130,246,.25); border-radius: 20px;
        padding: 2px 10px; font-size: 0.75rem; font-weight: 700;
    }

    .section-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: rgba(255,255,255,.48);
        margin: 1.6rem 0 10px;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }

    .admin-metric {
        background: rgba(255,255,255,.025);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 14px;
        padding: 14px 16px;
        transition: transform 0.2s cubic-bezier(0.4,0,0.2,1),
                    box-shadow 0.2s cubic-bezier(0.4,0,0.2,1);
        width: 100%;
    }
    .admin-metric:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.4); }
    .am-top { display: flex; align-items: center; gap: 7px; margin-bottom: 7px; }
    .am-icon { font-size: 1.15rem; }
    .am-label { font-size: 0.68rem; color: rgba(255,255,255,.38);
                text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; }
    .am-value { font-size: 1.4rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em; }

    .admin-sub-card {
        background: rgba(255,255,255,.025);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 16px;
        padding: 20px;
        min-height: 220px;
    }

    .activity-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 11px 16px;
        background: rgba(255,255,255,.018);
        border: 1px solid rgba(255,255,255,.05);
        border-radius: 11px;
        margin-bottom: 6px;
        width: 100%;
        transition: background .15s, border-color .15s;
    }
    .activity-row:hover { background: rgba(59,130,246,.05); border-color: rgba(59,130,246,.15); }
    .act-id { font-family: 'Courier New', monospace; color: #60A5FA;
              font-weight: 700; font-size: 0.82rem; min-width: 120px; }
    .act-user { color: rgba(255,255,255,.42); font-size: 0.8rem; min-width: 80px; }
    .act-doc { flex: 1; color: rgba(255,255,255,.72); font-size: 0.86rem;
               overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .act-badge { padding: 3px 10px; border-radius: 14px; font-size: 0.7rem;
                 font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
    .act-time { color: rgba(255,255,255,.28); font-size: 0.76rem;
                min-width: 120px; text-align: right; }
    </style>
    """;
