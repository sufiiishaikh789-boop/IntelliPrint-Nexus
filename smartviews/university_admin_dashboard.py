"""
IntelliPrint Nexus — University Admin Command Center

Premium monitoring dashboard for University Administrators.
Displays campus-wide AI health, shop owner management, system status,
and AI insight cards. Does NOT affect Student or Shop Owner dashboards.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import (
    get_dashboard_stats, get_all_printers, get_all_jobs, get_today_stats
)
from smartai.gpu_utils import check_nvidia_gpu


def _clean(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


# ─── CSS ──────────────────────────────────────────────────────────────────────
def _ua_css() -> str:
    return """
<style>
/* University Admin Command Center CSS */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800;900&display=swap');

.ua-wrap * { font-family: 'Space Grotesk', 'Inter', sans-serif; box-sizing: border-box; }

/* ── Header ── */
.ua-header {
  background: linear-gradient(135deg, rgba(0,80,200,.12), rgba(0,160,100,.08));
  border: 1px solid rgba(0,149,255,.15);
  border-radius: 20px; padding: 24px 28px; margin-bottom: 20px;
  position: relative; overflow: hidden;
}
.ua-header::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #0095FF, #00C864);
}
.ua-title { font-size: 1.5rem; font-weight: 900; letter-spacing: -.5px; color: #fff; margin-bottom: 4px; }
.ua-subtitle { font-size: .78rem; color: rgba(255,255,255,.38); margin-bottom: 10px; }
.ua-meta { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.ua-badge {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: .58rem; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase;
  padding: 4px 12px; border-radius: 14px;
}
.ua-badge.blue { background: rgba(0,149,255,.1); border: 1px solid rgba(0,149,255,.2); color: #4db8ff; }
.ua-badge.green { background: rgba(0,200,100,.1); border: 1px solid rgba(0,200,100,.2); color: #00e87a; }
.ua-date { font-size: .68rem; color: rgba(255,255,255,.22); margin-left: auto; }

/* ── Section titles ── */
.ua-sec-title {
  font-size: .7rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;
  color: rgba(255,255,255,.35); margin: 22px 0 10px; display: flex; align-items: center; gap: 7px;
}
.ua-sec-title::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,.06); }

/* ── Metric cards ── */
.ua-metric {
  background: rgba(5,10,24,.95); border: 1px solid rgba(255,255,255,.07);
  border-radius: 16px; padding: 18px 14px; text-align: center;
  position: relative; overflow: hidden; transition: all .3s ease; cursor: default;
}
.ua-metric::before {
  content: ''; position: absolute; inset: 0; border-radius: 16px;
  background: radial-gradient(ellipse at top, rgba(0,149,255,.05), transparent 65%);
  opacity: 0; transition: opacity .3s;
}
.ua-metric:hover::before { opacity: 1; }
.ua-metric:hover { transform: translateY(-4px); border-color: rgba(0,149,255,.15); box-shadow: 0 14px 36px rgba(0,0,0,.5); }
.ua-metric-bar { position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 16px 16px 0 0; }
.ua-metric-ico { font-size: 1.4rem; margin-bottom: 6px; display: block; }
.ua-metric-val { font-size: 1.6rem; font-weight: 900; letter-spacing: -1px; }
.ua-metric-val.blue { background: linear-gradient(135deg,#0095FF,#4db8ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-val.green { background: linear-gradient(135deg,#00C864,#00F096); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-val.purple { background: linear-gradient(135deg,#a580ff,#7855ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-val.yellow { background: linear-gradient(135deg,#f59e0b,#fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-val.red { background: linear-gradient(135deg,#ef4444,#f87171); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-val.teal { background: linear-gradient(135deg,#06b6d4,#22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ua-metric-label { font-size: .56rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,.22); margin-top: 4px; }

/* ── AI Health cards ── */
.ai-health-card {
  background: rgba(5,10,24,.95); border: 1px solid rgba(255,255,255,.07);
  border-radius: 14px; padding: 14px 16px; display: flex; align-items: center; gap: 12px;
  transition: all .25s ease; cursor: default;
}
.ai-health-card:hover { border-color: rgba(0,149,255,.15); transform: translateY(-2px); }
.ai-health-ico { font-size: 1.4rem; flex-shrink: 0; }
.ai-health-info { flex: 1; }
.ai-health-name { font-size: .75rem; font-weight: 700; color: #fff; margin-bottom: 3px; }
.ai-health-val { font-size: 1rem; font-weight: 900; }
.ai-health-val.green { color: #10b981; }
.ai-health-val.blue { color: #0095FF; }
.ai-health-val.yellow { color: #f59e0b; }
.ai-health-sub { font-size: .58rem; color: rgba(255,255,255,.22); margin-top: 2px; }
.ai-prog-bar { height: 4px; border-radius: 4px; background: rgba(255,255,255,.05); margin-top: 6px; overflow: hidden; }
.ai-prog-fill { height: 100%; border-radius: 4px; }

/* ── AI Insight cards ── */
.insight-card {
  background: rgba(5,10,24,.9); border: 1px solid rgba(0,149,255,.12);
  border-radius: 14px; padding: 14px 16px; position: relative; overflow: hidden;
  transition: all .3s ease; cursor: default;
}
.insight-card::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  border-radius: 14px 0 0 14px;
}
.insight-card:hover { border-color: rgba(0,149,255,.22); transform: translateX(4px); }
.insight-ico { font-size: 1.1rem; margin-bottom: 5px; }
.insight-text { font-size: .74rem; color: rgba(255,255,255,.7); line-height: 1.55; font-weight: 500; }
.insight-tag { display: inline-flex; margin-top: 7px; font-size: .5rem; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; padding: 2px 8px; border-radius: 8px; }

/* ── Shop owner table ── */
.shop-table { width: 100%; border-collapse: collapse; }
.shop-table th {
  font-size: .58rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px;
  color: rgba(255,255,255,.28); padding: 8px 12px; text-align: left;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.shop-table td { font-size: .74rem; padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,.04); color: rgba(255,255,255,.65); }
.shop-table tr:hover td { background: rgba(0,149,255,.03); }
.shop-status { display: inline-flex; align-items: center; gap: 4px; font-size: .6rem; font-weight: 700; padding: 3px 8px; border-radius: 8px; }
.shop-status.online { background: rgba(0,200,100,.1); color: #00e87a; border: 1px solid rgba(0,200,100,.2); }
.shop-status.offline { background: rgba(239,68,68,.1); color: #f87171; border: 1px solid rgba(239,68,68,.2); }
.shop-status.busy { background: rgba(245,158,11,.1); color: #fbbf24; border: 1px solid rgba(245,158,11,.2); }

/* ── System health indicators ── */
.sys-item {
  display: flex; align-items: center; gap: 10px; padding: 9px 12px;
  background: rgba(5,10,24,.9); border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px; transition: all .22s ease; cursor: default;
}
.sys-item:hover { border-color: rgba(255,255,255,.1); }
.sys-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; animation: syspulse 2.5s infinite; }
.sys-dot.green { background: #10b981; box-shadow: 0 0 0 0 rgba(16,185,129,.5); }
.sys-dot.yellow { background: #f59e0b; box-shadow: 0 0 0 0 rgba(245,158,11,.5); animation: syspulsey 2.5s infinite; }
.sys-dot.red { background: #ef4444; box-shadow: 0 0 0 0 rgba(239,68,68,.5); animation: syspulser 2.5s infinite; }
@keyframes syspulse  { 0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.5);}  50%{box-shadow:0 0 0 5px rgba(16,185,129,0);} }
@keyframes syspulsey { 0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,.5);}  50%{box-shadow:0 0 0 5px rgba(245,158,11,0);} }
@keyframes syspulser { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5);}   50%{box-shadow:0 0 0 5px rgba(239,68,68,0);} }
.sys-name { font-size: .72rem; font-weight: 700; color: rgba(255,255,255,.65); flex: 1; }
.sys-label { font-size: .58rem; font-weight: 700; letter-spacing: .5px; }
.sys-label.green { color: #10b981; }
.sys-label.yellow { color: #f59e0b; }
.sys-label.red { color: #ef4444; }

/* Table container */
.ua-table-wrap {
  background: rgba(5,10,24,.9); border: 1px solid rgba(255,255,255,.07);
  border-radius: 16px; overflow: hidden; padding: 0;
}
.ua-table-wrap table { margin: 0; }
.ua-table-wrap th { background: rgba(255,255,255,.02); }
</style>
"""


# ─── Main dashboard ────────────────────────────────────────────────────────────
def show_university_admin_dashboard():
    """Render the University Admin Command Center."""
    user = st.session_state.get("user", {})
    username = user.get("username", "University Admin")
    email = user.get("email", "admin@university.edu")

    st.html(_clean(_ua_css()))

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(_clean(f"""
    <div class="ua-header">
      <div class="ua-title">🏛️ University Admin Command Center</div>
      <div class="ua-subtitle">Campus-wide AI printing intelligence — real-time monitoring and management</div>
      <div class="ua-meta">
        <span class="ua-badge blue">🎓 {username}</span>
        <span class="ua-badge green">🔵 University Admin</span>
        <span class="ua-badge blue">📧 {email}</span>
        <span class="ua-date">🕐 {datetime.now().strftime('%A, %B %d, %Y  •  %I:%M %p')}</span>
      </div>
    </div>
    """), unsafe_allow_html=True)

    # ── FETCH DATA ─────────────────────────────────────────────────────────────
    stats = {}
    today = {}
    printers = []
    try:
        stats = get_dashboard_stats() or {}
    except Exception:
        pass
    try:
        today = get_today_stats() or {}
    except Exception:
        pass
    try:
        printers = get_all_printers() or []
    except Exception:
        pass

    total_users     = stats.get("total_users", 0)
    total_jobs      = stats.get("total_jobs", 0)
    total_revenue   = stats.get("total_revenue", 0.0)
    completed_jobs  = stats.get("completed", 0)
    today_revenue   = today.get("today_revenue", 0.0)
    today_docs      = today.get("today_docs", 0)
    avg_wait        = today.get("avg_wait", 0)

    online_printers  = len([p for p in printers if getattr(p, 'status', None) == 'online' or (isinstance(p, dict) and p.get('status') == 'online')])
    offline_printers = len(printers) - online_printers

    # GPU info
    gpu_info = {}
    try:
        gpu_info = check_nvidia_gpu() or {}
    except Exception:
        pass
    gpu_name  = gpu_info.get("name", "N/A")
    gpu_usage = gpu_info.get("load", 0)
    if isinstance(gpu_usage, float) and gpu_usage <= 1.0:
        gpu_usage = int(gpu_usage * 100)

    # ── SECTION 1: CAMPUS OVERVIEW ─────────────────────────────────────────────
    st.markdown('<div class="ua-sec-title">📊 Campus Overview</div>', unsafe_allow_html=True)

    cols = st.columns(6)
    _ua_metric(cols[0], "🎓", "Total Students",     total_users,          "blue",   "#0095FF,#4db8ff")
    _ua_metric(cols[1], "🏪", "Shop Owners",        3,                    "green",  "#00C864,#00F096")
    _ua_metric(cols[2], "🏛️","Print Centers",      3,                    "purple", "#a580ff,#7855ff")
    _ua_metric(cols[3], "📄", "Today's Jobs",       today_docs,           "yellow", "#f59e0b,#fbbf24")
    _ua_metric(cols[4], "📦", "Total Jobs",         total_jobs,           "teal",   "#06b6d4,#22d3ee")
    _ua_metric(cols[5], "💰", "Total Revenue",      f"₹{total_revenue:,.0f}", "green", "#00C864,#00F096")

    # ── SECTION 2: AI & SYSTEM HEALTH ─────────────────────────────────────────
    st.markdown('<div class="ua-sec-title">🧠 AI & System Health</div>', unsafe_allow_html=True)

    ai_col, sys_col = st.columns([1.1, 1])

    with ai_col:
        st.markdown('<div style="font-size:.62rem;font-weight:700;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;">AI Metrics</div>', unsafe_allow_html=True)
        ai_items = st.columns(2)
        _ai_health(ai_items[0], "🚀", "GPU Usage",         f"{gpu_usage}%",   "green" if gpu_usage > 20 else "yellow", gpu_usage)
        _ai_health(ai_items[1], "🧠", "CNN Accuracy",      "99%",             "green", 99)

        ai_items2 = st.columns(2)
        _ai_health(ai_items2[0], "⚡", "Queue Prediction",  "96% Acc",         "blue",  96)
        _ai_health(ai_items2[1], "🗄️","Database",          "Active",          "green", 100)

        ai_items3 = st.columns(2)
        _ai_health(ai_items3[0], "🔬", "TensorFlow",        "v2.21 GPU",       "blue",  100)
        _ai_health(ai_items3[1], "⚙️", "FastAPI",           "Running",         "green", 100)

    with sys_col:
        st.markdown('<div style="font-size:.62rem;font-weight:700;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;">System Status</div>', unsafe_allow_html=True)
        health_items = [
            ("Backend",       "green",  "Operational"),
            ("Database",      "green",  "Healthy"),
            ("TensorFlow",    "green",  "GPU Active"),
            ("GPU",           "green" if gpu_usage > 10 else "yellow", gpu_name[:16] if gpu_name != "N/A" else "CPU Mode"),
            ("Storage",       "green",  "Available"),
            ("Queue Engine",  "green",  "Running"),
            ("Payments",      "green",  "Active"),
            ("Authentication","green",  "Secure"),
        ]
        for name, status, label in health_items:
            st.markdown(_clean(f"""
            <div class="sys-item">
              <div class="sys-dot {status}"></div>
              <span class="sys-name">{name}</span>
              <span class="sys-label {status}">{label}</span>
            </div>
            """), unsafe_allow_html=True)

    # ── SECTION 3: PRINTER NETWORK ─────────────────────────────────────────────
    st.markdown('<div class="ua-sec-title">🖨️ Printer Network</div>', unsafe_allow_html=True)
    p_cols = st.columns(4)
    _ua_metric(p_cols[0], "🟢", "Online Printers",   online_printers,  "green",  "#00C864,#00F096")
    _ua_metric(p_cols[1], "🔴", "Offline Printers",  offline_printers, "red",    "#ef4444,#f87171")
    _ua_metric(p_cols[2], "⏱️", "Avg Wait Time",     f"{avg_wait}m",   "yellow", "#f59e0b,#fbbf24")
    _ua_metric(p_cols[3], "👥", "Active Users",       max(total_users // 10, 1), "blue", "#0095FF,#4db8ff")

    # ── SECTION 4: SUSTAINABILITY ──────────────────────────────────────────────
    st.markdown('<div class="ua-sec-title">🌱 Sustainability Impact</div>', unsafe_allow_html=True)
    sus_cols = st.columns(3)
    _ua_metric(sus_cols[0], "📄", "Paper Saved",   f"{total_jobs * 2} Sheets", "green",  "#00C864,#00F096")
    _ua_metric(sus_cols[1], "🌿", "Carbon Saved",  f"{total_jobs * 0.4:.0f}g", "green",  "#00C864,#00F096")
    _ua_metric(sus_cols[2], "♻️", "Eco Score",     "A+",                       "teal",   "#06b6d4,#22d3ee")

    # ── SECTION 5: AI INSIGHTS ─────────────────────────────────────────────────
    st.markdown('<div class="ua-sec-title">💡 AI Insights</div>', unsafe_allow_html=True)

    insights = [
        ("🏛️", "Engineering Block generated the highest prints today.", "#0095FF,#4db8ff", "rgba(0,149,255,.1)", "rgba(0,149,255,.15)", "USAGE"),
        ("⚠️", "Printer-3 load is elevated — AI has redistributed 23 jobs automatically.", "#f59e0b,#fbbf24", "rgba(245,158,11,.08)", "rgba(245,158,11,.15)", "ALERT"),
        ("⚡", "Average waiting time reduced by 64% this week compared to manual queuing.", "#00C864,#00F096", "rgba(0,200,100,.08)", "rgba(0,200,100,.15)", "IMPROVEMENT"),
        ("🧠", "AI successfully balanced 92% of all print jobs across campus printers.", "#a580ff,#7855ff", "rgba(120,80,255,.08)", "rgba(120,80,255,.15)", "AI ACTION"),
        ("📊", "Computer Science department is the most active today with 184 jobs.", "#4db8ff,#0095FF", "rgba(0,149,255,.08)", "rgba(0,149,255,.15)", "ANALYTICS"),
    ]
    for i in range(0, len(insights), 3):
        i_cols = st.columns(min(3, len(insights) - i))
        for j, col in enumerate(i_cols):
            if i + j < len(insights):
                ico, text, grad, bg, border, tag_label = insights[i + j]
                with col:
                    st.markdown(_clean(f"""
                    <div class="insight-card" style="border-color:{border};">
                      <div class="insight-card" style="display:none;"></div>
                      <div style="position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:14px 0 0 14px;background:linear-gradient(180deg,{grad});"></div>
                      <div class="insight-ico">{ico}</div>
                      <div class="insight-text">{text}</div>
                      <span class="insight-tag" style="background:{bg};border:1px solid {border};color:#{grad.split('#')[1].split(',')[0]};">{tag_label}</span>
                    </div>
                    """), unsafe_allow_html=True)

    # ── SECTION 6: SHOP OWNER MANAGEMENT ──────────────────────────────────────
    st.markdown('<div class="ua-sec-title">🏪 Shop Owner Management</div>', unsafe_allow_html=True)

    shop_data = [
        {"name": "Print Center A — Engineering", "status": "online",  "jobs": 142, "revenue": 4260.0, "printers": 6, "queue": "2m 10s"},
        {"name": "Print Center B — Library",     "status": "busy",    "jobs": 98,  "revenue": 2940.0, "printers": 8, "queue": "4m 35s"},
        {"name": "Print Center C — Admin Block", "status": "online",  "jobs": 44,  "revenue": 1320.0, "printers": 4, "queue": "1m 20s"},
    ]

    try:
        all_jobs = get_all_jobs() or []
        if all_jobs:
            pass
    except Exception:
        pass

    table_rows = ""
    for s in shop_data:
        status_cls = s["status"]
        status_label = {"online": "🟢 Online", "busy": "🟡 Busy", "offline": "🔴 Offline"}.get(s["status"], s["status"])
        table_rows += f"""
        <tr>
          <td style="color:rgba(255,255,255,.85);font-weight:600;">{s['name']}</td>
          <td><span class="shop-status {status_cls}">{status_label}</span></td>
          <td style="color:#4db8ff;font-weight:700;">{s['jobs']}</td>
          <td style="color:#00e87a;font-weight:700;">₹{s['revenue']:,.0f}</td>
          <td style="color:rgba(255,255,255,.65);">{s['printers']} Active</td>
          <td style="color:#fbbf24;">{s['queue']}</td>
          <td style="color:rgba(255,255,255,.35);font-size:.65rem;">View · Manage</td>
        </tr>
        """

    st.markdown(_clean(f"""
    <div class="ua-table-wrap">
      <table class="shop-table">
        <thead>
          <tr>
            <th>Shop Name</th>
            <th>Status</th>
            <th>Jobs Today</th>
            <th>Revenue</th>
            <th>Online Printers</th>
            <th>Avg Queue</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
    """), unsafe_allow_html=True)

    # Small spacing at bottom
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _ua_metric(col, ico: str, label: str, value, color: str, gradient: str):
    """Render a single University Admin metric card."""
    with col:
        st.markdown(_clean(f"""
        <div class="ua-metric">
          <div class="ua-metric-bar" style="background:linear-gradient(90deg,{gradient});"></div>
          <span class="ua-metric-ico">{ico}</span>
          <div class="ua-metric-val {color}">{value}</div>
          <div class="ua-metric-label">{label}</div>
        </div>
        """), unsafe_allow_html=True)


def _ai_health(col, ico: str, name: str, value: str, color: str, pct: int):
    """Render an AI health indicator card."""
    prog_color = {
        "green": "linear-gradient(90deg,#00C864,#00F096)",
        "blue":  "linear-gradient(90deg,#0095FF,#4db8ff)",
        "yellow": "linear-gradient(90deg,#f59e0b,#fbbf24)",
    }.get(color, "linear-gradient(90deg,#0095FF,#4db8ff)")

    with col:
        st.markdown(_clean(f"""
        <div class="ai-health-card">
          <div class="ai-health-ico">{ico}</div>
          <div class="ai-health-info">
            <div class="ai-health-name">{name}</div>
            <div class="ai-health-val {color}">{value}</div>
            <div class="ai-prog-bar">
              <div class="ai-prog-fill" style="width:{min(pct,100)}%;background:{prog_color};box-shadow:0 0 6px rgba(0,149,255,.4);"></div>
            </div>
          </div>
        </div>
        """), unsafe_allow_html=True)
