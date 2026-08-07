"""
IntelliPrint Nexus - Enterprise Student Dashboard (Phase 3)
Comprehensive self-service portal with analytics, live jobs, notifications,
favorite printer, quick reprint, and activity feed.
"""

import streamlit as st
import re
from datetime import datetime

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


# ─── Status helpers ────────────────────────────────────────────────────────────

_STATUS_COLORS = {
    "pending":         "#f59e0b",
    "payment_pending": "#f59e0b",
    "queued":          "#3b82f6",
    "printing":        "#3B82F6",
    "completed":       "#10b981",
    "ready":           "#10b981",
    "collected":       "#6b7280",
    "cancelled":       "#ef4444",
    "failed":          "#ef4444",
}

_STATUS_ICONS = {
    "pending":         "⏳",
    "payment_pending": "💳",
    "queued":          "📋",
    "printing":        "🖨️",
    "completed":       "✅",
    "ready":           "📦",
    "collected":       "🎉",
    "cancelled":       "❌",
    "failed":          "⚠️",
}


def _scolor(status: str) -> str:
    return _STATUS_COLORS.get(status.lower(), "#6b7280")


def _sicon(status: str) -> str:
    return _STATUS_ICONS.get(status.lower(), "📄")


# ─── Main entry ───────────────────────────────────────────────────────────────

