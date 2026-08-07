"""
IntelliPrint Nexus - Admin Digital Twin Dashboard
Live representation of every printer as a virtual machine card showing:
  health %, temperature, toner, paper level, current job, progress, ETA, queue.
Auto-refreshes every 5 seconds while jobs are actively printing.
"""

import streamlit as st
import re
import time
import random
from datetime import datetime

from smartdb.crud import (
    get_all_printers, get_all_jobs, get_live_progress,
)


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


# ── Status config ─────────────────────────────────────────────────────────────
_STATUS_ICONS = {
    "online":      "🟢",
    "idle":        "🔵",
    "busy":        "🟡",
    "warming up":  "🟠",
    "preparing":   "🟣",
    "offline":     "🔴",
    "maintenance": "⚫",
    "paper jam":   "⚠️",
    "low paper":   "⚠️",
    "low toner":   "⚠️",
    "door open":   "⚠️",
    "error":       "⚠️",
}
_STATUS_COLORS = {
    "online":      "#10b981",
    "idle":        "#3b82f6",
    "busy":        "#eab308",
    "warming up":  "#f97316",
    "preparing":   "#a855f7",
    "offline":     "#ef4444",
    "maintenance": "#6b7280",
    "paper jam":   "#ef4444",
    "low paper":   "#f97316",
    "low toner":   "#f59e0b",
    "door open":   "#ef4444",
    "error":       "#ef4444",
}


def _health_score(p: dict) -> int:
    """Calculate printer health 0-100."""
    score = 100
    toner = p.get("toner_level", 100) or 100
    errors = p.get("error_count", 0) or 0
    temp = p.get("temperature", 35) or 35
    score -= max(0, (50 - toner) * 0.5)
    score -= errors * 4
    score -= max(0, (temp - 40) * 2)
    last_maint = p.get("last_maintenance")
    if last_maint:
        try:
            days_since = (datetime.utcnow() - last_maint).days
            score -= max(0, (days_since - 90) * 0.3)
        except Exception:
            pass
    return max(0, min(100, int(score)))


def _paper_level(printer_id: int) -> int:
    """Simulate stable paper level based on printer_id."""
    random.seed(printer_id * 7 + 42)
    return random.randint(30, 98)


def show_admin_digital_twin():
    """Render the full Digital Twin printer monitoring page."""
    st.html(_twin_css())

    st.html("""
    <div class="twin-header">
        <div class="twin-title">🖥️ Digital Twin Dashboard</div>
        <div class="twin-subtitle">Live virtual representation of all printer hardware nodes</div>
    </div>
    """)

    printers = get_all_printers() or []
    all_jobs = get_all_jobs() or []

    if not printers:
        st.html("""
        <div style="text-align:center;padding:60px 20px;background:rgba(255,255,255,.02);
                    border:1px dashed rgba(255,255,255,.1);border-radius:16px;margin:20px 0;">
            <div style="font-size:3rem;">🖨️</div>
            <div style="font-size:1.2rem;font-weight:700;color:#fff;margin:10px 0 6px;">No Printers Found</div>
            <div style="color:rgba(255,255,255,.4);font-size:.88rem;">Add printers in Printer Management.</div>
        </div>
        """)
        return

    # ── Summary strip ─────────────────────────────────────────────────────────
    online_c  = sum(1 for p in printers if (p.get("status") or "").lower() in ("online", "idle", "busy"))
    printing_c = sum(1 for p in printers if (p.get("status") or "").lower() in ("busy", "preparing"))
    offline_c = sum(1 for p in printers if (p.get("status") or "").lower() == "offline")
    active_jobs_c = sum(1 for j in all_jobs if (j.get("status") or "").lower() in ("printing","queued","preparing"))

    cols = st.columns(5)
    for col, (label, val, color) in zip(cols, [
        ("🖨️ Total",      len(printers), "#3B82F6"),
        ("🟢 Online",     online_c,      "#10b981"),
        ("🖨️ Printing",  printing_c,    "#eab308"),
        ("🔴 Offline",    offline_c,     "#ef4444"),
        ("📋 Active Jobs",active_jobs_c, "#3b82f6"),
    ]):
        with col:
            st.html(f"""
            <div class="twin-stat" style="border-left:3px solid {color};">
                <div class="ts-label">{label}</div>
                <div class="ts-value" style="color:{color};">{val}</div>
            </div>
            """)

    # ── Printer cards (2-column grid) ─────────────────────────────────────────
    cols2 = st.columns(2)
    for i, p in enumerate(printers):
        with cols2[i % 2]:
            _render_twin_card(p, all_jobs)

    # ── Last-updated & auto-refresh ───────────────────────────────────────────
    actively_printing = any(
        (j.get("status") or "").lower() in ("printing", "preparing")
        for j in all_jobs
    )
    st.html(f"""
    <div style="text-align:center;color:rgba(255,255,255,.3);font-size:.75rem;margin-top:14px;">
        💡 Auto-refreshes every 5s while jobs are active &nbsp;•&nbsp;
        Last updated: {datetime.now().strftime('%H:%M:%S')}
    </div>
    """)
    if actively_printing:
        time.sleep(5)
        st.rerun()
    else:
        if st.button("🔄 Refresh Dashboard", key="twin_refresh"):
            st.rerun()


