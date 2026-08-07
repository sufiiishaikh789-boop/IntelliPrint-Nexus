"""
IntelliPrint Nexus - Enhanced Student Profile (Phase 3)
Extended profile with department, course, phone, stats, and editable fields.
"""

import streamlit as st
from datetime import datetime


def show_profile():
    """Render the enhanced student profile page."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_profile_css())

    st.html("""
    <div class="prof-header">
        <div class="prof-title">👤 My Profile</div>
        <div class="prof-sub">Manage your account and personal details</div>
    </div>
    """)

    # ── Load profile ──────────────────────────────────────────────────────────
    profile = {}
    analytics = {}
    fav_printer = None
    try:
        from smartdb.crud_ext import get_user_profile, get_student_analytics, get_favorite_printer
        profile     = get_user_profile(user_id)     or {}
        analytics   = get_student_analytics(user_id) or {}
        fav_printer = get_favorite_printer(user_id)
    except Exception:
        profile = user.copy()

    username   = profile.get("username", user.get("username", "Student"))
    email      = profile.get("email", user.get("email", ""))
    role       = profile.get("role", "Student")
    student_id = profile.get("student_id") or ""
    department = profile.get("department") or ""
    course     = profile.get("course")     or ""
    phone      = profile.get("phone")      or ""
    joined     = profile.get("created_at")
    last_login = profile.get("last_login")

    # ── Layout: info card left, stats right ───────────────────────────────────
    pc1, pc2 = st.columns([2, 3])

    with pc1:
        joined_str = ""
        if joined:
            try:
                d = joined if isinstance(joined, datetime) else datetime.fromisoformat(str(joined))
                joined_str = d.strftime("%B %Y")
            except Exception:
                joined_str = str(joined)[:10]

        login_str = ""
        if last_login:
            try:
                d = last_login if isinstance(last_login, datetime) else datetime.fromisoformat(str(last_login))
                login_str = d.strftime("%Y-%m-%d %H:%M")
            except Exception:
                login_str = str(last_login)[:16]

        avatar_letter = username[0].upper() if username else "S"

        st.html(f"""
        <div class="prof-card">
            <div class="prof-avatar">{avatar_letter}</div>
            <div class="prof-username">{username}</div>
            <div class="prof-role">{role}</div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">📧</span>
                <span class="prof-detail-val">{email or '—'}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">🎓</span>
                <span class="prof-detail-val">{student_id or '—'}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">🏛️</span>
                <span class="prof-detail-val">{department or '—'}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">📚</span>
                <span class="prof-detail-val">{course or '—'}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">📱</span>
                <span class="prof-detail-val">{phone or '—'}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">📅</span>
                <span class="prof-detail-val">Joined {joined_str}</span>
            </div>
            <div class="prof-detail-row">
                <span class="prof-detail-icon">🕐</span>
                <span class="prof-detail-val">Last login: {login_str or '—'}</span>
            </div>
        </div>
        """)

    with pc2:
        # Quick stats
        st.html('<div class="prof-section-title">📊 Printing Summary</div>')
        stats_data = [
            ("📄", "Total Jobs",     analytics.get("total_jobs", 0),          "#3B82F6"),
            ("📑", "Total Pages",    analytics.get("total_pages", 0),         "#3b82f6"),
            ("💰", "Total Spent",    f"₹{analytics.get('total_spent', 0):.2f}", "#10b981"),
            ("⭐", "Fav. Printer",   fav_printer or "—",                       "#f59e0b"),
            ("♻️", "Paper Saved",    f"{analytics.get('paper_saved', 0)} sheets", "#84cc16"),
            ("✅", "Completed",      analytics.get("completed_jobs", 0),       "#6b7280"),
        ]
        stat_cols = st.columns(3)
        for i, (icon, label, val, color) in enumerate(stats_data):
            with stat_cols[i % 3]:
                st.html(f"""
                <div class="prof-stat-card" style="border-top:2px solid {color};">
                    <div class="psc-icon">{icon}</div>
                    <div class="psc-val" style="color:{color};">{val}</div>
                    <div class="psc-label">{label}</div>
                </div>
                """)

    # ── Edit Profile Form ─────────────────────────────────────────────────────
    st.html('<div class="prof-section-title">✏️ Edit Profile</div>')

    with st.form("edit_profile_form"):
        fc1, fc2 = st.columns(2)
        with fc1:
            new_student_id = st.text_input("🎓 Student ID",   value=student_id, key="ep_sid",
                                           placeholder="e.g. CS2021001")
            new_department = st.text_input("🏛️ Department",   value=department, key="ep_dept",
                                           placeholder="e.g. Computer Science")
            new_course     = st.text_input("📚 Course",       value=course,     key="ep_course",
                                           placeholder="e.g. B.Tech CSE")
        with fc2:
            new_phone      = st.text_input("📱 Phone",        value=phone,      key="ep_phone",
                                           placeholder="e.g. +91 98765 43210")
            new_email      = st.text_input("📧 Email",        value=email,      key="ep_email",
                                           placeholder="your@email.com")

        st.caption("⚠️ Username and role cannot be changed. Contact admin for account issues.")
        save = st.form_submit_button("💾 Save Profile", use_container_width=True)

        if save:
            try:
                from smartdb.crud_ext import update_user_profile
                updated = update_user_profile(
                    user_id,
                    student_id=new_student_id.strip(),
                    department=new_department.strip(),
                    course=new_course.strip(),
                    phone=new_phone.strip(),
                    email=new_email.strip().lower(),
                )
                if updated:
                    # Update session state email
                    if st.session_state.get("user"):
                        st.session_state["user"]["email"] = new_email.strip().lower()
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Could not update profile. Please try again.")
            except Exception as e:
                st.error(f"Profile update failed: {e}")

    # ── Change Password ───────────────────────────────────────────────────────
    with st.expander("🔒 Change Password", expanded=False):
        with st.form("change_password_form"):
            old_pw  = st.text_input("Current Password",    type="password", key="cp_old")
            new_pw  = st.text_input("New Password",        type="password", key="cp_new")
            conf_pw = st.text_input("Confirm New Password", type="password", key="cp_conf")
            cp_save = st.form_submit_button("🔐 Update Password")
            if cp_save:
                if not old_pw or not new_pw or not conf_pw:
                    st.error("All password fields are required.")
                elif new_pw != conf_pw:
                    st.error("New passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        import hashlib
                        from smartdb.crud import get_user_by_username, update_user_credentials
                        stored = get_user_by_username(username)
                        if stored:
                            old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
                            if stored.password_hash == old_hash:
                                new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
                                update_user_credentials(user_id, email, new_hash)
                                st.success("✅ Password updated successfully!")
                            else:
                                st.error("Current password is incorrect.")
                        else:
                            st.error("User not found.")
                    except Exception as e:
                        st.error(f"Password update failed: {e}")


def _profile_css() -> str:
    return """<style>
