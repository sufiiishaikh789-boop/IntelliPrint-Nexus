"""
IntelliPrint Nexus - Admin Printer Management (Upgraded)
Full printer management: add, remove, configure, monitor health and consumables.
"""

import streamlit as st
from datetime import datetime
from smartdb.crud import (
    get_all_printers, update_printer_status,
    add_printer, delete_printer, update_printer_fields,
    get_all_jobs
)


def _safe_dt(value) -> "datetime | None":
    """Safely convert value to datetime. Returns None on failure."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s or s in ("-", "None", "null"):
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None  # Unparseable — return None rather than crash


def show_admin_printers():
    """Render the full printer management page."""
    st.html(_pr_css())

    st.markdown("""
    <div class="pr-header">
        <div class="pr-title">🖨️ Printer Management</div>
        <div class="pr-subtitle">Add, configure, monitor and control all printer hardware nodes</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────────
    printers = []
    all_jobs = []
    try:
        printers = get_all_printers() or []
        all_jobs = get_all_jobs() or []
    except Exception as e:
        st.error(f"Error loading printers: {e}")

    # ── Summary strip ─────────────────────────────────────────────────────
    total = len(printers)
    online_c = sum(1 for p in printers if (p.get("status") or "").lower() == "online")
    offline_c = sum(1 for p in printers if (p.get("status") or "").lower() == "offline")
    maint_c = sum(1 for p in printers if (p.get("status") or "").lower() == "maintenance")
    low_toner_c = sum(1 for p in printers if (p.get("toner_level") or 100) < 20)

    s1, s2, s3, s4, s5 = st.columns(5)
    _pr_stat(s1, "🖨️ Total", total, "#3B82F6")
    _pr_stat(s2, "🟢 Online", online_c, "#10b981")
    _pr_stat(s3, "🔴 Offline", offline_c, "#ef4444")
    _pr_stat(s4, "🟡 Maintenance", maint_c, "#f59e0b")
    _pr_stat(s5, "⚠️ Low Toner", low_toner_c, "#f97316")

    # ── Add Printer Section ───────────────────────────────────────────────
    with st.expander("➕ Add New Printer", expanded=False):
        with st.form("add_printer_form", clear_on_submit=True):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                new_name = st.text_input("Printer Name*", placeholder="e.g. HP LaserJet Pro M404")
                new_loc = st.text_input("Location*", placeholder="e.g. Library — Ground Floor")
                new_type = st.selectbox("Printer Type", ["LaserJet", "InkJet", "InkTank", "LaserJet Multifunction", "LED"])
            with ac2:
                new_status = st.selectbox("Initial Status", ["Online", "Idle", "Offline", "Maintenance"])
                new_toner = st.slider("Initial Toner Level (%)", 0, 100, 100)
                new_ppm = st.number_input("Speed (PPM)", min_value=1, max_value=200, value=20,
                                          help="Pages Per Minute — used for realistic print time calculation")
            with ac3:
                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                st.markdown("""<div style="font-size:.78rem;color:rgba(255,255,255,.4);padding:8px 0;">
                    <b>PPM Guide</b><br>LaserJet: 20-40 ppm<br>InkJet: 8-15 ppm<br>High-speed: 40-80 ppm
                    </div>""", unsafe_allow_html=True)
                submitted = st.form_submit_button("✅ Add Printer", use_container_width=True)
            if submitted:
                if not new_name.strip() or not new_loc.strip():
                    st.error("Printer name and location are required.")
                else:
                    try:
                        from smartdb.crud import add_printer
                        add_printer(new_name.strip(), new_loc.strip(), new_type, new_toner, new_status, ppm=int(new_ppm))
                        st.success(f"✅ Printer '{new_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add printer: {e}")

    st.markdown("---")

    # ── Printer Cards ─────────────────────────────────────────────────────
    if not printers:
        st.markdown("""
        <div class="pr-empty">
            <div style="font-size:3rem;">🖨️</div>
            <div class="pr-empty-title">No Printers Found</div>
            <div class="pr-empty-desc">Add a printer using the form above to get started.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for p in printers:
        _render_printer_card(p, all_jobs)


def _render_printer_card(p: dict, all_jobs: list):
    """Render a full printer management card."""
    pid = p.get("id")
    name = p.get("name", "Printer")
    location = p.get("location", "—")
    status = p.get("status", "Unknown")
    toner = p.get("toner_level") or 0
    temp = p.get("temperature") or 35
    errors = p.get("error_count") or 0
    total_prints = p.get("total_prints") or 0
    printer_type = p.get("printer_type", "LaserJet")

    # ── Safe datetime handling ─────────────────────────────────────────────
    last_maint_dt = _safe_dt(p.get("last_maintenance"))
    last_maint_str = last_maint_dt.strftime("%Y-%m-%d") if last_maint_dt else "—"

    # ── Compute health (safe — no string arithmetic) ───────────────────────
    days_since_maint = (datetime.utcnow() - last_maint_dt).days if last_maint_dt else 0
    health = max(0, min(100,
        100
        - max(0, (50 - toner) * 0.5)
        - errors * 4
        - max(0, (temp - 40) * 2)
        - max(0, (days_since_maint - 90) * 0.3)
    ))
    health_label = ("Excellent" if health >= 90 else "Good" if health >= 70
                    else "Average" if health >= 50 else "Needs Service")
    health_color = "#10b981" if health > 70 else "#f59e0b" if health > 40 else "#ef4444"
    status_color = {"online": "#10b981", "offline": "#ef4444", "maintenance": "#f59e0b"}.get(status.lower(), "#6b7280")
    toner_color = "#10b981" if toner > 40 else "#f59e0b" if toner > 15 else "#ef4444"
    temp_color = "#ef4444" if temp > 45 else "#f59e0b" if temp > 40 else "#10b981"

    # Jobs for this printer
    printer_jobs = [j for j in all_jobs if j.get("printer_id") == pid]
    active_jobs = [j for j in printer_jobs if (j.get("status") or "").lower() in ("printing", "queued")]
    current_job = next((j for j in printer_jobs if (j.get("status") or "").lower() == "printing"), None)
    queue_len = len([j for j in printer_jobs if (j.get("status") or "").lower() == "queued"])

    with st.container():
        st.markdown(f"""
        <div class="pr-card">
            <div class="pr-card-top">
                <div>
                    <div class="pr-card-name">🖨️ {name}</div>
                    <div class="pr-card-type">{printer_type}</div>
                    <div class="pr-card-loc">📍 {location}</div>
                </div>
                <div class="pr-card-status-block">
                    <span class="pr-status-badge" style="background:{status_color}22;color:{status_color};border:1px solid {status_color}55;">● {status}</span>
                    <div class="pr-health-label">Health: <b style="color:{health_color};">{health:.0f}%</b> — {health_label}</div>
                </div>
            </div>
            <div class="pr-metrics">
                <div class="pr-metric-item"><div class="pr-mv" style="color:#3B82F6;">{total_prints:,}</div><div class="pr-ml">Total Prints</div></div>
                <div class="pr-metric-item"><div class="pr-mv" style="color:{toner_color};">{toner:.0f}%</div><div class="pr-ml">Toner</div></div>
                <div class="pr-metric-item"><div class="pr-mv" style="color:{temp_color};">{temp}°C</div><div class="pr-ml">Temp</div></div>
                <div class="pr-metric-item"><div class="pr-mv" style="color:#3b82f6;">{queue_len}</div><div class="pr-ml">In Queue</div></div>
                <div class="pr-metric-item"><div class="pr-mv">{p.get('pages_per_minute', 20)}</div><div class="pr-ml">PPM</div></div>
                <div class="pr-metric-item"><div class="pr-mv" style="color:{'#ef4444' if errors>5 else '#fff'};">{errors}</div><div class="pr-ml">Errors</div></div>
                <div class="pr-metric-item"><div class="pr-mv" style="font-size:.8rem;">{last_maint_str}</div><div class="pr-ml">Last Maint.</div></div>
            </div>
            {f'<div class="pr-current-job">🖨️ Currently Printing: <b>{current_job.get("document_name","")[:35]}</b> — {current_job.get("print_id","")}</div>' if current_job else ''}
        </div>
        """, unsafe_allow_html=True)

        # Toner bar
        st.markdown(f"""
        <div style="padding:0 0 8px;">
            <div style="display:flex;justify-content:space-between;font-size:.72rem;color:rgba(255,255,255,.4);margin-bottom:3px;">
                <span>Toner Level{' ⚠️ LOW' if toner < 20 else ''}</span><span>{toner:.0f}%</span>
            </div>
            <div class="pr-bar-bg"><div class="pr-bar-fill" style="width:{toner:.0f}%;background:{toner_color};"></div></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Action buttons ────────────────────────────────────────────────
        b1, b2, b3, b4, b5, b6, b7, _ = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
        with b1:
            if st.button("🟢 Online", key=f"pr_on_{pid}", help="Set Online"):
                update_printer_status(pid, "Online")
                st.rerun()
        with b2:
            if st.button("🔵 Idle", key=f"pr_idle_{pid}", help="Set Idle"):
                update_printer_status(pid, "Idle")
                st.rerun()
        with b3:
            if st.button("🔴 Offline", key=f"pr_off_{pid}", help="Set Offline"):
                update_printer_status(pid, "Offline")
                st.rerun()
        with b4:
            if st.button("🟡 Maint.", key=f"pr_maint_{pid}", help="Set Maintenance"):
                update_printer_status(pid, "Maintenance")
                st.rerun()
        with b5:
            if st.button("✏️ Edit", key=f"pr_edit_{pid}", help="Edit Printer"):
                st.session_state[f"pr_edit_open_{pid}"] = not st.session_state.get(f"pr_edit_open_{pid}", False)
        with b6:
            if st.button("🔧 Maintain", key=f"pr_service_{pid}", help="Log Maintenance"):
                update_printer_fields(pid, last_maintenance=datetime.utcnow(), error_count=0)
                st.success(f"Maintenance logged for {name}.")
                st.rerun()
        with b7:
            if st.button("🗑️ Delete", key=f"pr_del_{pid}", help="Delete Printer"):
                st.session_state[f"pr_confirm_del_{pid}"] = True

        # Delete confirmation
        if st.session_state.get(f"pr_confirm_del_{pid}"):
            st.warning(f"⚠️ Are you sure you want to delete **{name}**? This cannot be undone.")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("✅ Yes, Delete", key=f"pr_del_yes_{pid}"):
                    delete_printer(pid)
                    st.success(f"Printer '{name}' deleted.")
                    st.session_state.pop(f"pr_confirm_del_{pid}", None)
                    st.rerun()
            with dc2:
                if st.button("❌ Cancel", key=f"pr_del_no_{pid}"):
                    st.session_state.pop(f"pr_confirm_del_{pid}", None)
                    st.rerun()

        # ── Edit form ─────────────────────────────────────────────────────
        if st.session_state.get(f"pr_edit_open_{pid}"):
            with st.expander(f"✏️ Edit — {name}", expanded=True):
                with st.form(f"edit_printer_{pid}", clear_on_submit=False):
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        edit_name = st.text_input("Name", value=name, key=f"ename_{pid}")
                        edit_loc = st.text_input("Location", value=location, key=f"eloc_{pid}")
                        edit_type = st.text_input("Type", value=printer_type, key=f"etype_{pid}")
                    with ec2:
                        edit_toner = st.slider("Toner Level (%)", 0, 100, int(toner), key=f"etoner_{pid}")
                        edit_ppm = st.number_input("Speed (PPM)", min_value=1, max_value=200,
                                                   value=int(p.get("pages_per_minute", 20) or 20),
                                                   key=f"eppm_{pid}")
                    with ec3:
                        edit_status = st.selectbox(
                            "Status",
                            ["Online", "Idle", "Offline", "Maintenance", "Busy",
                             "Paper Jam", "Low Paper", "Low Toner", "Error"],
                            index=["Online", "Idle", "Offline", "Maintenance", "Busy",
                                   "Paper Jam", "Low Paper", "Low Toner", "Error"].index(status)
                                  if status in ["Online", "Idle", "Offline", "Maintenance", "Busy",
                                                "Paper Jam", "Low Paper", "Low Toner", "Error"] else 0,
                            key=f"estatus_{pid}",
                        )
                    save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    if save:
                        update_printer_fields(pid,
                                              name=edit_name.strip(),
                                              location=edit_loc.strip(),
                                              printer_type=edit_type.strip(),
                                              toner_level=float(edit_toner),
                                              pages_per_minute=int(edit_ppm),
                                              status=edit_status)
                        st.success(f"Printer '{edit_name}' updated!")
                        st.session_state[f"pr_edit_open_{pid}"] = False
                        st.rerun()
                if st.button("✕ Close Edit", key=f"pr_edit_close_{pid}"):
                    st.session_state[f"pr_edit_open_{pid}"] = False
                    st.rerun()

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)


