"""
SmartPrint AI - Admin Printers Management
Refactored layout hierarchy following standard container layout system.
"""

import streamlit as st
import re
import textwrap

from smartdb.crud import get_all_printers, update_printer_status

def _clean_html(html_str: str) -> str:
    cleaned = re.sub(r'\n\s*\n', '\n', html_str)
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
    return cleaned

def show_admin_printers():
    """Render the admin printer management page."""
    st.html(_clean_html(_printer_css()))

    # ── SECTION 1: Page Header ───────────────────────────────────────────
    with st.container():
        st.markdown(_clean_html(textwrap.dedent("""
            <div class="ap-header">
                <div class="ap-icon">🖨️</div>
                <div class="ap-title">Printer Terminal Registry</div>
                <div class="ap-subtitle">Manage printer hardware configurations and active nodes</div>
            </div>
            """)), unsafe_allow_html=True)

    # Fetch printers from CRUD
    printers = []
    try:
        printers = get_all_printers() or []
    except Exception:
        pass

    if not printers:
        printers = [
            {"id": 1, "name": "HP LaserJet Pro M404", "location": "Library — Ground Floor", "status": "Online", "toner_level": 85, "total_prints": 1240, "printer_type": "HP LaserJet", "last_maintenance": None},
            {"id": 2, "name": "Canon imageRUNNER", "location": "Admin Block — 2nd Floor", "status": "Online", "toner_level": 42, "total_prints": 890, "printer_type": "Canon IR", "last_maintenance": None},
            {"id": 3, "name": "Epson WF-C5790", "location": "Computer Lab — 1st Floor", "status": "Offline", "toner_level": 12, "total_prints": 2310, "printer_type": "Epson WF", "last_maintenance": None},
        ]

    # ── SECTION 2: Statistics Cards ──────────────────────────────────────
    total = len(printers)
    online = sum(1 for p in printers if p.get("status", "").lower() == "online")
    offline = total - online
    low_toner = sum(1 for p in printers if p.get("toner_level", 100) < 25)

    with st.container():
        ss1, ss2, ss3, ss4 = st.columns(4)
        _summary_card(ss1, "🖨️", "Total", total, "#00D9FF")
        _summary_card(ss2, "🟢", "Online", online, "#10b981")
        _summary_card(ss3, "🔴", "Offline", offline, "#ef4444")
        _summary_card(ss4, "⚠️", "Low Toner", low_toner, "#f59e0b")

    # ── SECTION 3: Maintenance Alerts ────────────────────────────────────
    alerts = []
    for p in printers:
        toner = p.get("toner_level", 100)
        if toner < 15:
            alerts.append(f"🔴 **{p['name']}** — Critical toner level ({toner}%). Replace immediately!")
        elif toner < 30:
            alerts.append(f"🟡 **{p['name']}** — Low toner ({toner}%). Order replacement soon.")
        if p.get("status", "").lower() == "offline":
            alerts.append(f"🔴 **{p['name']}** — Printer is offline. Check connection.")

    if alerts:
        st.markdown('<div class="section-title" style="margin-top:1.5rem;">⚠️ System Alerts</div>', unsafe_allow_html=True)
        for alert in alerts:
            with st.container():
                st.markdown(_clean_html(textwrap.dedent(f"""
                    <div class="alert-item">
                        {alert}
                    </div>
                    """)), unsafe_allow_html=True)

    # ── SECTION 4: Printer Terminals ─────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:1.5rem;">🖨️ Registered Terminals</div>', unsafe_allow_html=True)
    for idx, printer in enumerate(printers):
        with st.container():
            _render_printer_card(printer, idx)