def _render_twin_card(p: dict, all_jobs: list):
    """Render one Digital Twin printer card using st.html() for all panels."""
    pid          = p.get("id")
    name         = p.get("name", "Printer")
    location     = p.get("location", "—")
    status       = (p.get("status") or "Online")
    status_lower = status.lower()
    toner        = p.get("toner_level", 100) or 100
    temp         = p.get("temperature", 35) or 35
    errors       = p.get("error_count", 0) or 0
    total_prints = p.get("total_prints", 0) or 0
    ppm          = p.get("pages_per_minute", 20) or 20
    last_maint   = p.get("last_maintenance")
    printer_type = p.get("printer_type", "LaserJet")

    health = _health_score(p)
    paper  = _paper_level(pid or 0)

    status_icon  = _STATUS_ICONS.get(status_lower, "⚪")
    status_color = _STATUS_COLORS.get(status_lower, "#6b7280")
    health_color = "#10b981" if health >= 80 else "#f59e0b" if health >= 50 else "#ef4444"
    toner_color  = "#10b981" if toner >= 40 else "#f59e0b" if toner >= 15 else "#ef4444"
    temp_color   = "#ef4444" if temp > 50 else "#f59e0b" if temp > 42 else "#10b981"
    paper_color  = "#10b981" if paper >= 40 else "#f59e0b" if paper >= 20 else "#ef4444"
    health_label = ("Excellent" if health >= 90 else "Good" if health >= 70
                    else "Average" if health >= 50 else "Needs Service")
    last_maint_str = str(last_maint)[:10] if last_maint else "—"

    # Active / queued jobs
    current_job = next(
        (j for j in all_jobs if j.get("printer_id") == pid
         and (j.get("status") or "").lower() in ("printing", "preparing")), None
    )
    queued_jobs = [j for j in all_jobs if j.get("printer_id") == pid
                   and (j.get("status") or "").lower() == "queued"]

    progress_pct = current_page = total_p = 0
    remaining = "—"
    if current_job:
        try:
            prog = get_live_progress(current_job["id"]) or {}
            progress_pct = prog.get("progress_pct", 0)
            current_page = prog.get("current_page", 0)
            total_p      = prog.get("total_pages", 0)
            remaining    = prog.get("remaining", "—")
        except Exception:
            pass

    with st.container():
        # ── Card header ────────────────────────────────────────────────────
        st.html(f"""
        <div class="twin-card" style="border-top:3px solid {status_color};">
            <div class="tc-header">
                <div>
                    <div class="tc-name">🖨️ {name}</div>
                    <div class="tc-type">{printer_type}</div>
                    <div class="tc-loc">📍 {location}</div>
                </div>
                <div style="text-align:right;">
                    <div class="tc-status"
                         style="background:{status_color}22;color:{status_color};
                                border:1px solid {status_color}44;">
                        {status_icon} {status}
                    </div>
                    <div style="margin-top:6px;font-size:.72rem;color:rgba(255,255,255,.4);">
                        Health: <b style="color:{health_color};">{health}%</b> — {health_label}
                    </div>
                    <div style="font-size:.68rem;color:rgba(255,255,255,.3);margin-top:2px;">
                        {ppm} PPM • {total_prints:,} pages
                    </div>
                </div>
            </div>
        </div>
        """)

        # ── Metric strip ──────────────────────────────────────────────────
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        for col, (val, lbl, color) in zip(
            [m1, m2, m3, m4, m5, m6],
            [
                (f"{toner:.0f}%",       "Toner",       toner_color),
                (f"{paper}%",           "Paper",       paper_color),
                (f"{temp:.0f}°C",       "Temp",        temp_color),
                (f"{health}%",          "Health",      health_color),
                (str(len(queued_jobs)), "Queued",      "#3b82f6"),
                (last_maint_str,        "Last Maint.", "#6b7280"),
            ],
        ):
            with col:
                st.html(f"""
                <div class="tc-m">
                    <div class="tc-mv" style="color:{color};">{val}</div>
                    <div class="tc-ml">{lbl}</div>
                </div>
                """)

        # ── Toner / Paper bars ────────────────────────────────────────────
        _twin_bar(toner, "🖤 Toner", toner_color)
        _twin_bar(paper, "📄 Paper", paper_color)

        # ── Current job or idle status ────────────────────────────────────
        if current_job:
            doc        = (current_job.get("document_name") or "—")[:35]
            student_id = current_job.get("user_id", "—")
            st.html(f"""
            <div class="tc-active-job">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:.72rem;color:#3B82F6;font-weight:700;
                                    text-transform:uppercase;letter-spacing:.4px;">🖨️ Currently Printing</div>
                        <div style="font-size:.88rem;color:#fff;font-weight:600;margin-top:2px;">{doc}</div>
                        <div style="font-size:.72rem;color:rgba(255,255,255,.4);">
                            Student #{student_id} • Page {current_page}/{total_p} • ETA: {remaining}
                        </div>
                    </div>
                    <div style="font-size:1.2rem;font-weight:800;color:#3B82F6;">{progress_pct}%</div>
                </div>
            </div>
            <div style="margin:4px 0 8px;">
                <div class="pr-bar-bg">
                    <div class="pr-bar-fill printing-bar" style="width:{progress_pct}%;"></div>
                </div>
            </div>
            """)
        elif queued_jobs:
            st.html(f"""
            <div style="padding:8px 12px;background:rgba(59,130,246,.06);
                        border:1px solid rgba(59,130,246,.15);
                        border-radius:8px;margin:4px 0;font-size:.78rem;color:rgba(255,255,255,.6);">
                📋 {len(queued_jobs)} job(s) in queue — Idle
            </div>
            """)
        else:
            st.html("""
            <div style="padding:8px 12px;background:rgba(16,185,129,.04);
                        border:1px solid rgba(16,185,129,.12);
                        border-radius:8px;margin:4px 0;font-size:.78rem;color:rgba(255,255,255,.4);">
                ✅ Idle — No active print jobs
            </div>
            """)

        # ── Alerts ────────────────────────────────────────────────────────
        alerts = []
        if toner  <  15: alerts.append("⚠️ Critical: Toner level very low")
        elif toner < 25: alerts.append("⚠️ Warning: Toner running low")
        if paper  <  20: alerts.append("⚠️ Critical: Paper almost empty")
        elif paper < 30: alerts.append("⚠️ Warning: Paper running low")
        if temp   >  50: alerts.append("🔥 Alert: High temperature detected")
        if errors >   8: alerts.append(f"❌ Alert: {errors} errors recorded")

        for alert in alerts:
            st.html(f"""
            <div style="padding:6px 12px;background:rgba(239,68,68,.08);
                        border:1px solid rgba(239,68,68,.25);
                        border-radius:6px;margin:2px 0;font-size:.75rem;color:#fca5a5;">{alert}</div>
            """)

        st.html('<div style="height:8px;"></div>')


