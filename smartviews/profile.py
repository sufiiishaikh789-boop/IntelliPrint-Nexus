"""
SmartPrint AI - Profile Page
Refactored layout hierarchy following standard container layout system.
"""

import streamlit as st
import re
from datetime import datetime

from smartdb.crud import get_user_jobs, update_user_credentials
from smartauth.security import hash_password


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

def show_profile():
    """Render the user profile page."""
    user = st.session_state.get("user", {})
    username = user.get("username", "User")
    email = user.get("email", "user@example.com")
    role = user.get("role", "student").title()
    member_since = user.get("created_at", datetime.now().isoformat())[:10]
    user_id = user.get("id", 0)

    st.html(_clean_html(_profile_css()))

    # ── SECTION 1: Page Header & Hero Avatar ──────────────────────────────
    with st.container():
        st.markdown(_clean_html(f"""
            <div class="profile-hero">
                <div class="profile-avatar">{username[0].upper() if username else 'U'}</div>
                <div class="profile-name">{username}</div>
                <div class="profile-role-badge">{role} Account</div>
            </div>
            """), unsafe_allow_html=True)

    # ── SECTION 2: User Account Attributes ────────────────────────────────
    st.markdown(_clean_html('<div class="section-title">👤 Account Information</div>'), unsafe_allow_html=True)
    with st.container():
        st.markdown(_clean_html(f"""
            <div class="profile-info-card">
                <div class="info-row">
                    <span class="info-icon">👤</span>
                    <span class="info-label">Username</span>
                    <span class="info-value">{username}</span>
                </div>
                <div class="info-row">
                    <span class="info-icon">📧</span>
                    <span class="info-label">Email Address</span>
                    <span class="info-value">{email}</span>
                </div>
                <div class="info-row">
                    <span class="info-icon">🛡️</span>
                    <span class="info-label">User Privilege</span>
                    <span class="info-value">{role}</span>
                </div>
                <div class="info-row">
                    <span class="info-icon">📅</span>
                    <span class="info-label">Registration Date</span>
                    <span class="info-value">{member_since}</span>
                </div>
            </div>
            """), unsafe_allow_html=True)

    # ── SECTION 3: Account Statistics ────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">📊 Account Statistics</div>'), unsafe_allow_html=True)
    
    all_jobs = get_user_jobs(user_id) or []
    total_jobs = len(all_jobs)
    total_pages = sum(j.get("pages", 0) * j.get("copies", 1) for j in all_jobs)
    total_spent = sum(j.get("cost", 0) for j in all_jobs)
    completed = sum(1 for j in all_jobs if j.get("status", "").lower() in ("completed", "ready"))

    with st.container():
        s1, s2, s3, s4 = st.columns(4)
        _stat_card(s1, "📄", "Total Jobs", total_jobs, "#00D9FF")
        _stat_card(s2, "📃", "Total Pages", total_pages, "#3b82f6")
        _stat_card(s3, "💰", "Total Spent", f"₹{total_spent:.0f}", "#10b981")
        _stat_card(s4, "✅", "Completed", completed, "#06b6d4")

    # ── SECTION 4: Edit Profile Forms ─────────────────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">✏️ Edit profile credentials</div>'), unsafe_allow_html=True)
    with st.container():
        with st.form("edit_profile_form", clear_on_submit=False):
            st.markdown('<span class="form-wrapper-marker" style="display:none;"></span>', unsafe_allow_html=True)
            new_email = st.text_input("New Email", value=email)
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_password = st.text_input(
                    "New Password", type="password", placeholder="Leave blank to retain current"
                )
            with col_p2:
                confirm_password = st.text_input(
                    "Confirm New Password", type="password", placeholder="Confirm new password"
                )
            update_btn = st.form_submit_button("💾 Save Profile Changes", use_container_width=True)

        if update_btn:
            if new_password and new_password != confirm_password:
                st.error("Passwords do not match.")
            elif not new_email or "@" not in new_email or "." not in new_email:
                st.error("Invalid email address.")
            else:
                pwd_hash = hash_password(new_password) if new_password else None
                success = update_user_credentials(user_id, new_email, pwd_hash)
                if success:
                    st.session_state["user"]["email"] = new_email
                    st.success("✅ Profile credentials updated successfully in database!")
                    st.rerun()
                else:
                    st.error("Failed to update profile. User not found in database.")



def _stat_card(column, icon: str, label: str, value, color: str):
    with column:
        st.markdown(_clean_html(f"""
            <div class="pstat-card" style="border-top: 3px solid {color};">
                <div class="pstat-icon">{icon}</div>
                <div class="pstat-value">{value}</div>
                <div class="pstat-label">{label}</div>
            </div>
            """), unsafe_allow_html=True)


def _profile_css() -> str:
    return """
    <style>
    .profile-hero { text-align: center; padding: 20px 0 10px; }
    .profile-avatar {
        width: 80px; height: 80px; border-radius: 50%;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 2.2rem; font-weight: 800; color: #fff; margin-bottom: 10px;
        box-shadow: 0 8px 30px rgba(0,217,255,0.25);
    }
    .profile-name { font-size: 1.6rem; font-weight: 800; color: #fff; margin-bottom: 4px; }
    .profile-role-badge {
        display: inline-block; background: rgba(0,217,255,0.15); color: #00D9FF;
        padding: 3px 16px; border-radius: 20px; font-size: 0.78rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.8px;
    }
    
    .section-title {
        font-size: 1.1rem; font-weight: 700;
        color: rgba(255,255,255,0.85); margin-bottom: 12px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    .profile-info-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px; padding: 16px 22px; backdrop-filter: blur(10px);
    }
    .info-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }
    .info-row:last-child { border-bottom: none; }
    .info-icon { font-size: 1.1rem; margin-right: 12px; }
    .info-label { color: rgba(255,255,255,0.45); font-size: 0.82rem; min-width: 120px; font-weight: 500; }
    .info-value { color: #fff; font-weight: 600; font-size: 0.9rem; }
    
    .pstat-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 16px 12px; text-align: center; backdrop-filter: blur(10px);
        transition: transform 0.25s ease;
    }
    .pstat-card:hover { transform: translateY(-2px); }
    .pstat-icon { font-size: 1.4rem; margin-bottom: 4px; }
    .pstat-value { font-size: 1.45rem; font-weight: 800; color: #fff; }
    .pstat-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; }
    
    .form-wrapper { background: rgba(255,255,255,0.02); padding: 10px; border-radius: 12px; }
    div[data-testid="stForm"] { border: 1px solid rgba(255,255,255,0.06) !important; background: rgba(255,255,255,0.02) !important; border-radius: 16px !important; }
    </style>
    """