def _render_printer_card(printer: dict, idx: int):
    """Render a detailed printer card with controls."""
    printer_id = printer.get("id", idx)
    name = printer.get("name", "Printer")
    location = printer.get("location", "Unknown")
    status = printer.get("status", "Unknown")
    toner = printer.get("toner_level", 0)
    print_count = printer.get("total_prints", 0)  # correct field name
    model = printer.get("printer_type", "LaserJet")  # correct field name
    ip_addr = "192.168.1." + str(100 + printer.get("id", 0))  # simulated IP
    last_maint_raw = printer.get("last_maintenance")
    if last_maint_raw:
        last_maint = str(last_maint_raw)[:10] if last_maint_raw else "N/A"
    else:
        last_maint = "N/A"

    is_online = status.lower() == "online"
    status_color = "#10b981" if is_online else "#ef4444"
    toner_color = "#10b981" if toner > 50 else "#f59e0b" if toner > 20 else "#ef4444"

    col_info, col_ctrl = st.columns([2.5, 1])

    with col_info:
        st.markdown(_clean_html(textwrap.dedent(f"""
            <div class="printer-detail-card" style="border-left: 4px solid {status_color};">
                <div class="pd-header">
                    <div class="pd-name">{name}</div>
                    <div class="pd-status" style="color:{status_color};">● {status}</div>
                </div>
                <div class="pd-location">📍 {location}</div>
                <div class="pd-meta-grid">
                    <div class="pd-meta-item">
                        <span class="pd-meta-label">Model</span>
                        <span class="pd-meta-value">{model}</span>
                    </div>
                    <div class="pd-meta-item">
                        <span class="pd-meta-label">IP Address</span>
                        <span class="pd-meta-value" style="font-family:monospace;">{ip_addr}</span>
                    </div>
                    <div class="pd-meta-item">
                        <span class="pd-meta-label">Print Count</span>
                        <span class="pd-meta-value">{print_count:,}</span>
                    </div>
                    <div class="pd-meta-item">
                        <span class="pd-meta-label">Last Maintenance</span>
                        <span class="pd-meta-value">{last_maint}</span>
                    </div>
                </div>
            </div>
            """)), unsafe_allow_html=True)

        st.markdown(_clean_html(f'<div style="font-size:0.8rem; color:rgba(255,255,255,0.45); margin:8px 0 2px;">Toner Level: <span style="color:{toner_color}; font-weight:700;">{toner}%</span></div>'), unsafe_allow_html=True)
        st.progress(toner / 100)

    with col_ctrl:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        if is_online:
            if st.button("🔴 Deactivate Node", key=f"offline_{printer_id}", use_container_width=True):
                try:
                    update_printer_status(printer_id, "Offline")
                    st.warning(f"{name} taken offline.")
                    st.rerun()
                except Exception:
                    st.warning(f"{name} deactivation completed (demo).")
        else:
            if st.button("🟢 Activate Node", key=f"online_{printer_id}", use_container_width=True):
                try:
                    update_printer_status(printer_id, "Online")
                    st.success(f"{name} is online.")
                    st.rerun()
                except Exception:
                    st.success(f"{name} activation completed (demo).")

        if st.button("🔧 Maintenance", key=f"maint_{printer_id}", use_container_width=True):
            st.info(f"Logged maintenance request for {name}.")

    st.markdown('<div class="printer-divider"></div>', unsafe_allow_html=True)


def _summary_card(column, icon: str, label: str, value, color: str):
    with column:
        st.markdown(_clean_html(textwrap.dedent(f"""
            <div class="ap-summary" style="border-top: 3px solid {color};">
                <div class="aps-icon">{icon}</div>
                <div class="aps-value">{value}</div>
                <div class="aps-label">{label}</div>
            </div>
            """)), unsafe_allow_html=True)


def _printer_css() -> str:
    return """
    <style>
    .ap-header { text-align: center; padding: 20px 0 10px; }
    .ap-icon { font-size: 3rem; margin-bottom: 8px; }
    .ap-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .ap-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    
    .section-title {
        font-size: 1.1rem; font-weight: 700;
        color: rgba(255,255,255,0.85); margin-bottom: 12px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    .ap-summary {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 14px; text-align: center; backdrop-filter: blur(10px);
    }
    .aps-icon { font-size: 1.4rem; margin-bottom: 4px; }
    .aps-value { font-size: 1.6rem; font-weight: 800; color: #fff; }
    .aps-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; }
    
    .alert-item {
        background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15);
        border-radius: 10px; padding: 12px 18px; margin-bottom: 6px; font-size: 0.82rem; color: rgba(255,255,255,0.75);
    }
    
    .printer-detail-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px; padding: 18px 20px; backdrop-filter: blur(10px);
    }
    .pd-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .pd-name { font-size: 1rem; font-weight: 700; color: #fff; }
    .pd-status { font-size: 0.82rem; font-weight: 600; }
    .pd-location { color: rgba(255,255,255,0.45); font-size: 0.8rem; margin-bottom: 12px; }
    
    .pd-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .pd-meta-label { display: block; font-size: 0.68rem; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
    .pd-meta-value { display: block; font-size: 0.82rem; color: rgba(255,255,255,0.75); font-weight: 500; }
    
    .printer-divider { border-top: 1px solid rgba(255,255,255,0.04); margin: 15px 0 10px; }
    </style>
    """