def _pr_stat(col, label, value, color):
    with col:
        st.markdown(f"""
        <div class="pr-stat" style="border-left:3px solid {color};">
            <div class="pr-stat-label">{label}</div>
            <div class="pr-stat-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def _pr_css() -> str:
    return """<style>
.pr-header { padding:18px 0 12px; margin-bottom:1rem; }
.pr-title { font-size:1.9rem; font-weight:800; color:#fff; }
.pr-subtitle { color:rgba(255,255,255,.45); font-size:.9rem; margin-top:4px; }
.pr-stat { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:12px; padding:12px 16px; margin-bottom:12px; }
.pr-stat-label { font-size:.75rem; color:rgba(255,255,255,.45); font-weight:600; text-transform:uppercase; }
.pr-stat-value { font-size:1.5rem; font-weight:800; margin-top:2px; }
.pr-card { background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.07); border-radius:14px; padding:18px; margin-bottom:4px; }
.pr-card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }
.pr-card-name { font-size:1.1rem; font-weight:700; color:#fff; }
.pr-card-type { font-size:.75rem; color:#3B82F6; margin-top:2px; font-weight:600; }
.pr-card-loc { font-size:.78rem; color:rgba(255,255,255,.4); margin-top:4px; }
.pr-card-status-block { text-align:right; }
.pr-status-badge { padding:4px 12px; border-radius:12px; font-size:.78rem; font-weight:700; }
.pr-health-label { font-size:.75rem; color:rgba(255,255,255,.4); margin-top:6px; }
.pr-metrics { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.pr-metric-item { flex:1; min-width:70px; text-align:center; background:rgba(255,255,255,.03); border-radius:8px; padding:8px 4px; }
.pr-mv { font-size:1.05rem; font-weight:800; color:#fff; }
.pr-ml { font-size:.62rem; color:rgba(255,255,255,.4); margin-top:2px; text-transform:uppercase; letter-spacing:.3px; }
.pr-current-job { margin-bottom:8px; padding:8px 12px; background:rgba(0,217,255,.06); border:1px solid rgba(0,217,255,.15); border-radius:8px; font-size:.82rem; color:rgba(255,255,255,.7); }
.pr-bar-bg { height:6px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
.pr-bar-fill { height:6px; border-radius:4px; transition:width .4s; }
.pr-empty { text-align:center; padding:60px 20px; background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.05); border-radius:16px; margin:20px 0; }
.pr-empty-title { font-size:1.2rem; font-weight:700; color:#fff; margin:10px 0 6px; }
.pr-empty-desc { color:rgba(255,255,255,.4); font-size:.88rem; }
</style>"""