.prof-header { padding:14px 0 10px; margin-bottom:1rem; }
.prof-title {
    font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.prof-sub { color:rgba(255,255,255,.4); font-size:.88rem; margin-top:4px; }

.prof-card {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08);
    border-radius:16px; padding:24px 20px; text-align:center;
}
.prof-avatar {
    width:72px; height:72px; border-radius:50%;
    background:linear-gradient(135deg,#3B82F6,#7c3aed);
    font-size:1.8rem; font-weight:800; color:#fff;
    display:flex; align-items:center; justify-content:center;
    margin:0 auto 12px;
}
.prof-username { font-size:1.2rem; font-weight:700; color:#fff; }
.prof-role {
    display:inline-block; background:rgba(0,217,255,.12);
    border:1px solid rgba(0,217,255,.25); border-radius:14px;
    padding:2px 12px; font-size:.72rem; color:#3B82F6;
    font-weight:700; margin:6px 0 14px;
}
.prof-detail-row {
    display:flex; align-items:center; gap:8px;
    text-align:left; padding:6px 0;
    border-bottom:1px solid rgba(255,255,255,.04);
}
.prof-detail-icon { font-size:.9rem; flex-shrink:0; }
.prof-detail-val  { font-size:.82rem; color:rgba(255,255,255,.7); }

.prof-section-title {
    font-size:.95rem; font-weight:700; color:rgba(255,255,255,.7);
    text-transform:uppercase; letter-spacing:.5px; margin:1.4rem 0 8px;
}

.prof-stat-card {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:14px 10px; text-align:center; margin-bottom:8px;
}
.psc-icon  { font-size:1.3rem; }
.psc-val   { font-size:1.2rem; font-weight:800; margin:4px 0; }
.psc-label { font-size:.67rem; color:rgba(255,255,255,.4);
             text-transform:uppercase; letter-spacing:.4px; }
</style>"""
