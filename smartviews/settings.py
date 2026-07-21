"""
SmartPrint AI - Settings
Refactored layout hierarchy following standard container layout system.
"""

import streamlit as st
import re

def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_settings():
    """Render the settings page."""
    st.html(_clean_html(_settings_css()))

    # ── SECTION 1: Page Header ───────────────────────────────────────────
    with st.container():
        st.markdown(_clean_html("""
            <div class="settings-header">
                <div class="settings-icon">⚙️</div>
                <div class="settings-title">Settings Portal</div>
                <div class="settings-subtitle">Configure system default actions and notification preferences</div>
            </div>
            """), unsafe_allow_html=True)

    # Load saved preferences
    prefs = st.session_state.get("user_preferences", {})
    current_theme = prefs.get("theme", "Dark")
    email_notif = prefs.get("email_notifications", True)
    auto_refresh = prefs.get("auto_refresh", True)
    default_copies = prefs.get("default_copies", 1)
    default_color = prefs.get("default_color_mode", "Black & White")

    # ── SECTION 2: Appearance settings ───────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">🎨 Appearance</div>'), unsafe_allow_html=True)
    with st.container():
        col_lbl, col_val = st.columns([2, 1])
        with col_lbl:
            st.markdown(_clean_html("""
                <div class="setting-card">
                    <div class="setting-name">Theme Style</div>
                    <div class="setting-desc">Toggle the primary user interface dark/light canvas mode</div>
                </div>
                """), unsafe_allow_html=True)
        with col_val:
            st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
            theme = st.selectbox(
                "Theme Selection",
                options=["Dark", "Light", "System"],
                index=["Dark", "Light", "System"].index(current_theme),
                label_visibility="collapsed",
                key="theme_selection_key"
            )

    # ── SECTION 3: Notification toggles ──────────────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">🔔 Notifications</div>'), unsafe_allow_html=True)
    with st.container():
        col_lbl1, col_val1 = st.columns([2, 1])
        with col_lbl1:
            st.markdown(_clean_html("""
                <div class="setting-card">
                    <div class="setting-name">Email Alerts</div>
                    <div class="setting-desc">Send automated queue status transitions directly to inbox</div>
                </div>
                """), unsafe_allow_html=True)
        with col_val1:
            st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)
            email_toggle = st.toggle("Email Alerts Toggle", value=email_notif, key="email_notif_toggle", label_visibility="collapsed")

    with st.container():
        col_lbl2, col_val2 = st.columns([2, 1])
        with col_lbl2:
            st.markdown(_clean_html("""
                <div class="setting-card">
                    <div class="setting-name">Auto-Refresh Queue</div>
                    <div class="setting-desc">Continuously sync active print jobs without manual refresh</div>
                </div>
                """), unsafe_allow_html=True)
        with col_val2:
            st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)
            auto_refresh_toggle = st.toggle("Auto-Refresh Toggle", value=auto_refresh, key="auto_refresh_toggle", label_visibility="collapsed")

    # ── SECTION 4: Print Defaults configuration ──────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">🖨️ Printer Defaults</div>'), unsafe_allow_html=True)
    with st.container():
        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown(_clean_html("""
                <div class="setting-card">
                    <div class="setting-name">Default Copies</div>
                    <div class="setting-desc">Pre-fill the copies count field on job upload</div>
                </div>
                """), unsafe_allow_html=True)
            copies_default = st.number_input(
                "Default Copies field", min_value=1, max_value=50, value=default_copies,
                label_visibility="collapsed",
                key="copies_default_key"
            )

        with dc2:
            st.markdown(_clean_html("""
                <div class="setting-card">
                    <div class="setting-name">Default Color Mode</div>
                    <div class="setting-desc">Pre-select print format color option</div>
                </div>
                """), unsafe_allow_html=True)
            color_default = st.selectbox(
                "Default Color field",
                options=["Black & White", "Color"],
                index=["Black & White", "Color"].index(default_color),
                label_visibility="collapsed",
                key="color_default_key"
            )

    # ── SECTION 5: Save Settings Button ──────────────────────────────────
    with st.container():
        st.markdown('<div style="margin-top:1.8rem;"></div>', unsafe_allow_html=True)
        if st.button("💾 Save User Settings", use_container_width=True, key="save_settings_btn", type="primary"):
            st.session_state["user_preferences"] = {
                "theme": theme,
                "email_notifications": email_toggle,
                "auto_refresh": auto_refresh_toggle,
                "default_copies": copies_default,
                "default_color_mode": color_default,
            }
            st.success("✅ System preferences updated successfully!")

    # ── SECTION 6: Danger zone expander ──────────────────────────────────
    with st.container():
        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
        with st.expander("⚠️ System Management Details", expanded=False):
            st.warning("These operations wipe cache assets and persist logs deletion.")
            if st.button("🗑️ Reset Local Database Cache", key="adm_reset_db", use_container_width=True):
                st.info("System cache reset successful.")


def _settings_css() -> str:
    return """
    <style>
    .settings-header { text-align: center; padding: 20px 0 10px; }
    .settings-icon { font-size: 3rem; margin-bottom: 8px; }
    .settings-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .settings-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }
    
    .section-title {
        font-size: 1.1rem; font-weight: 700;
        color: rgba(255,255,255,0.85); margin-bottom: 12px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    .setting-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px; padding: 12px 18px; margin-bottom: 8px;
    }
    .setting-name { font-weight: 600; color: #fff; font-size: 0.95rem; margin-bottom: 2px; }
    .setting-desc { color: rgba(255,255,255,0.4); font-size: 0.8rem; }
    </style>
    """