def show_student_dashboard():
    """Render the enterprise student dashboard."""
    user     = st.session_state.get("user", {})
    username = user.get("username", "Student")
    email    = user.get("email", "")
    user_id  = user.get("id", 0)

    st.html(_dashboard_css())

    # ── Data loading ──────────────────────────────────────────────────────────
    all_jobs = []
    analytics = {}
    fav_printer = None
    unread_count = 0
    printers = []

    try:
        from smartdb.crud import get_user_jobs, get_all_printers
        all_jobs = get_user_jobs(user_id) or []
        printers = get_all_printers() or []
    except Exception:
        pass

    try:
        from smartdb.crud_ext import (
            get_student_analytics, get_favorite_printer,
            get_notifications_unread_count,
        )
        analytics    = get_student_analytics(user_id) or {}
        fav_printer  = get_favorite_printer(user_id)
        unread_count = get_notifications_unread_count(user_id)
    except Exception:
        analytics = {}

    # Computed values
    active_jobs = [j for j in all_jobs if (j.get("status") or "").lower()
                   in ("pending", "payment_pending", "queued", "printing", "preparing")]
    printing_now = [j for j in all_jobs if (j.get("status") or "").lower() == "printing"]

    # ── Welcome card ──────────────────────────────────────────────────────────
    now_str = datetime.now().strftime("%A, %B %d, %Y")
    greeting = "Good morning" if datetime.now().hour < 12 else \
               "Good afternoon" if datetime.now().hour < 17 else "Good evening"

    st.html(f"""
    <div class="dash-welcome">
        <div class="dash-left">
            <div class="dash-greeting">{greeting}, <span class="dash-name">{username}</span> 👋</div>
            <div class="dash-meta">📧 {email}</div>
            <div class="dash-date">📅 {now_str}</div>
        </div>
        <div class="dash-right">
            {"<div class='dash-notif-badge'>🔔 " + str(unread_count) + " unread</div>" if unread_count > 0 else ""}
            {"<div class='dash-fav'>⭐ Favourite: <b>" + fav_printer + "</b></div>" if fav_printer else ""}
            <div class="dash-active-badge">{len(active_jobs)} active job(s)</div>
        </div>
    </div>
    """)

    # ── Metric grid — 6 cards ────────────────────────────────────────────────
    mc = st.columns(6)
    metrics = [
        ("📄", "Total Jobs",     analytics.get("total_jobs", len(all_jobs)),    "#60A5FA"),
        ("🗒️", "Docs Printed",   analytics.get("total_docs", 0),               "#3B82F6"),
        ("📑", "Total Pages",    analytics.get("total_pages", 0),              "#8B5CF6"),
        ("💰", "Total Spent",    f"₹{analytics.get('total_spent', 0):.0f}",    "#10B981"),
        ("♻️", "Paper Saved",    f"{analytics.get('paper_saved', 0)} sheets",  "#34D399"),
        ("🌿", "CO₂ Saved",      f"{analytics.get('co2_saved', 0):.2f} kg",   "#06B6D4"),
    ]
    for col, (icon, label, value, color) in zip(mc, metrics):
        with col:
            st.html(f"""
            <div class="dash-metric" style="border-top:3px solid {color};">
                <div class="dm-icon">{icon}</div>
                <div class="dm-value" style="color:{color};">{value}</div>
                <div class="dm-label">{label}</div>
            </div>
            """)

    # Second row of metrics
    mc2 = st.columns(6)
    metrics2 = [
        ("🖨️", "Printing Now",  len(printing_now),                            "#F59E0B"),
        ("📬", "Today's Jobs",   analytics.get("todays_jobs", 0),             "#06B6D4"),
        ("✅", "Completed",      analytics.get("completed_jobs", 0),          "#10B981"),
        ("⏱️", "Avg Wait",       f"{analytics.get('avg_wait_min', 0)} min",   "#A78BFA"),
        ("🖤", "B&W Jobs",       analytics.get("bw_jobs", 0),                  "#94A3B8"),
        ("🎨", "Colour Jobs",    analytics.get("color_jobs", 0),               "#F472B6"),
    ]
    for col, (icon, label, value, color) in zip(mc2, metrics2):
        with col:
            st.html(f"""
            <div class="dash-metric" style="border-top:3px solid {color};">
                <div class="dm-icon">{icon}</div>
                <div class="dm-value" style="color:{color};">{value}</div>
                <div class="dm-label">{label}</div>
            </div>
            """)

    st.html('<div style="height:8px;"></div>')

    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.html('<div class="section-title">⚡ Quick Actions</div>')
    qa = st.columns(5)
    actions = [
        ("📤 Upload & Print",  "Submit Print Job"),
        ("📋 Track Queue",     "Track Order"),
        ("📜 Print History",   "My Print Jobs"),
        ("📊 Analytics",       "Analytics"),
        ("🔔 Notifications",   "Notifications"),
    ]
    for col, (label, page) in zip(qa, actions):
        with col:
            if st.button(label, use_container_width=True, key=f"qa_{page}"):
                st.session_state["current_page"] = page
                st.rerun()

    # ── Active Jobs ───────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.html('<div class="section-title">🖨️ Active Print Jobs</div>')
        if not active_jobs:
            st.html("""
            <div class="dash-empty">
                <div style="font-size:2rem;">📭</div>
                <div class="de-title">No active jobs</div>
                <div class="de-sub">Upload a document to get started</div>
            </div>
            """)
        else:
            for j in active_jobs[:4]:
                status = (j.get("status") or "Pending")
                sc = _scolor(status.lower())
                si = _sicon(status.lower())
                doc = (j.get("document_name") or "Document")[:32]
                pid = j.get("print_id", "—")
                wait = j.get("estimated_wait_time", 0) or 0

                # Live progress
                prog_pct = 0
                try:
                    from smartdb.crud import get_live_progress
                    prog = get_live_progress(j["id"]) or {}
                    prog_pct = prog.get("progress_pct", 0)
                except Exception:
                    pass

                st.html(f"""
                <div class="active-job-card" style="border-left:3px solid {sc};">
                    <div class="ajc-top">
                        <div>
                            <div class="ajc-id">{pid}</div>
                            <div class="ajc-doc">{doc}</div>
                        </div>
                        <div class="ajc-status" style="color:{sc};">{si} {status}</div>
                    </div>
                    <div style="margin-top:6px;">
                        <div style="display:flex;justify-content:space-between;font-size:.68rem;
                                    color:rgba(255,255,255,.4);margin-bottom:2px;">
                            <span>Progress</span><span>{prog_pct}% · ⏱ {wait} min est.</span>
                        </div>
                        <div class="prog-bar-bg">
                            <div class="prog-bar-fill" style="width:{prog_pct}%;background:{sc};"></div>
                        </div>
                    </div>
                </div>
                """)

                if status.lower() in ("queued", "printing"):
                    if st.button("🔍 Track Live", key=f"track_{j['id']}", use_container_width=False):
                        st.session_state["track_job_id"] = j["id"]
                        st.session_state["current_page"] = "Track Order"
                        st.rerun()

    with col_right:
        st.html('<div class="section-title">🖨️ Printer Status</div>')
        if not printers:
            st.html('<div class="de-sub" style="padding:10px;">No printers configured.</div>')
        else:
            for p in printers[:5]:
                s = (p.get("status") or "Unknown")
                sc = "#10b981" if s.lower() in ("online", "idle") else \
                     "#f59e0b" if s.lower() in ("busy", "preparing") else "#ef4444"
                toner = p.get("toner_level") or 100
                st.html(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:rgba(255,255,255,.02);
                            border-radius:8px;margin-bottom:4px;
                            border:1px solid rgba(255,255,255,.05);">
                    <div>
                        <div style="font-size:.85rem;color:#fff;font-weight:500;">{p.get('name','')}</div>
                        <div style="font-size:.7rem;color:rgba(255,255,255,.4);">🖤 Toner: {toner:.0f}%</div>
                    </div>
                    <span style="color:{sc};font-weight:700;font-size:.78rem;">● {s}</span>
                </div>
                """)

    # ── Activity Chart ────────────────────────────────────────────────────────
    st.html('<div class="section-title">📊 Monthly Activity</div>')
    monthly = analytics.get("monthly_pages", {})
    if monthly and _PLOTLY:
        sorted_months = sorted(monthly.keys(), key=lambda m: datetime.strptime(m, "%b %Y"))
        vals = [monthly[k] for k in sorted_months]
        fig = go.Figure(go.Bar(
            x=sorted_months, y=vals,
            marker=dict(
                color=vals,
                colorscale=[[0, "#3B82F6"], [1, "#8B5CF6"]],
                line=dict(width=0),
            ),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
            font=dict(color="rgba(255,255,255,0.6)", size=11),
            xaxis=dict(showgrid=False, tickfont=dict(color="rgba(255,255,255,.5)")),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.05)",
                       tickfont=dict(color="rgba(255,255,255,.4)")),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.html("""
        <div class="dash-empty">
            <div class="de-sub">Upload and print documents to see your activity chart.</div>
        </div>
        """)

    # ── Recent Jobs Timeline ──────────────────────────────────────────────────
    st.html('<div class="section-title">📋 Recent Jobs</div>')
    recent = sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:6]
    if not recent:
        st.html("""
        <div class="dash-empty">
            <div style="font-size:2rem;">📭</div>
            <div class="de-title">No print history yet</div>
        </div>
        """)
    else:
        for j in recent:
            status = (j.get("status") or "Pending")
            sc = _scolor(status.lower())
            si = _sicon(status.lower())
            doc = (j.get("document_name") or "Document")[:40]
            pid = j.get("print_id", "—")
            ts  = str(j.get("created_at", ""))[:16].replace("T", " ")
            pages = j.get("total_pages", 0)
            cost  = j.get("cost", 0)

            st.html(f"""
            <div class="recent-job-row">
                <div class="rjr-status" style="color:{sc};">{si}</div>
                <div class="rjr-info">
                    <div class="rjr-doc">{doc}</div>
                    <div class="rjr-meta">{pid} · {ts} · {pages}p · ₹{cost:.0f}</div>
                </div>
                <div class="rjr-badge" style="background:{sc}22;color:{sc};
                            border:1px solid {sc}44;">{status}</div>
            </div>
            """)

    # ── QR Pickup Codes ───────────────────────────────────────────────────────
    import os
    pickup_jobs = [j for j in all_jobs if j.get("qr_code_path")
                   and os.path.exists(str(j.get("qr_code_path") or ""))
                   and (j.get("status") or "").lower() in ("ready", "completed", "queued", "printing")]
    if pickup_jobs:
        st.html('<div class="section-title">📱 QR Pickup Codes</div>')
        qc = st.columns(min(4, len(pickup_jobs)))
        for idx, job in enumerate(pickup_jobs[:4]):
            with qc[idx % len(qc)]:
                s = (job.get("status") or "").lower()
                sc = "#10b981" if s in ("ready", "completed") else "#f59e0b"
                st.html(f"""
                <div style="background:rgba(59,130,246,.05);border:1px solid rgba(59,130,246,.15);
                            border-radius:12px;padding:10px;text-align:center;margin-bottom:6px;">
                    <div style="font-family:monospace;font-weight:700;color:#60A5FA;
                                font-size:.85rem;">{job.get('print_id','')}</div>
                    <div style="font-size:.72rem;color:rgba(255,255,255,.45);margin:2px 0;">
                        {(job.get('document_name') or '')[:20]}</div>
                    <div style="font-size:.7rem;font-weight:700;color:{sc};">{job.get('status','')}</div>
                </div>
                """)
                try:
                    st.image(job.get("qr_code_path"), use_container_width=True)
                except Exception:
                    pass

    # ── Footer refresh ────────────────────────────────────────────────────────
    st.html(f"""
    <div style="text-align:center;color:rgba(255,255,255,.25);font-size:.72rem;margin-top:16px;">
        Last refreshed: {datetime.now().strftime('%H:%M:%S')} ·
        <span style="color:rgba(255,255,255,.35);">Click Refresh to update live data</span>
    </div>
    """)
    if st.button("🔄 Refresh Dashboard", key="dash_refresh", use_container_width=False):
        st.rerun()


def _dashboard_css() -> str:
    return """<style>
/* ── Welcome card ── */
.dash-welcome {
    display:flex; justify-content:space-between; align-items:flex-start;
    background:linear-gradient(145deg,rgba(59,130,246,.06),rgba(139,92,246,.03));
    border:1px solid rgba(59,130,246,.18);
    border-radius:16px; padding:24px 28px; margin-bottom:1.2rem;
}
.dash-greeting { font-size:1.65rem; font-weight:800; color:#F8FAFC; letter-spacing:-0.02em; }
.dash-name {
    background:linear-gradient(135deg,#60A5FA,#A78BFA);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.dash-meta { color:rgba(255,255,255,.4); font-size:.84rem; margin-top:5px; }
.dash-date { color:rgba(255,255,255,.28); font-size:.78rem; margin-top:3px; }
.dash-right { text-align:right; display:flex; flex-direction:column; gap:5px; align-items:flex-end; }
.dash-notif-badge {
    display:inline-flex; align-items:center; gap:5px;
    background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.28);
    border-radius:20px; padding:4px 12px; font-size:.76rem; color:#FCA5A5;
}
.dash-fav { font-size:.78rem; color:rgba(255,255,255,.45); }
.dash-active-badge {
    display:inline-flex; align-items:center;
    background:rgba(59,130,246,.10); border:1px solid rgba(59,130,246,.25);
    border-radius:20px; padding:4px 12px; font-size:.76rem; color:#60A5FA;
}

/* ── Section title ── */
.section-title {
    font-size:.75rem; font-weight:700; color:rgba(255,255,255,.55);
    margin:1.6rem 0 10px; text-transform:uppercase; letter-spacing:.08em;
}

/* ── Metric cards ── */
.dash-metric {
    background:rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.06);
    border-radius:14px; padding:16px 12px; text-align:center;
    transition:transform .2s cubic-bezier(0.4,0,0.2,1),
               box-shadow .2s cubic-bezier(0.4,0,0.2,1);
    margin-bottom:8px;
}
.dash-metric:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,.4); }
.dm-icon { font-size:1.4rem; margin-bottom:6px; }
.dm-value { font-size:1.35rem; font-weight:800; letter-spacing:-0.02em; }
.dm-label { font-size:.65rem; color:rgba(255,255,255,.35);
            text-transform:uppercase; letter-spacing:.07em; margin-top:4px; }

