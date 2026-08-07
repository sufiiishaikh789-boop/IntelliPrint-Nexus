"""
IntelliPrint Nexus - Enhanced Settings Page (Phase 3)
Default printer, default print options, notification preferences.
"""

import streamlit as st


_DEFAULT_SETTINGS = {
    "default_copies":      1,
    "default_color_mode":  "BW",
    "default_duplex":      False,
    "default_paper_size":  "A4",
    "default_priority":    "Normal",
    "notify_upload":       True,
    "notify_ai":           True,
    "notify_payment":      True,
    "notify_queue":        True,
    "notify_printing":     True,
    "notify_completed":    True,
    "notify_ready":        True,
    "notify_collected":    True,
    "notify_cancelled":    True,
}


def show_settings():
    """Render the enhanced student settings page."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_settings_css())

    st.html("""
    <div class="sett-header">
        <div class="sett-title">⚙️ Settings</div>
        <div class="sett-sub">Configure your default printing preferences and notification options</div>
    </div>
    """)

    # ── Load settings ─────────────────────────────────────────────────────────
    settings = {}
    try:
        from smartdb.crud_ext import get_user_settings
        settings = get_user_settings(user_id) or {}
    except Exception:
        pass

    # Merge with defaults
    s = {**_DEFAULT_SETTINGS, **settings}

    # ── Printer list for default selection ────────────────────────────────────
    printers = []
    printer_names = ["(No preference)"]
    try:
        from smartdb.crud import get_all_printers
        printers = get_all_printers() or []
        printer_names += [p.get("name", f"Printer {p['id']}") for p in printers
                          if (p.get("status") or "").lower() not in ("offline", "maintenance")]
    except Exception:
        pass

    # ── Default Print Settings ────────────────────────────────────────────────
    st.html('<div class="sett-section">🖨️ Default Print Settings</div>')

    with st.form("settings_print_form"):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            fav_printer_stored = s.get("default_printer", "(No preference)")
            fav_idx = printer_names.index(fav_printer_stored) if fav_printer_stored in printer_names else 0
            new_printer = st.selectbox(
                "⭐ Default Printer",
                printer_names,
                index=fav_idx,
                key="sett_printer",
                help="Your preferred printer will be pre-selected on the upload page.",
            )
            new_copies = st.number_input(
                "📄 Default Copies",
                min_value=1, max_value=50,
                value=int(s.get("default_copies", 1)),
                key="sett_copies",
            )

        with pc2:
            new_color = st.selectbox(
                "🎨 Default Colour Mode",
                ["BW", "Color"],
                index=0 if s.get("default_color_mode", "BW") == "BW" else 1,
                key="sett_color",
            )
            new_paper = st.selectbox(
                "📐 Default Paper Size",
                ["A4", "A3", "Letter", "Legal"],
                index=["A4", "A3", "Letter", "Legal"].index(s.get("default_paper_size", "A4")),
                key="sett_paper",
            )

        with pc3:
            new_duplex = st.checkbox(
                "📃 Default Duplex (Double-sided)",
                value=bool(s.get("default_duplex", False)),
                key="sett_duplex",
                help="Save paper by printing on both sides by default.",
            )
            new_priority = st.selectbox(
                "⚡ Default Priority",
                ["Normal", "High", "Urgent"],
                index=["Normal", "High", "Urgent"].index(s.get("default_priority", "Normal")),
                key="sett_priority",
            )

        save_print = st.form_submit_button("💾 Save Print Settings", use_container_width=True)
        if save_print:
            try:
                from smartdb.crud_ext import save_user_settings
                save_user_settings(user_id, {
                    "default_printer":    new_printer,
                    "default_copies":     new_copies,
                    "default_color_mode": new_color,
                    "default_paper_size": new_paper,
                    "default_duplex":     new_duplex,
                    "default_priority":   new_priority,
                })
                st.success("✅ Print settings saved!")
                # Store in session for upload page to read
                st.session_state["user_print_settings"] = {
                    "printer":    new_printer,
                    "copies":     new_copies,
                    "color_mode": new_color,
                    "paper_size": new_paper,
                    "duplex":     new_duplex,
                    "priority":   new_priority,
                }
                st.rerun()
            except Exception as e:
                st.error(f"Could not save settings: {e}")

    # ── Notification Preferences ──────────────────────────────────────────────
    st.html('<div class="sett-section">🔔 Notification Preferences</div>')
    st.caption("Choose which events trigger notifications in your Notification Center.")

    with st.form("settings_notif_form"):
        nc1, nc2 = st.columns(2)
        notif_fields = [
            ("notify_upload",    "📤 Document Upload"),
            ("notify_ai",        "🤖 AI Analysis Complete"),
            ("notify_payment",   "💳 Payment Received"),
            ("notify_queue",     "📋 Queue Assigned"),
            ("notify_printing",  "🖨️ Printing Started"),
            ("notify_completed", "✅ Printing Completed"),
            ("notify_ready",     "📦 Ready for Pickup"),
            ("notify_collected", "🎉 Document Collected"),
            ("notify_cancelled", "❌ Job Cancelled"),
        ]
        new_notif = {}
        for i, (key, label) in enumerate(notif_fields):
            with (nc1 if i % 2 == 0 else nc2):
                new_notif[key] = st.checkbox(
                    label,
                    value=bool(s.get(key, True)),
                    key=f"sett_{key}",
                )

        save_notif = st.form_submit_button("💾 Save Notification Settings", use_container_width=True)
        if save_notif:
            try:
                from smartdb.crud_ext import save_user_settings
                save_user_settings(user_id, new_notif)
                st.success("✅ Notification preferences saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save preferences: {e}")

    # ── Reset to defaults ─────────────────────────────────────────────────────
    st.html('<div class="sett-section">🔄 Reset</div>')
    if st.button("🔄 Reset All Settings to Default", key="sett_reset"):
        try:
            from smartdb.crud_ext import save_user_settings
            save_user_settings(user_id, _DEFAULT_SETTINGS)
            if "user_print_settings" in st.session_state:
                del st.session_state["user_print_settings"]
            st.success("✅ Settings reset to defaults.")
            st.rerun()
        except Exception as e:
            st.error(f"Reset failed: {e}")

    # ── Current settings preview ──────────────────────────────────────────────
    st.html('<div class="sett-section">👁️ Current Configuration</div>')
    cfg_items = [
        ("Default Printer",    s.get("default_printer", "No preference")),
        ("Default Copies",     str(s.get("default_copies", 1))),
        ("Colour Mode",        s.get("default_color_mode", "BW")),
        ("Paper Size",         s.get("default_paper_size", "A4")),
        ("Duplex",             "Yes" if s.get("default_duplex") else "No"),
        ("Priority",           s.get("default_priority", "Normal")),
    ]
    cfg_cols = st.columns(3)
    for i, (label, val) in enumerate(cfg_items):
        with cfg_cols[i % 3]:
            st.html(f"""
            <div class="sett-cfg-row">
                <div class="scr-label">{label}</div>
                <div class="scr-val">{val}</div>
            </div>
            """)


def _settings_css() -> str:
    return """<style>
.sett-header { padding:14px 0 10px; margin-bottom:1rem; }
.sett-title {
    font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.sett-sub { color:rgba(255,255,255,.4); font-size:.88rem; margin-top:4px; }
.sett-section {
    font-size:.95rem; font-weight:700; color:rgba(255,255,255,.75);
    text-transform:uppercase; letter-spacing:.5px;
    margin:1.5rem 0 10px; padding-bottom:6px;
    border-bottom:1px solid rgba(255,255,255,.07);
}
.sett-cfg-row {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
    border-radius:10px; padding:12px 14px; margin-bottom:8px;
}
.scr-label { font-size:.7rem; color:rgba(255,255,255,.4);
             text-transform:uppercase; letter-spacing:.4px; }
.scr-val { font-size:1rem; font-weight:700; color:#3B82F6; margin-top:2px; }
</style>"""
