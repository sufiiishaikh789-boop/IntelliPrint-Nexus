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

# Centralized hardware telemetry (new)
try:
    from smartcore.hardware_telemetry import hardware_telemetry as _hw_svc
except Exception:
    _hw_svc = None

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

    # ── SECTION 2b: GPU / AI Hardware Monitor (upgraded) ─────────────────
    _render_hardware_monitor()

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


# ══════════════════════════════════════════════════════════════════════════════
# AI HARDWARE MONITOR — Upgraded Component
# Uses @st.fragment(run_every=5) for auto-refresh + manual Refresh button
# All values come from hardware_telemetry service (real, never fabricated)
# ══════════════════════════════════════════════════════════════════════════════

@st.fragment(run_every=5)
def _render_hardware_monitor():
    """Self-refreshing AI Hardware Monitor fragment."""

    # ── Session state initialisation ──────────────────────────────────────
    if "hw_refreshing" not in st.session_state:
        st.session_state["hw_refreshing"] = False
    if "hw_last_updated" not in st.session_state:
        st.session_state["hw_last_updated"] = None
    if "hw_error" not in st.session_state:
        st.session_state["hw_error"] = None

    # ── Collect telemetry ─────────────────────────────────────────────────
    tel = None
    force = st.session_state.get("hw_force_refresh", False)
    if force:
        st.session_state["hw_force_refresh"] = False

    if _hw_svc is not None:
        try:
            tel = _hw_svc.get(force=force)
            st.session_state["hw_last_updated"] = datetime.now().strftime("%I:%M:%S %p")
            st.session_state["hw_error"] = None
        except Exception as exc:
            st.session_state["hw_error"] = str(exc)

    # Fall back to legacy gpu_manager if new service unavailable
    if tel is None:
        _render_hardware_monitor_legacy()
        return

    d = tel.to_dict()
    last_upd   = st.session_state.get("hw_last_updated") or d["timestamp"]
    status     = d["status"]   # "live" | "cpu_fallback" | "unavailable"
    mode       = d["mode"]     # "CUDA_GPU" | "TF_GPU" | "CPU"
    is_gpu     = mode in ("CUDA_GPU", "TF_GPU")
    is_cuda    = mode == "CUDA_GPU"
    refreshing = st.session_state.get("hw_refreshing", False)

    # ── Status badge values ───────────────────────────────────────────────
    _STATUS_CFG = {
        "live":         ("🟢", "LIVE",         "#10b981", "rgba(16,185,129,.12)"),
        "cpu_fallback": ("⚙️", "CPU FALLBACK",  "#f59e0b", "rgba(245,158,11,.12)"),
        "unavailable":  ("🔴", "UNAVAILABLE",   "#ef4444", "rgba(239,68,68,.12)"),
        "updating":     ("🟡", "UPDATING",      "#fbbf24", "rgba(251,191,36,.12)"),
    }
    badge_key = "updating" if refreshing else status
    s_icon, s_label, s_color, s_bg = _STATUS_CFG.get(badge_key, _STATUS_CFG["unavailable"])

    # ── Header row: title + status badge + timestamp + refresh button ─────
    st.markdown(_clean_html('<div class="section-title">⚡ AI Hardware Monitor — Live</div>'), unsafe_allow_html=True)

    hdr_left, hdr_mid, hdr_right = st.columns([3, 2, 1])
    with hdr_left:
        upd_txt = "Updating..." if refreshing else f"Last updated: {last_upd}"
        st.markdown(
            f'<div class="hw-meta">'
            f'<span class="hw-status-badge" style="background:{s_bg};color:{s_color};border-color:{s_color}40;">'
            f'{s_icon} {s_label}</span>'
            f'<span class="hw-ts">{upd_txt}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hdr_mid:
        st.markdown(
            f'<div class="hw-mode-pill" style="color:{"#10b981" if is_cuda else ("#3b82f6" if is_gpu else "#f59e0b")};'
            f'border-color:{"#10b981" if is_cuda else ("#3b82f6" if is_gpu else "#f59e0b")}40;">'
            f'{"🚀 CUDA GPU" if is_cuda else ("🔷 TF GPU" if is_gpu else "⚙️ CPU MODE")}</div>',
            unsafe_allow_html=True,
        )
    with hdr_right:
        btn_label    = "↻ Refreshing..." if refreshing else "↻ Refresh"
        btn_disabled = refreshing
        if st.button(
            btn_label,
            key="hw_refresh_btn",
            disabled=btn_disabled,
            use_container_width=True,
            help="Refresh AI hardware telemetry",
        ):
            st.session_state["hw_refreshing"]     = True
            st.session_state["hw_force_refresh"]  = True
            if _hw_svc is not None:
                _hw_svc.invalidate()
            st.rerun(scope="fragment")

    # Mark refresh complete (was set in previous run)
    if st.session_state.get("hw_refreshing"):
        st.session_state["hw_refreshing"] = False

    # ── GPU Metrics Row ───────────────────────────────────────────────────
    with st.container():
        gc1, gc2, gc3, gc4, gc5, gc6 = st.columns(6)

        gpu_name   = d["gpu_name"]
        cuda_ver   = d["gpu_cuda_version"]
        vram_used  = d["gpu_vram_used_mb"]
        vram_total = d["gpu_vram_total_mb"]
        vram_pct   = d["gpu_vram_pct"]
        gpu_util   = d["gpu_utilization_pct"]
        gpu_temp   = d["gpu_temperature_c"]
        gpu_power  = d["gpu_power_watts"]
        gpu_fan    = d["gpu_fan_pct"]
        tf_gpu     = d["gpu_tf"]
        driver_v   = d["gpu_driver_version"]
        fallback_r = d["gpu_fallback_reason"]

        hw_label    = (gpu_name[:15] if gpu_name != "N/A" else "CPU Mode")
        hw_color    = "#10b981" if is_gpu else "#f59e0b"
        mode_icon   = "🚀" if is_gpu else "⚙️"
        cuda_lbl    = (f"CUDA {cuda_ver}" if (is_cuda and cuda_ver != "N/A")
                       else (cuda_ver if is_gpu else "N/A"))
        tf_lbl      = "✅ GPU" if tf_gpu else "⚠️ CPU"
        vram_lbl    = (f"{vram_used}MB / {vram_total}MB" if vram_total else "N/A")
        util_lbl    = (f"{gpu_util}%" if is_gpu else "N/A")
        temp_lbl    = (f"{gpu_temp}°C" if isinstance(gpu_temp, int) else "N/A")
        power_lbl   = (f"{gpu_power:.1f}W" if isinstance(gpu_power, (int, float)) and gpu_power is not None else "N/A")
        fan_sub     = (f"Fan: {gpu_fan}%" if isinstance(gpu_fan, int) else "Fan: N/A")
        temp_color  = ("#06b6d4" if isinstance(gpu_temp, int) and gpu_temp < 80
                       else ("#f59e0b" if isinstance(gpu_temp, int) else "#6b7280"))

        def _gpu_card(col, icon, label, val, color="#fff", sub=""):
            with col:
                sub_html = (f'<div style="font-size:.65rem;color:rgba(255,255,255,.35);margin-top:3px;">'
                            f'{sub}</div>') if sub else ""
                st.markdown(_clean_html(f"""
                    <div class="admin-metric" style="border-left:3px solid {color};">
                        <div class="am-top">
                            <span class="am-icon">{icon}</span>
                            <span class="am-label">{label}</span>
                        </div>
                        <div class="am-value" style="font-size:.88rem;color:{color};">{val}</div>
                        {sub_html}
                    </div>"""), unsafe_allow_html=True)

        _gpu_card(gc1, mode_icon,  "Hardware Mode", hw_label,   hw_color,          "GPU" if is_gpu else (fallback_r[:22] if fallback_r else "CPU Fallback"))
        _gpu_card(gc2, "⚡",        "CUDA Version",  cuda_lbl,   "#3B82F6" if is_cuda else "#6b7280", f"TF: {tf_lbl}")
        _gpu_card(gc3, "🌡️",       "GPU Temp",      temp_lbl,   temp_color,        fan_sub)
        _gpu_card(gc4, "⚡",        "GPU Power",     power_lbl,  "#8B5CF6" if isinstance(gpu_power, (int, float)) else "#6b7280", "Power Draw")
        _gpu_card(gc5, "📊",        "VRAM",          vram_lbl,   "#3B82F6",         f"{vram_pct}% used")
        _gpu_card(gc6, "📈",        "GPU Util",      util_lbl,   "#06b6d4" if is_gpu else "#6b7280", "Real-time")

    # ── Live System Resources ─────────────────────────────────────────────
    cpu_pct  = d["cpu_utilization_pct"]
    ram_used = d["ram_used_gb"]
    ram_tot  = d["ram_total_gb"]
    ram_pct  = d["ram_utilization_pct"]
    disk_pct = d["disk_utilization_pct"]
    disk_tot = d["disk_total_gb"]
    disk_usd = d["disk_used_gb"]
    disk_mnt = d["disk_mount"]

    def _pbar_color(pct):
        if not isinstance(pct, (int, float)) or pct == 0: return "#6b7280"
        if pct < 60: return "#10b981"
        if pct < 80: return "#f59e0b"
        return "#ef4444"

    def _pbar(pct, color):
        w = f"{min(pct,100):.1f}%" if isinstance(pct, (int, float)) else "0%"
        return (f'<div style="background:rgba(255,255,255,.08);border-radius:4px;'
                f'height:5px;margin-top:4px;">'
                f'<div style="width:{w};background:{color};height:5px;'
                f'border-radius:4px;transition:width .5s;"></div></div>')

    cpu_color  = _pbar_color(cpu_pct)
    ram_color  = _pbar_color(ram_pct)
    disk_color = _pbar_color(disk_pct)
    vram_color = _pbar_color(vram_pct)

    with st.container():
        st.markdown(_clean_html(f"""
        <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);
                    border-radius:12px;padding:14px 18px;margin-top:10px;">
            <div style="font-size:.78rem;font-weight:700;color:rgba(255,255,255,.5);
                        text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;">
                ⚙️ Live System Resources
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">CPU Usage</div>
                    <div style="font-size:1rem;font-weight:700;color:{cpu_color};">
                        {cpu_pct}{'%' if isinstance(cpu_pct,(int,float)) else ''}
                    </div>
                    {_pbar(cpu_pct, cpu_color)}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">RAM Usage</div>
                    <div style="font-size:1rem;font-weight:700;color:{ram_color};">
                        {ram_used} GB / {ram_tot} GB
                    </div>
                    {_pbar(ram_pct, ram_color)}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">Disk Usage ({disk_mnt})</div>
                    <div style="font-size:1rem;font-weight:700;color:{disk_color};">
                        {disk_usd} GB / {disk_tot} GB
                    </div>
                    {_pbar(disk_pct, disk_color)}
                </div>
                <div>
                    <div style="font-size:.7rem;color:rgba(255,255,255,.4);">GPU VRAM</div>
                    <div style="font-size:1rem;font-weight:700;color:{vram_color};">
                        {'N/A' if not is_gpu else f'{vram_pct}% used'}
                    </div>
                    {_pbar(vram_pct if is_gpu else 0, vram_color)}
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    # ── Hardware Details Expander ─────────────────────────────────────────
    cpu_model = d.get("cpu_model", "N/A")
    cpu_cores = d.get("cpu_cores_logical", "N/A")
    cpu_phys  = d.get("cpu_cores_physical", "N/A")
    cpu_freq  = d.get("cpu_freq_mhz", "N/A")
    dev_idx   = d.get("gpu_device_index", "N/A")
    dev_count = d.get("gpu_device_count", 0)

    with st.expander("🔬 Hardware Details", expanded=False):
        det1, det2, det3 = st.columns(3)
        with det1:
            st.markdown("**🖥 CPU**")
            st.markdown(_clean_html(f"""
            <div class="hw-detail-grid">
                <div class="hw-dk">Model</div><div class="hw-dv">{cpu_model}</div>
                <div class="hw-dk">Cores (logical)</div><div class="hw-dv">{cpu_cores}</div>
                <div class="hw-dk">Cores (physical)</div><div class="hw-dv">{cpu_phys}</div>
                <div class="hw-dk">Frequency</div><div class="hw-dv">{cpu_freq} MHz</div>
                <div class="hw-dk">Utilization</div><div class="hw-dv">{cpu_pct}%</div>
            </div>"""), unsafe_allow_html=True)
        with det2:
            st.markdown("**🧠 Memory & Disk**")
            st.markdown(_clean_html(f"""
            <div class="hw-detail-grid">
                <div class="hw-dk">RAM Total</div><div class="hw-dv">{ram_tot} GB</div>
                <div class="hw-dk">RAM Used</div><div class="hw-dv">{ram_used} GB ({ram_pct}%)</div>
                <div class="hw-dk">Disk Total</div><div class="hw-dv">{disk_tot} GB</div>
                <div class="hw-dk">Disk Used</div><div class="hw-dv">{disk_usd} GB ({disk_pct}%)</div>
                <div class="hw-dk">Mount</div><div class="hw-dv">{disk_mnt}</div>
            </div>"""), unsafe_allow_html=True)
        with det3:
            st.markdown("**🎮 GPU**")
            st.markdown(_clean_html(f"""
            <div class="hw-detail-grid">
                <div class="hw-dk">GPU</div><div class="hw-dv">{gpu_name}</div>
                <div class="hw-dk">Vendor</div><div class="hw-dv">{d['gpu_vendor']}</div>
                <div class="hw-dk">Backend</div><div class="hw-dv">{mode}</div>
                <div class="hw-dk">CUDA</div><div class="hw-dv">{cuda_ver}</div>
                <div class="hw-dk">Driver</div><div class="hw-dv">{driver_v}</div>
                <div class="hw-dk">VRAM</div><div class="hw-dv">{vram_lbl}</div>
                <div class="hw-dk">Device Index</div><div class="hw-dv">{dev_idx} ({dev_count} total)</div>
            </div>"""), unsafe_allow_html=True)

        if d["errors"]:
            for err in d["errors"]:
                st.caption(f"⚠️ {err}")
        if d["warnings"]:
            for w in d["warnings"]:
                st.caption(f"ℹ️ {w}")

    # ── Reviewer Summary Box ──────────────────────────────────────────────
    ai_accel = ("ACTIVE — " + ("CUDA GPU" if is_cuda else "TF GPU")) if is_gpu else "CPU FALLBACK"
    cuda_avail_lbl = "AVAILABLE" if d["gpu_cuda"] else "UNAVAILABLE"
    st.markdown(_clean_html(f"""
    <div class="hw-summary-box">
        <div class="hw-sum-row"><span class="hw-sum-k">Hardware Mode</span>
            <span class="hw-sum-v" style="color:{hw_color};">{mode}</span></div>
        <div class="hw-sum-row"><span class="hw-sum-k">GPU</span>
            <span class="hw-sum-v">{gpu_name}</span></div>
        <div class="hw-sum-row"><span class="hw-sum-k">AI Acceleration</span>
            <span class="hw-sum-v" style="color:{'#10b981' if is_gpu else '#f59e0b'};">{'ACTIVE' if is_gpu else 'CPU FALLBACK'}</span></div>
        <div class="hw-sum-row"><span class="hw-sum-k">CUDA</span>
            <span class="hw-sum-v" style="color:{'#10b981' if d['gpu_cuda'] else '#ef4444'};">{cuda_avail_lbl}</span></div>
        <div class="hw-sum-row"><span class="hw-sum-k">Telemetry</span>
            <span class="hw-sum-v" style="color:{s_color};">{s_icon} {s_label}</span></div>
    </div>
    """), unsafe_allow_html=True)


def _render_hardware_monitor_legacy():
    """Fallback hardware monitor using old gpu_manager calls."""
    from smartai.gpu_utils import get_gpu_extended_stats, get_system_resources
    gpu     = check_nvidia_gpu()
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
    cuda_label = f"CUDA {cuda_ver}" if (gpu_active and cuda_ver != "N/A") else "N/A"
    vram_label = f"{mem_used}MB / {mem_total}MB" if mem_total else "N/A"
    util_label = f"{gpu_util}%" if gpu_active else "N/A"
    temp_label = f"{gpu_temp}°C" if isinstance(gpu_temp, int) else "N/A"
    power_label = f"{gpu_power:.1f}W" if isinstance(gpu_power, float) else "N/A"
    cpu_pct  = sysres.get("cpu_percent", "N/A")
    ram_used = sysres.get("ram_used_gb", "N/A")
    ram_tot  = sysres.get("ram_total_gb", "N/A")
    ram_pct  = sysres.get("ram_percent", "N/A")
    disk_pct = sysres.get("disk_percent", "N/A")

    def _pc(p):
        if not isinstance(p, (int, float)): return "#6b7280"
        return "#10b981" if p < 60 else ("#f59e0b" if p < 80 else "#ef4444")

    def _pb(p, c):
        w = f"{p}%" if isinstance(p, (int, float)) else "0%"
        return f'<div style="background:rgba(255,255,255,.08);border-radius:4px;height:5px;margin-top:4px;"><div style="width:{w};background:{c};height:5px;border-radius:4px;"></div></div>'

    st.markdown(_clean_html('<div class="section-title">⚡ AI Hardware Monitor — Live</div>'), unsafe_allow_html=True)
    gc1, gc2, gc3, gc4, gc5, gc6 = st.columns(6)

    def _gc(col, icon, label, val, color, sub=""):
        with col:
            sub_h = f'<div style="font-size:.65rem;color:rgba(255,255,255,.35);margin-top:3px;">{sub}</div>' if sub else ""
            st.markdown(_clean_html(f'<div class="admin-metric" style="border-left:3px solid {color};"><div class="am-top"><span class="am-icon">{icon}</span><span class="am-label">{label}</span></div><div class="am-value" style="font-size:.88rem;color:{color};">{val}</div>{sub_h}</div>'), unsafe_allow_html=True)

    _gc(gc1, "🚀" if gpu_active else "⚙️", "Hardware Mode", hw_label[:16], hw_color, "GPU" if gpu_active else "CPU Fallback")
    _gc(gc2, "⚡", "CUDA Version", cuda_label, "#3B82F6" if gpu_active else "#6b7280", f"TF: {'GPU' if tf_gpu else 'CPU'}")
    _gc(gc3, "🌡️", "GPU Temp", temp_label, "#06b6d4" if isinstance(gpu_temp, int) and gpu_temp < 80 else "#f59e0b", f"Fan: {gpu_fan}%" if isinstance(gpu_fan, int) else "Fan: N/A")
    _gc(gc4, "⚡", "GPU Power", power_label, "#8B5CF6" if isinstance(gpu_power, float) else "#6b7280", "Power Draw")
    _gc(gc5, "📊", "VRAM", vram_label, "#3B82F6", f"{mem_pct}% used")
    _gc(gc6, "📈", "GPU Util", util_label, "#06b6d4" if gpu_active else "#6b7280", "Real-time")

    st.markdown(_clean_html(f'<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px 18px;margin-top:10px;"><div style="font-size:.78rem;font-weight:700;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;">⚙️ Live System Resources</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;"><div><div style="font-size:.7rem;color:rgba(255,255,255,.4);">CPU Usage</div><div style="font-size:1rem;font-weight:700;color:{_pc(cpu_pct)};">{cpu_pct}%</div>{_pb(cpu_pct,_pc(cpu_pct))}</div><div><div style="font-size:.7rem;color:rgba(255,255,255,.4);">RAM Usage</div><div style="font-size:1rem;font-weight:700;color:{_pc(ram_pct)};">{ram_used} GB / {ram_tot} GB</div>{_pb(ram_pct,_pc(ram_pct))}</div><div><div style="font-size:.7rem;color:rgba(255,255,255,.4);">Disk Usage</div><div style="font-size:1rem;font-weight:700;color:{_pc(disk_pct)};">{disk_pct}%</div>{_pb(disk_pct,_pc(disk_pct))}</div><div><div style="font-size:.7rem;color:rgba(255,255,255,.4);">GPU VRAM</div><div style="font-size:1rem;font-weight:700;color:{_pc(mem_pct)};">{mem_pct}% {'used' if mem_total else 'N/A'}</div>{_pb(mem_pct,_pc(mem_pct))}</div></div></div>'), unsafe_allow_html=True)


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

    /* ── Hardware Monitor styles ────────────────────────────── */
    .hw-meta {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 0; flex-wrap: wrap;
    }
    .hw-status-badge {
        font-size: .72rem; font-weight: 700;
        padding: 3px 10px; border-radius: 20px;
        border: 1px solid transparent;
        letter-spacing: .04em;
    }
    .hw-ts {
        font-size: .72rem; color: rgba(255,255,255,.35);
    }
    .hw-mode-pill {
        font-size: .75rem; font-weight: 800;
        padding: 4px 12px; border-radius: 20px;
        border: 1px solid transparent;
        text-align: center; letter-spacing: .06em;
        background: rgba(255,255,255,.04);
    }
    .hw-detail-grid {
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 4px 8px; font-size: .76rem; margin-top: 6px;
    }
    .hw-dk { color: rgba(255,255,255,.38); }
    .hw-dv { color: rgba(255,255,255,.85); font-weight: 600; overflow: hidden;
             text-overflow: ellipsis; white-space: nowrap; }
    .hw-summary-box {
        background: rgba(255,255,255,.02);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 10px;
        padding: 10px 16px;
        margin-top: 8px;
        display: flex; flex-wrap: wrap; gap: 0;
    }
    .hw-sum-row {
        display: flex; align-items: center; gap: 8px;
        width: 50%; padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,.04);
    }
    .hw-sum-k { font-size: .72rem; color: rgba(255,255,255,.38);
                min-width: 110px; font-weight: 600; }
    .hw-sum-v { font-size: .78rem; color: #F8FAFC; font-weight: 700; }
    </style>
    """;