/* ── Active job cards ── */
.active-job-card {
    background:rgba(255,255,255,.02);
    border:1px solid rgba(255,255,255,.06);
    border-radius:12px; padding:14px 16px; margin-bottom:8px;
    transition:border-color .2s;
}
.active-job-card:hover { border-color:rgba(59,130,246,.25); }
.ajc-top { display:flex; justify-content:space-between; align-items:flex-start; }
.ajc-id { font-family:monospace; font-size:.78rem; color:#60A5FA; font-weight:700; }
.ajc-doc { font-size:.86rem; color:rgba(255,255,255,.8); margin-top:3px; }
.ajc-status { font-size:.76rem; font-weight:700; }

/* ── Progress bar ── */
.prog-bar-bg { height:4px; background:rgba(255,255,255,.07); border-radius:4px; margin-top:8px; }
.prog-bar-fill { height:4px; border-radius:4px; transition:width .4s cubic-bezier(0.4,0,0.2,1); }

/* ── Empty state ── */
.dash-empty {
    text-align:center; padding:28px 20px; background:rgba(255,255,255,.015);
    border:1px dashed rgba(255,255,255,.07); border-radius:14px; margin:4px 0;
}
.de-title { font-size:.95rem; font-weight:600; color:rgba(255,255,255,.55); margin-top:8px; }
.de-sub   { font-size:.8rem; color:rgba(255,255,255,.3); margin-top:4px; }

/* ── Recent jobs ── */
.recent-job-row {
    display:flex; align-items:center; gap:12px;
    padding:11px 14px; background:rgba(255,255,255,.018);
    border:1px solid rgba(255,255,255,.05); border-radius:11px; margin-bottom:6px;
    transition:background .15s, border-color .15s;
}
.recent-job-row:hover { background:rgba(59,130,246,.05); border-color:rgba(59,130,246,.15); }
.rjr-status { font-size:1.15rem; flex-shrink:0; }
.rjr-info { flex:1; min-width:0; }
.rjr-doc { font-size:.86rem; color:rgba(255,255,255,.84); font-weight:500;
           white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.rjr-meta { font-size:.7rem; color:rgba(255,255,255,.32); margin-top:2px; }
.rjr-badge {
    padding:3px 10px; border-radius:14px;
    font-size:.7rem; font-weight:700; white-space:nowrap; flex-shrink:0;
}
</style>"""
