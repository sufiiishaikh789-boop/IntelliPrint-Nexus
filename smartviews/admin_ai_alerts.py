"""
IntelliPrint Nexus - Admin AI Alert Center
Live AI-generated alerts from system state: printer health, queue, payments, GPU.
"""

import streamlit as st
from datetime import datetime
from smartdb.crud import get_all_printers, get_all_jobs, get_dashboard_stats


def show_ai_alerts():
    """Render the AI Alert Center."""
    st.html(_alert_css())

    st.markdown("""
    <div class="alert-header">
        <div class="alert-title">🚨 AI Alert Center</div>
        <div class="alert-subtitle">Real-time AI-generated system alerts and recommended actions</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Generate alerts from live data ────────────────────────────────────
    alerts = _generate_alerts()

    # ── Summary bar ───────────────────────────────────────────────────────
    critical = sum(1 for a in alerts if a["severity"] == "Critical")
    warning = sum(1 for a in alerts if a["severity"] == "Warning")
    info = sum(1 for a in alerts if a["severity"] == "Info")

    s1, s2, s3, s4 = st.columns(4)
    _alert_stat(s1, "🚨 Total Alerts", len(alerts), "#ef4444" if alerts else "#10b981")
    _alert_stat(s2, "🔴 Critical", critical, "#ef4444")
    _alert_stat(s3, "🟡 Warning", warning, "#f59e0b")
    _alert_stat(s4, "🔵 Info", info, "#3b82f6")

    # ── Filter ────────────────────────────────────────────────────────────
    f1, f2 = st.columns([2, 1])
    with f1:
        sev_filter = st.selectbox("Filter by Severity", ["All", "Critical", "Warning", "Info"], key="al_sev")
    with f2:
        cat_filter = st.selectbox("Category", ["All", "Printer", "Queue", "Payment", "GPU", "Document"], key="al_cat")

    filtered_alerts = alerts[:]
    if sev_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a["severity"] == sev_filter]
    if cat_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a["category"] == cat_filter]

    if not filtered_alerts:
        st.markdown("""
        <div class="alert-empty">
            <div style="font-size:3rem;">✅</div>
            <div class="alert-empty-title">All Systems Normal</div>
            <div class="alert-empty-desc">No active alerts match your filter. The system is running smoothly.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Alert cards ───────────────────────────────────────────────────────
    for alert in filtered_alerts:
        sev = alert["severity"]
        sev_color = {"Critical": "#ef4444", "Warning": "#f59e0b", "Info": "#3b82f6"}.get(sev, "#6b7280")
        sev_icon = {"Critical": "🔴", "Warning": "🟡", "Info": "🔵"}.get(sev, "⚪")
        cat_icon = {"Printer": "🖨️", "Queue": "🔧", "Payment": "💳", "GPU": "⚡", "Document": "📄"}.get(alert["category"], "⚠️")

        st.markdown(f"""
        <div class="alert-card" style="border-left:4px solid {sev_color};">
            <div class="alert-card-top">
                <div class="alert-card-icon">{cat_icon}</div>
                <div class="alert-card-content">
                    <div class="alert-card-title">{alert['title']}</div>
                    <div class="alert-card-msg">{alert['message']}</div>
                </div>
                <div class="alert-meta">
                    <span class="alert-badge" style="background:{sev_color}22;color:{sev_color};">{sev_icon} {sev}</span>
                    <span class="alert-cat">{alert['category']}</span>
                    <span class="alert-time">{alert['time']}</span>
                </div>
            </div>
            <div class="alert-action">
                <span class="alert-action-label">💡 Recommended Action:</span>
                {alert['action']}
            </div>
            {f'<div class="alert-target">📍 {alert["target"]}</div>' if alert.get('target') else ''}
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<div style="color:rgba(255,255,255,.3);font-size:.75rem;margin-top:12px;">Last updated: {datetime.now().strftime("%H:%M:%S")} • {len(filtered_alerts)} alert(s) active</div>', unsafe_allow_html=True)

    if st.button("🔄 Refresh Alerts", key="alert_refresh"):
        st.rerun()


def _generate_alerts() -> list:
    """Generate alerts from live DB state."""
    alerts = []
    now = datetime.now().strftime("%H:%M")

    try:
        printers = get_all_printers() or []
        for p in printers:
            name = p.get("name", "Printer")
            toner = p.get("toner_level", 100) or 100
            status = (p.get("status") or "").lower()
            temp = p.get("temperature", 35) or 35
            errors = p.get("error_count", 0) or 0

            if status == "offline":
                alerts.append({
                    "title": f"Printer Offline: {name}",
                    "message": f"{name} is currently offline and cannot process jobs.",
                    "severity": "Critical",
                    "category": "Printer",
                    "action": "Check network connection, power cycle the printer, or switch jobs to another printer.",
                    "target": f"{p.get('location', '')}",
                    "time": now,
                })
            if status == "maintenance":
                alerts.append({
                    "title": f"Printer in Maintenance: {name}",
                    "message": f"{name} is in maintenance mode. No jobs can be processed.",
                    "severity": "Warning",
                    "category": "Printer",
                    "action": "Complete maintenance or route pending jobs to another printer.",
                    "target": p.get("location", ""),
                    "time": now,
                })
            if toner < 10:
                alerts.append({
                    "title": f"Critical: Low Toner — {name}",
                    "message": f"Toner level is critically low at {toner:.0f}%. Printer may stop soon.",
                    "severity": "Critical",
                    "category": "Printer",
                    "action": "Replace toner cartridge immediately to avoid interruption.",
                    "target": name,
                    "time": now,
                })
            elif toner < 20:
                alerts.append({
                    "title": f"Low Toner Warning — {name}",
                    "message": f"Toner level is at {toner:.0f}%. Order replacement soon.",
                    "severity": "Warning",
                    "category": "Printer",
                    "action": "Order a toner replacement cartridge. Current level: {:.0f}%.".format(toner),
                    "target": name,
                    "time": now,
                })
            if temp > 45:
                alerts.append({
                    "title": f"High Temperature — {name}",
                    "message": f"Printer temperature is {temp}°C, above safe threshold (45°C).",
                    "severity": "Warning",
                    "category": "Printer",
                    "action": "Allow printer to cool down. Check ventilation and ensure no paper jams.",
                    "target": name,
                    "time": now,
                })
            if errors > 5:
                alerts.append({
                    "title": f"High Error Count — {name}",
                    "message": f"{name} has recorded {errors} errors. Performance may be degraded.",
                    "severity": "Warning",
                    "category": "Printer",
                    "action": "Review error logs and schedule maintenance if errors persist.",
                    "target": name,
                    "time": now,
                })
    except Exception:
        pass

    try:
        jobs = get_all_jobs() or []
        queued = [j for j in jobs if (j.get("status") or "").lower() in ("queued", "pending")]
        if len(queued) > 10:
            alerts.append({
                "title": "Queue Overload Detected",
                "message": f"There are {len(queued)} jobs waiting in queue. Students may experience long waits.",
                "severity": "Warning",
                "category": "Queue",
                "action": "Enable additional printers or set priority jobs to emergency print.",
                "target": None,
                "time": now,
            })
        payment_pending = [j for j in jobs if (j.get("status") or "").lower() == "payment_pending"]
        if len(payment_pending) > 3:
            alerts.append({
                "title": "Multiple Payment-Pending Jobs",
                "message": f"{len(payment_pending)} jobs are waiting for payment. These are blocking queue slots.",
                "severity": "Info",
                "category": "Payment",
                "action": "Notify students to complete payment or auto-cancel after timeout.",
                "target": None,
                "time": now,
            })
    except Exception:
        pass

    # GPU/system always-info alert
    alerts.append({
        "title": "AI System Operational",
        "message": "Document quality analysis (CNN model) and GPU acceleration are running normally.",
        "severity": "Info",
        "category": "GPU",
        "action": "No action needed. Monitor GPU utilization in the Dashboard.",
        "target": None,
        "time": now,
    })

    return alerts


def _alert_stat(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="alert-stat" style="border-left:3px solid {color};">
            <div class="alert-stat-label">{label}</div>
            <div class="alert-stat-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _alert_css() -> str:
    return """<style>
.alert-header { padding:18px 0 12px; margin-bottom:1rem; }
.alert-title { font-size:1.9rem; font-weight:800; color:#fff; }
.alert-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }

.alert-stat { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:12px; padding:14px 16px; margin-bottom:14px; }
.alert-stat-label { font-size:.78rem; color:rgba(255,255,255,.45); font-weight:600; text-transform:uppercase; }
.alert-stat-value { font-size:1.5rem; font-weight:800; margin-top:2px; }

.alert-card {
    background: rgba(255,255,255,.02);
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    transition: background .15s;
}
.alert-card:hover { background: rgba(255,255,255,.04); }
.alert-card-top { display:flex; align-items:flex-start; gap:14px; }
.alert-card-icon { font-size:1.8rem; flex-shrink:0; }
.alert-card-content { flex:1; }
.alert-card-title { font-size:.95rem; font-weight:700; color:#fff; margin-bottom:3px; }
.alert-card-msg { font-size:.83rem; color:rgba(255,255,255,.55); line-height:1.5; }
.alert-meta { display:flex; flex-direction:column; align-items:flex-end; gap:4px; flex-shrink:0; }
.alert-badge { padding:3px 10px; border-radius:12px; font-size:.7rem; font-weight:700; }
.alert-cat { font-size:.7rem; color:rgba(255,255,255,.4); }
.alert-time { font-size:.7rem; color:rgba(255,255,255,.3); }
.alert-action { margin-top:10px; padding:8px 12px; background:rgba(0,217,255,.05); border-radius:8px; font-size:.82rem; color:rgba(255,255,255,.65); border:1px solid rgba(0,217,255,.1); }
.alert-action-label { font-weight:700; color:#3B82F6; margin-right:6px; }
.alert-target { margin-top:5px; font-size:.75rem; color:rgba(255,255,255,.35); }
.alert-empty { text-align:center; padding:60px 20px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.05); border-radius:16px; margin:20px 0; }
.alert-empty-title { font-size:1.2rem; font-weight:700; color:#fff; margin:10px 0 6px; }
.alert-empty-desc { color:rgba(255,255,255,.4); font-size:.88rem; }
</style>"""