def _twin_bar(value: float, label: str, color: str):
    """Render a labelled progress bar using st.html()."""
    alert = " ⚠️ LOW" if value < 20 else ""
    st.html(f"""
    <div style="padding:0 0 6px;">
        <div style="display:flex;justify-content:space-between;font-size:.68rem;
                    color:rgba(255,255,255,.4);margin-bottom:2px;">
            <span>{label}{alert}</span><span>{value:.0f}%</span>
        </div>
        <div class="pr-bar-bg">
            <div class="pr-bar-fill" style="width:{value:.0f}%;background:{color};"></div>
        </div>
    </div>
    """)


def _twin_css() -> str:
    return """<style>
@keyframes bar-animate { 0%{opacity:.7;}50%{opacity:1;}100%{opacity:.7;} }
.printing-bar {
    animation: bar-animate 1.5s ease-in-out infinite;
    background: linear-gradient(90deg,#3B82F6,#8B5CF6) !important;
}

.twin-header { padding:18px 0 12px; margin-bottom:1rem; }
.twin-title {
    font-size:1.9rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.twin-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }

.twin-stat {
    background:rgba(255,255,255,.03);
    border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:12px 16px; margin-bottom:12px;
}
.ts-label { font-size:.72rem; color:rgba(255,255,255,.45); font-weight:600; text-transform:uppercase; }
.ts-value { font-size:1.5rem; font-weight:800; margin-top:2px; }

.twin-card {
    background:rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.07);
    border-radius:14px; padding:16px 18px; margin-bottom:4px;
}
.tc-header {
    display:flex; justify-content:space-between;
    align-items:flex-start; margin-bottom:8px;
}
.tc-name  { font-size:1.05rem; font-weight:700; color:#fff; }
.tc-type  { font-size:.72rem;  color:#3B82F6; margin-top:2px; font-weight:600; }
.tc-loc   { font-size:.75rem;  color:rgba(255,255,255,.4); margin-top:3px; }
.tc-status {
    padding:4px 12px; border-radius:12px;
    font-size:.75rem; font-weight:700; display:inline-block;
}

.tc-m {
    text-align:center;
    background:rgba(255,255,255,.03);
    border-radius:8px; padding:7px 4px;
}
.tc-mv { font-size:.95rem; font-weight:800; color:#fff; }
.tc-ml {
    font-size:.58rem; color:rgba(255,255,255,.4);
    margin-top:2px; text-transform:uppercase; letter-spacing:.3px;
}

.tc-active-job {
    background:rgba(0,217,255,.05);
    border:1px solid rgba(0,217,255,.15);
    border-radius:10px; padding:10px 14px; margin:8px 0;
}

.pr-bar-bg {
    height:6px; background:rgba(255,255,255,.08);
    border-radius:4px; overflow:hidden;
}
.pr-bar-fill { height:6px; border-radius:4px; transition:width .4s; }
</style>"""
