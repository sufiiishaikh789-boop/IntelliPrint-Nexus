"""
IntelliPrint Nexus - Admin Reports & Analytics
Daily/monthly reports, per-printer analytics, and export functionality.
"""

import streamlit as st
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from smartdb.crud import get_all_jobs, get_all_printers, get_today_stats, get_all_payments_with_jobs


def show_reports():
    """Render the reports and analytics page."""
    st.html(_rep_css())

    st.markdown("""
    <div class="rep-header">
        <div class="rep-title">📊 Reports & Analytics</div>
        <div class="rep-subtitle">Business intelligence, printer analytics, and export tools</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch all data ────────────────────────────────────────────────────
    all_jobs = []
    printers = []
    today_stats = {}
    payments = []
    try:
        all_jobs = get_all_jobs() or []
        printers = get_all_printers() or []
        today_stats = get_today_stats() or {}
        payments = get_all_payments_with_jobs() or []
    except Exception as e:
        st.error(f"Error loading report data: {e}")

    # ── Today's Business Dashboard ─────────────────────────────────────────
    st.markdown('<div class="rep-section-title">📅 Today\'s Business Summary</div>', unsafe_allow_html=True)

    t1, t2, t3, t4, t5, t6 = st.columns(6)
    _rep_metric(t1, "💰 Revenue", f"₹{today_stats.get('today_revenue', 0):,.2f}", "#8B5CF6")
    _rep_metric(t2, "📄 Documents", today_stats.get("today_docs", 0), "#3B82F6")
    _rep_metric(t3, "📃 Pages", today_stats.get("today_pages", 0), "#3b82f6")
    _rep_metric(t4, "⏱️ Avg Wait", f"{today_stats.get('avg_wait', 0)} min", "#f59e0b")
    _rep_metric(t5, "🌟 Priority", today_stats.get("today_priority", 0), "#a855f7")
    _rep_metric(t6, "👥 Active Students", today_stats.get("active_students", 0), "#10b981")

    st.markdown("---")

    # ── Export buttons ─────────────────────────────────────────────────────
    st.markdown('<div class="rep-section-title">📥 Export Reports</div>', unsafe_allow_html=True)
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        if st.button("📄 Export Daily Report (CSV)", key="rep_daily_csv", use_container_width=True):
            _export_csv(all_jobs, payments, "daily")
    with e2:
        if st.button("📊 Export Monthly Report (CSV)", key="rep_monthly_csv", use_container_width=True):
            _export_csv(all_jobs, payments, "monthly")
    with e3:
        if st.button("🖨️ Download Full Stats (CSV)", key="rep_full_csv", use_container_width=True):
            _export_csv(all_jobs, payments, "full")
    with e4:
        if st.button("🔄 Refresh Data", key="rep_refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # ── Jobs over time chart ───────────────────────────────────────────────
    st.markdown('<div class="rep-section-title">📈 Print Jobs — Last 30 Days</div>', unsafe_allow_html=True)
    _jobs_over_time_chart(all_jobs)

    st.markdown("---")

    # ── Revenue chart ──────────────────────────────────────────────────────
    st.markdown('<div class="rep-section-title">💰 Revenue — Last 30 Days</div>', unsafe_allow_html=True)
    _revenue_chart(all_jobs)

    st.markdown("---")

    # ── Printer analytics ─────────────────────────────────────────────────
    st.markdown('<div class="rep-section-title">🖨️ Printer Analytics</div>', unsafe_allow_html=True)
    if not printers:
        st.info("No printers found.")
    else:
        cols_per_row = 2
        printer_pairs = [printers[i:i+cols_per_row] for i in range(0, len(printers), cols_per_row)]
        for pair in printer_pairs:
            pcols = st.columns(cols_per_row)
            for idx, p in enumerate(pair):
                with pcols[idx]:
                    _printer_analytics_card(p, all_jobs)

    st.markdown("---")

    # ── Status breakdown ──────────────────────────────────────────────────
    st.markdown('<div class="rep-section-title">📊 Job Status Distribution</div>', unsafe_allow_html=True)
    _status_pie(all_jobs)

    # ── Consumables table ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="rep-section-title">🔧 Consumables & Health Monitor</div>', unsafe_allow_html=True)
    _consumables_table(printers)


def _jobs_over_time_chart(jobs):
    """Bar chart of jobs submitted per day for last 30 days."""
    from collections import defaultdict
    day_counts = defaultdict(int)
    today = date.today()
    for j in jobs:
        submitted = j.get("submitted_at")
        if submitted:
            try:
                d = str(submitted)[:10]
                dt = datetime.strptime(d, "%Y-%m-%d").date()
                if (today - dt).days <= 30:
                    day_counts[d] += 1
            except Exception:
                pass

    labels = [(today - timedelta(days=i)).strftime("%b %d") for i in range(29, -1, -1)]
    date_keys = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    values = [day_counts.get(k, 0) for k in date_keys]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color="rgba(0,217,255,0.7)",
        marker_line_color="rgba(0,217,255,1)",
        marker_line_width=1,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.03)",
        font=dict(color="#fff", size=10),
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis=dict(tickfont=dict(size=9), gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _revenue_chart(jobs):
    """Line chart of daily revenue for last 30 days."""
    from collections import defaultdict
    day_rev = defaultdict(float)
    today = date.today()
    for j in jobs:
        submitted = j.get("submitted_at")
        cost = j.get("total_cost") or j.get("cost") or 0.0
        if submitted:
            try:
                d = str(submitted)[:10]
                dt = datetime.strptime(d, "%Y-%m-%d").date()
                if (today - dt).days <= 30:
                    day_rev[d] += float(cost)
            except Exception:
                pass

    labels = [(today - timedelta(days=i)).strftime("%b %d") for i in range(29, -1, -1)]
    date_keys = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    values = [round(day_rev.get(k, 0), 2) for k in date_keys]

    fig = go.Figure(go.Scatter(
        x=labels, y=values, mode="lines+markers",
        line=dict(color="#8B5CF6", width=2),
        marker=dict(color="#8B5CF6", size=5),
        fill="tozeroy", fillcolor="rgba(124,255,0,0.07)",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.03)",
        font=dict(color="#fff", size=10),
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis=dict(tickfont=dict(size=9), gridcolor="rgba(255,255,255,.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)", tickprefix="₹"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _printer_analytics_card(p, all_jobs):
    """Render a single printer analytics card."""
    pid = p.get("id")
    name = p.get("name", "Printer")
    status = p.get("status", "Unknown")
    toner = p.get("toner_level", 0) or 0
    temp = p.get("temperature", 35) or 35
    total_prints = p.get("total_prints", 0) or 0
    errors = p.get("error_count", 0) or 0

    printer_jobs = [j for j in all_jobs if j.get("printer_id") == pid]
    today = date.today()
    today_jobs = [j for j in printer_jobs if str(j.get("submitted_at", ""))[:10] == str(today)]
    today_pages = sum(j.get("total_pages", 0) for j in today_jobs)
    today_count = len(today_jobs)
    health = max(0, min(100, 100 - errors * 5 - max(0, 45 - temp) * 0.5))
    health_color = "#10b981" if health > 70 else "#f59e0b" if health > 40 else "#ef4444"
    status_color = "#10b981" if status.lower() == "online" else "#f59e0b" if status.lower() == "maintenance" else "#ef4444"
    toner_color = "#10b981" if toner > 40 else "#f59e0b" if toner > 15 else "#ef4444"

    st.markdown(f"""
    <div class="rep-printer-card">
        <div class="rep-printer-name">🖨️ {name}</div>
        <div class="rep-printer-location">{p.get('location', '')}</div>
        <div style="display:flex;gap:8px;margin:10px 0;flex-wrap:wrap;">
            <span class="rep-tag" style="color:{status_color};">● {status}</span>
            <span class="rep-tag" style="color:{toner_color};">Toner: {toner:.0f}%</span>
            <span class="rep-tag" style="color:{health_color};">Health: {health:.0f}%</span>
            <span class="rep-tag">🌡️ {temp}°C</span>
        </div>
        <div class="rep-printer-stats">
            <div class="rep-ps-item"><div class="rep-ps-val" style="color:#3B82F6;">{today_count}</div><div class="rep-ps-lbl">Today's Jobs</div></div>
            <div class="rep-ps-item"><div class="rep-ps-val">{today_pages}</div><div class="rep-ps-lbl">Today's Pages</div></div>
            <div class="rep-ps-item"><div class="rep-ps-val" style="color:#8B5CF6;">{total_prints:,}</div><div class="rep-ps-lbl">Lifetime Prints</div></div>
            <div class="rep-ps-item"><div class="rep-ps-val" style="color:#ef4444;">{errors}</div><div class="rep-ps-lbl">Total Errors</div></div>
        </div>
        <div style="margin-top:10px;">
            <div style="display:flex;justify-content:space-between;font-size:.72rem;color:rgba(255,255,255,.4);margin-bottom:4px;">
                <span>Toner Level</span><span>{toner:.0f}%</span>
            </div>
            <div class="rep-bar-bg"><div class="rep-bar-fill" style="width:{toner:.0f}%;background:{toner_color};"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _status_pie(jobs):
    """Donut chart of job statuses."""
    from collections import Counter
    statuses = [j.get("status", "Unknown") for j in jobs]
    counts = Counter(statuses)

    if not counts:
        st.info("No job data available.")
        return

    colors = {
        "Pending": "#f59e0b", "Payment_Pending": "#f59e0b",
        "Queued": "#3b82f6", "Printing": "#A78BFA",
        "Completed": "#10b981", "Ready": "#06b6d4",
        "Collected": "#059669", "Cancelled": "#ef4444", "Failed": "#dc2626",
    }
    labels = list(counts.keys())
    values = list(counts.values())
    marker_colors = [colors.get(l, "#6b7280") for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=marker_colors, line=dict(color="rgba(0,0,0,.3)", width=2)),
        textfont=dict(size=11, color="#fff"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fff"),
        margin=dict(t=5, b=5, l=5, r=5),
        height=240,
        legend=dict(font=dict(color="rgba(255,255,255,.6)", size=10), orientation="v"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _consumables_table(printers):
    """Table showing consumables for all printers."""
    if not printers:
        st.info("No printers found.")
        return

    st.markdown("""
    <div class="cons-header">
        <span style="flex:2">Printer</span>
        <span style="flex:1">Status</span>
        <span style="flex:1">Toner %</span>
        <span style="flex:1">Temperature</span>
        <span style="flex:1">Errors</span>
        <span style="flex:1.5">Last Maintenance</span>
        <span style="flex:1">Health</span>
    </div>
    """, unsafe_allow_html=True)

    for p in printers:
        toner = p.get("toner_level", 0) or 0
        status = p.get("status", "Unknown")
        temp = p.get("temperature", 35) or 35
        errors = p.get("error_count", 0) or 0
        last_maint = str(p.get("last_maintenance", ""))[:10] or "—"
        health = max(0, min(100, 100 - errors * 5))
        health_color = "#10b981" if health > 70 else "#f59e0b" if health > 40 else "#ef4444"
        toner_color = "#10b981" if toner > 40 else "#f59e0b" if toner > 15 else "#ef4444"
        status_color = "#10b981" if status.lower() == "online" else "#f59e0b" if status.lower() == "maintenance" else "#ef4444"
        toner_warn = " ⚠️" if toner < 20 else ""

        st.markdown(f"""
        <div class="cons-row">
            <span style="flex:2;font-weight:600;color:#fff;">{p.get('name','')}</span>
            <span style="flex:1;color:{status_color};">● {status}</span>
            <span style="flex:1;color:{toner_color};">{toner:.0f}%{toner_warn}</span>
            <span style="flex:1;color:{'#f59e0b' if temp>45 else '#fff'};">{temp}°C</span>
            <span style="flex:1;color:{'#ef4444' if errors>5 else '#fff'};">{errors}</span>
            <span style="flex:1.5;color:rgba(255,255,255,.5);font-size:.78rem;">{last_maint}</span>
            <span style="flex:1;color:{health_color};font-weight:700;">{health:.0f}%</span>
        </div>
        """, unsafe_allow_html=True)


def _export_csv(jobs, payments, mode):
    """Generate and offer a CSV download."""
    import io, csv as csv_mod
    buf = io.StringIO()
    writer = csv_mod.writer(buf)
    writer.writerow(["Print ID", "User ID", "Document", "Pages", "Copies", "Color", "Priority", "Status", "Cost", "Submitted", "Completed"])
    for j in jobs:
        writer.writerow([
            j.get("print_id", ""), j.get("user_id", ""), j.get("document_name", ""),
            j.get("total_pages", 0), j.get("copies", 1), j.get("color_mode", "BW"),
            j.get("priority", "Normal"), j.get("status", ""), j.get("total_cost", 0),
            str(j.get("submitted_at", ""))[:16], str(j.get("completed_at", ""))[:16],
        ])
    csv_bytes = buf.getvalue().encode("utf-8")
    fname = f"smartprint_{mode}_{date.today()}.csv"
    st.download_button(f"⬇️ Download {fname}", data=csv_bytes, file_name=fname, mime="text/csv", key=f"dl_{mode}_{id(jobs)}")


def _rep_metric(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="rep-metric" style="border-left:3px solid {color};">
            <div class="rep-metric-label">{label}</div>
            <div class="rep-metric-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _rep_css() -> str:
    return """<style>
.rep-header { padding:18px 0 12px; margin-bottom:1rem; }
.rep-title { font-size:1.9rem; font-weight:800; color:#fff; }
.rep-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }
.rep-section-title { font-size:1rem; font-weight:700; color:rgba(255,255,255,.8); text-transform:uppercase; letter-spacing:.5px; margin:1.2rem 0 10px; }
.rep-metric { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:12px; padding:12px 14px; margin-bottom:12px; }
.rep-metric-label { font-size:.72rem; color:rgba(255,255,255,.45); font-weight:600; text-transform:uppercase; }
.rep-metric-value { font-size:1.35rem; font-weight:800; margin-top:2px; }
.rep-printer-card { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:14px; padding:16px; margin-bottom:12px; }
.rep-printer-name { font-size:1rem; font-weight:700; color:#fff; }
.rep-printer-location { font-size:.75rem; color:rgba(255,255,255,.4); margin-top:2px; }
.rep-tag { font-size:.72rem; font-weight:600; padding:3px 8px; background:rgba(255,255,255,.05); border-radius:6px; }
.rep-printer-stats { display:flex; gap:12px; margin-top:10px; }
.rep-ps-item { flex:1; text-align:center; background:rgba(255,255,255,.03); border-radius:8px; padding:8px 4px; }
.rep-ps-val { font-size:1.1rem; font-weight:800; color:#fff; }
.rep-ps-lbl { font-size:.65rem; color:rgba(255,255,255,.4); margin-top:2px; text-transform:uppercase; }
.rep-bar-bg { height:6px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
.rep-bar-fill { height:6px; border-radius:4px; transition:width .4s; }
.cons-header { display:flex; padding:8px 12px; background:rgba(0,217,255,.06); border:1px solid rgba(0,217,255,.12); border-radius:8px; margin-bottom:6px; font-size:.7rem; font-weight:700; color:rgba(0,217,255,.8); text-transform:uppercase; letter-spacing:.4px; gap:6px; }
.cons-row { display:flex; align-items:center; padding:10px 12px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.05); border-radius:8px; margin-bottom:4px; font-size:.82rem; gap:6px; }
.cons-row:hover { background:rgba(255,255,255,.04); }
</style>"""
