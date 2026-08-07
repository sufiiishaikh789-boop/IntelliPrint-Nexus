"""
IntelliPrint Nexus — Printer Availability (Student Read-Only View)
==================================================================
Allows students to check live printer status BEFORE uploading documents.
Read-only: no upload, no configuration, no queue management.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import get_all_printers, get_print_jobs_for_printer
from smartai.recommendation import recommend_printers
from smartai.wait_time import predict_wait_time


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _workload_color(pct: float) -> str:
    if pct <= 40:
        return "#10b981"
    elif pct <= 75:
        return "#f59e0b"
    return "#ef4444"


def _status_meta(status: str, queue: int):
    s = status.lower()
    if s == "online" and queue == 0:
        return "🟢", "Available", "#10b981"
    elif s == "online":
        return "🟡", "Busy", "#f59e0b"
    elif s == "maintenance":
        return "🔧", "Maintenance", "#f59e0b"
    return "🔴", "Offline", "#ef4444"


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

def show_printer_availability():
    """Render the Printer Availability read-only page."""

    st.html(_clean_html(_page_css()))

    # ── Page Header ───────────────────────────────────────────────────────────
    st.html(_clean_html("""
        <div class="pa-header">
            <div class="pa-header-icon">🖨️</div>
            <div>
                <div class="pa-header-title">Printer Availability</div>
                <div class="pa-header-sub">Check Live Printer Status Before Uploading Documents</div>
            </div>
            <div class="pa-readonly-badge">👁 Read Only</div>
        </div>
    """))

    # ── Load data ─────────────────────────────────────────────────────────────
    printers = []
    try:
        printers = get_all_printers() or []
    except Exception:
        st.error("⚠️ Could not load printer data. Please try again.")
        return

    if not printers:
        st.info("📭 No printers configured yet.")
        return

    # Enrich each printer with live queue + wait metrics
    enriched = []
    for p in printers:
        p_id = p.get("id")
        try:
            jobs = get_print_jobs_for_printer(p_id) or []
        except Exception:
            jobs = []
        queue_len = sum(1 for j in jobs if (j.get("status") or "").lower() in ("queued", "printing"))
        ppm = p.get("ppm") or 30
        try:
            wait_info = predict_wait_time(
                queue_length=queue_len,
                pages=5,
                copies=1,
                printer_speed_ppm=ppm,
                priority_flag=False,
            )
            wait_min = wait_info.get("estimated_wait_minutes", 0)
        except Exception:
            wait_min = queue_len * 2

        # Workload = queue-based heuristic (0-100%)
        workload = min(100, int((queue_len / max(1, 10)) * 100 + (100 - p.get("toner_level", 100)) * 0.1))

        dot, status_label, scolor = _status_meta(p.get("status", "Offline"), queue_len)

        supports_color = p.get("color_supported", True)
        supports_bw    = p.get("bw_supported", True)

        enriched.append({
            **p,
            "queue_len":    queue_len,
            "wait_min":     wait_min,
            "workload":     workload,
            "dot":          dot,
            "status_label": status_label,
            "scolor":       scolor,
            "ppm":          ppm,
            "supports_color": supports_color,
            "supports_bw":    supports_bw,
        })

    # ── Summary Stats ─────────────────────────────────────────────────────────
    total     = len(enriched)
    available = sum(1 for p in enriched if p["status_label"] == "Available")
    busy      = sum(1 for p in enriched if p["status_label"] == "Busy")
    offline   = sum(1 for p in enriched if p["status_label"] == "Offline")
    avg_wait  = round(
        sum(p["wait_min"] for p in enriched if p.get("status", "").lower() == "online") /
        max(1, sum(1 for p in enriched if p.get("status", "").lower() == "online")), 1
    )

    stat_cards = [
        ("🖨️", "Total Printers", str(total),        "#3B82F6"),
        ("🟢", "Available",       str(available),    "#10b981"),
        ("🟡", "Busy",            str(busy),         "#f59e0b"),
        ("🔴", "Offline",         str(offline),      "#ef4444"),
        ("⏱️", "Avg Wait",       f"{avg_wait} min",  "#06b6d4"),
    ]

    cols = st.columns(5)
    for col, (icon, label, value, color) in zip(cols, stat_cards):
        with col:
            st.html(_clean_html(f"""
                <div class="pa-stat-card" style="border-top:3px solid {color};">
                    <div class="pa-stat-icon">{icon}</div>
                    <div class="pa-stat-value" style="color:{color};">{value}</div>
                    <div class="pa-stat-label">{label}</div>
                </div>
            """))

    # ── Filter Chips ──────────────────────────────────────────────────────────
    st.html(_clean_html('<div class="pa-section-title" style="margin-top:1.5rem;">Filters</div>'))

    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    with fc1:
        f_available = st.checkbox("Available Only", key="pa_f_available")
    with fc2:
        f_color = st.checkbox("Color Printing", key="pa_f_color")
    with fc3:
        f_bw = st.checkbox("Black and White", key="pa_f_bw")
    with fc4:
        f_a4 = st.checkbox("A4", key="pa_f_a4")
    with fc5:
        f_a3 = st.checkbox("A3", key="pa_f_a3")

    # Apply filters
    filtered = enriched
    if f_available:
        filtered = [p for p in filtered if p["status_label"] == "Available"]
    if f_color:
        filtered = [p for p in filtered if p.get("supports_color", True)]
    if f_bw:
        filtered = [p for p in filtered if p.get("supports_bw", True)]

    # ── AI Recommendation ─────────────────────────────────────────────────────
    online_printers = [p for p in enriched if p.get("status", "").lower() == "online"]
    if online_printers:
        try:
            rec_result = recommend_printers(
                job_pages=5,
                job_copies=1,
                color_required=False,
                available_printers=online_printers,
            )
            best = rec_result.get("best_printer") if rec_result else None
        except Exception:
            best = None

        if best:
            best_name  = best.get("name", "Unknown")
            best_wait  = best.get("predicted_wait", 0)
            best_queue = best.get("queue", 0)
            best_ppm   = best.get("ppm", 30)
            confidence = int(best.get("score", 96))

            st.html(_clean_html(f"""
                <div class="pa-section-title" style="margin-top:1.5rem;">AI Recommendation</div>
                <div class="pa-ai-card">
                    <div class="pa-ai-left">
                        <div class="pa-ai-robot">🤖</div>
                        <div class="pa-ai-conf">{confidence}%<div class="pa-ai-conf-lbl">Confidence</div></div>
                    </div>
                    <div class="pa-ai-mid">
                        <div class="pa-ai-tag">Recommended Printer</div>
                        <div class="pa-ai-name">{best_name}</div>
                        <div class="pa-ai-reasons">
                            <div class="pa-ai-reason">Fastest completion time</div>
                            <div class="pa-ai-reason">Lowest queue ({best_queue} jobs)</div>
                            <div class="pa-ai-reason">Speed: {best_ppm} pages/min</div>
                        </div>
                    </div>
                    <div class="pa-ai-right">
                        <div class="pa-ai-wait-val">{best_wait} min</div>
                        <div class="pa-ai-wait-lbl">Est. Wait</div>
                        <div class="pa-ai-info">Informational only</div>
                    </div>
                </div>
            """))

    # ── Printer Cards ─────────────────────────────────────────────────────────
    count_label = f'{len(filtered)} printer{"s" if len(filtered)!=1 else ""} shown'
    st.html(_clean_html(
        f'<div class="pa-section-title" style="margin-top:1.5rem;">Live Printer Status '
        f'<span style="font-size:0.75rem;color:rgba(255,255,255,.35);font-weight:400;">({count_label})</span></div>'
    ))

    if not filtered:
        st.info("No printers match the selected filters.")
        return

    now_str = datetime.now().strftime("%H:%M")

    chunk_size = 3
    for i in range(0, len(filtered), chunk_size):
        chunk = filtered[i:i + chunk_size]
        cols = st.columns(len(chunk))
        for col, p in zip(cols, chunk):
            wl       = p["workload"]
            wl_color = _workload_color(wl)
            scolor   = p["scolor"]
            dot      = p["dot"]
            sl       = p["status_label"]
            toner    = p.get("toner_level", 0) or 0
            toner_c  = _workload_color(100 - toner)

            support_parts = []
            if p.get("supports_color", True):
                support_parts.append("Color")
            if p.get("supports_bw", True):
                support_parts.append("B&W")
            support_display = " + ".join(support_parts) if support_parts else "B&W"

            with col:
                st.html(_clean_html(f"""
                    <div class="pa-printer-card" style="border-top:3px solid {scolor};">
                        <div class="pa-pc-header">
                            <div class="pa-pc-name">{p.get('name', 'Printer')[:22]}</div>
                            <div class="pa-pc-status-dot" style="color:{scolor};">{dot}</div>
                        </div>
                        <div class="pa-pc-location">{p.get('location', 'Campus')[:30]}</div>
                        <div class="pa-pc-status-pill" style="background:{scolor}18;color:{scolor};border:1px solid {scolor}33;">{sl}</div>
                        <div class="pa-pc-divider"></div>
                        <div class="pa-pc-row">
                            <span class="pa-pc-lbl">Queue</span>
                            <span class="pa-pc-val">{p['queue_len']} Job{"s" if p["queue_len"]!=1 else ""}</span>
                        </div>
                        <div class="pa-pc-row">
                            <span class="pa-pc-lbl">Est. Wait</span>
                            <span class="pa-pc-val" style="color:#f59e0b;">{p['wait_min']} min</span>
                        </div>
                        <div class="pa-pc-row">
                            <span class="pa-pc-lbl">Speed</span>
                            <span class="pa-pc-val">{p['ppm']} PPM</span>
                        </div>
                        <div class="pa-pc-row">
                            <span class="pa-pc-lbl">Support</span>
                            <span class="pa-pc-val" style="font-size:0.7rem;">{support_display}</span>
                        </div>
                        <div class="pa-pc-row">
                            <span class="pa-pc-lbl">Updated</span>
                            <span class="pa-pc-val" style="color:rgba(255,255,255,.4);">{now_str}</span>
                        </div>
                        <div class="pa-pc-divider"></div>
                        <div class="pa-pc-lbl" style="margin-bottom:5px;">Workload {wl}%</div>
                        <div class="pa-wl-bar-bg">
                            <div class="pa-wl-bar-fill" style="width:{wl}%;background:{wl_color};"></div>
                        </div>
                        <div class="pa-pc-lbl" style="margin-top:8px;margin-bottom:4px;">Toner {int(toner)}%</div>
                        <div class="pa-wl-bar-bg">
                            <div class="pa-wl-bar-fill" style="width:{int(toner)}%;background:{toner_c};"></div>
                        </div>
                    </div>
                """))

    # ── Workload Legend ───────────────────────────────────────────────────────
    st.html(_clean_html("""
        <div class="pa-legend">
            <div class="pa-legend-title">Workload Guide</div>
            <div class="pa-legend-items">
                <div class="pa-legend-item">
                    <div class="pa-legend-dot" style="background:#10b981;"></div>
                    <span>0-40% Low (Best time to print)</span>
                </div>
                <div class="pa-legend-item">
                    <div class="pa-legend-dot" style="background:#f59e0b;"></div>
                    <span>41-75% Moderate (Short wait)</span>
                </div>
                <div class="pa-legend-item">
                    <div class="pa-legend-dot" style="background:#ef4444;"></div>
                    <span>76-100% High (Consider waiting)</span>
                </div>
            </div>
        </div>
    """))


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

def _page_css() -> str:
    return """
    <style>
    .pa-header {
        display:flex; align-items:center; gap:18px;
        padding:20px 0 16px;
        border-bottom:1px solid rgba(255,255,255,.06);
        margin-bottom:1.5rem;
    }
    .pa-header-icon { font-size:2.8rem; }
    .pa-header-title {
        font-size:1.8rem; font-weight:800; letter-spacing:-0.03em;
        background:linear-gradient(135deg,#3B82F6,#60A5FA,#a78bfa);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        background-clip:text;
    }
    .pa-header-sub { font-size:0.88rem; color:rgba(255,255,255,.45); margin-top:3px; }
    .pa-readonly-badge {
        margin-left:auto; background:rgba(255,255,255,.05);
        border:1px solid rgba(255,255,255,.10); border-radius:20px;
        padding:5px 14px; font-size:0.75rem; color:rgba(255,255,255,.45);
        font-weight:600; white-space:nowrap;
    }
    .pa-section-title {
        font-size:0.82rem; font-weight:700; letter-spacing:.08em;
        text-transform:uppercase; color:rgba(255,255,255,.5);
        margin-bottom:10px;
    }
    .pa-stat-card {
        background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
        border-radius:14px; padding:16px 14px; text-align:center;
        transition:transform .2s,box-shadow .2s;
    }
    .pa-stat-card:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,.3); }
    .pa-stat-icon { font-size:1.5rem; margin-bottom:6px; }
    .pa-stat-value { font-size:1.6rem; font-weight:800; letter-spacing:-0.02em; }
    .pa-stat-label { font-size:0.7rem; font-weight:600; text-transform:uppercase;
                     letter-spacing:.06em; color:rgba(255,255,255,.4); margin-top:3px; }
    .pa-ai-card {
        display:flex; align-items:stretch; gap:20px;
        background:linear-gradient(135deg,rgba(59,130,246,.08),rgba(139,92,246,.06));
        border:1px solid rgba(59,130,246,.25); border-radius:16px;
        padding:20px 24px; margin-bottom:1rem;
        transition:transform .2s,box-shadow .2s;
    }
    .pa-ai-card:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(59,130,246,.18); }
    .pa-ai-left { display:flex; flex-direction:column; align-items:center; gap:10px; min-width:70px; }
    .pa-ai-robot { font-size:2.5rem; }
    .pa-ai-conf { font-size:1.4rem; font-weight:900; color:#10b981; text-align:center; line-height:1.1; }
    .pa-ai-conf-lbl { font-size:0.6rem; font-weight:600; text-transform:uppercase;
                      letter-spacing:.05em; color:rgba(255,255,255,.4); }
    .pa-ai-mid { flex:1; }
    .pa-ai-tag { font-size:0.7rem; font-weight:700; text-transform:uppercase;
                 letter-spacing:.08em; color:rgba(59,130,246,.8); margin-bottom:5px; }
    .pa-ai-name { font-size:1.15rem; font-weight:800; color:#fff; margin-bottom:10px; }
    .pa-ai-reasons { display:flex; flex-direction:column; gap:4px; }
    .pa-ai-reason { font-size:0.8rem; color:rgba(255,255,255,.6); }
    .pa-ai-right {
        text-align:center; min-width:90px;
        border-left:1px solid rgba(255,255,255,.07); padding-left:20px;
        display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px;
    }
    .pa-ai-wait-val { font-size:1.6rem; font-weight:800; color:#f59e0b; }
    .pa-ai-wait-lbl { font-size:0.65rem; text-transform:uppercase; letter-spacing:.06em; color:rgba(255,255,255,.35); }
    .pa-ai-info { font-size:0.65rem; color:rgba(255,255,255,.25); margin-top:8px; }
    .pa-printer-card {
        background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
        border-radius:16px; padding:16px 14px; margin-bottom:10px;
        transition:transform .2s,box-shadow .2s;
    }
    .pa-printer-card:hover { transform:translateY(-3px); box-shadow:0 10px 28px rgba(0,0,0,.35); }
    .pa-pc-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:2px; }
    .pa-pc-name { font-size:0.88rem; font-weight:700; color:#fff; }
    .pa-pc-status-dot { font-size:1rem; }
    .pa-pc-location { font-size:0.7rem; color:rgba(255,255,255,.35); margin-bottom:8px; }
    .pa-pc-status-pill {
        display:inline-block; padding:3px 10px; border-radius:20px;
        font-size:0.7rem; font-weight:700; margin-bottom:8px;
    }
    .pa-pc-divider { border-top:1px solid rgba(255,255,255,.05); margin:7px 0; }
    .pa-pc-row { display:flex; justify-content:space-between; font-size:0.74rem; margin-bottom:5px; }
    .pa-pc-lbl { color:rgba(255,255,255,.4); font-size:0.72rem; font-weight:500; }
    .pa-pc-val { color:#fff; font-weight:600; }
    .pa-wl-bar-bg { width:100%; height:6px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
    .pa-wl-bar-fill { height:100%; border-radius:4px; transition:width .5s ease; }
    .pa-legend {
        background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.06);
        border-radius:12px; padding:14px 18px; margin-top:1rem;
        display:flex; align-items:center; gap:20px; flex-wrap:wrap;
    }
    .pa-legend-title { font-size:0.72rem; font-weight:700; text-transform:uppercase;
                       letter-spacing:.06em; color:rgba(255,255,255,.4); white-space:nowrap; }
    .pa-legend-items { display:flex; gap:18px; flex-wrap:wrap; }
    .pa-legend-item { display:flex; align-items:center; gap:7px; font-size:0.75rem; color:rgba(255,255,255,.5); }
    .pa-legend-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
    </style>
    """
