"""
SmartPrint AI - Registration Page
Clean registration form with validation and user creation.
"""

import streamlit as st
import re


def _clean_html(html: str) -> str:
    """Clean indentations, comments, and newlines that confuse streamlit's markdown parser."""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


from smartauth.security import register_new_user


def show_register():
    """Render the registration page."""

    st.html(_clean_html(_register_css()))

    col_l, col_c, col_r = st.columns([1, 2.5, 1])
    with col_c:
        st.markdown(_clean_html("""
            <div class="reg-header">
                <div class="reg-icon">✨</div>
                <div class="reg-title">Create Your Account</div>
                <div class="reg-subtitle">Join SmartPrint AI and start printing smarter</div>
            </div>
            """),
            unsafe_allow_html=True,)

        with st.form("register_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="reg_username_field"
            )
            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="reg_email_field"
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a password",
                    key="reg_password_field"
                )
            with col_p2:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter password",
                    key="reg_confirm_password_field"
                )
            role = st.selectbox(
                "Role",
                options=["Student", "Faculty", "Admin"],
                index=0,
                help="Select your role in the institution.",
                key="reg_role_field"
            )
            submitted = st.form_submit_button(
                "🚀  Create Account", use_container_width=True
            )

        if submitted:
            # ── Validation ───────────────────────────────────────────────
            if not all([username, email, password, confirm_password]):
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
            else:
                reg_res = register_new_user(username, email, password, role)
                if reg_res and reg_res.get("success"):
                    st.success(
                        "🎉 Account created successfully! You can now sign in."
                    )
                    st.balloons()
                else:
                    msg = reg_res.get("message", "Registration failed. Username or email may already exist.") if reg_res else "Registration failed."
                    st.error(msg)

        # ── Links ────────────────────────────────────────────────────────
        st.markdown(_clean_html("<br>"), unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        with lc1:
            if st.button("🔑  Already have an account? Login", key="reg_go_login", use_container_width=True):
                st.session_state["current_page"] = "login"
                st.rerun()
        with lc2:
            if st.button("🏠  Back to Home", key="reg_go_home", use_container_width=True):
                st.session_state["current_page"] = "landing"
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════
def _register_css() -> str:
    return """
    <style>
    /* ── Force dark background for register page ──────────────── */
    .stApp, .stApp > div, section.main, section.main > div,
    .block-container, html, body, [class*="css"] {
        background-color: #0a0a12 !important;
        color: #ffffff !important;
    }

    .reg-header {
        text-align: center;
        padding: 30px 0 10px;
    }
    .reg-icon { font-size: 3rem; margin-bottom: 10px; }
    .reg-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #7CFF00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .reg-subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 0.95rem;
        margin-bottom: 10px;
    }

    /* ── Dark theme for ALL input fields on register page ── */
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] > div {
        background-color: rgba(10, 20, 20, 0.95) !important;
        border: 1px solid rgba(0, 217, 255, 0.35) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }

    div[data-baseweb="input"] > div:hover,
    div[data-baseweb="base-input"] > div:hover {
        border-color: rgba(0, 217, 255, 0.65) !important;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="base-input"] > div:focus-within {
        border-color: #00D9FF !important;
        box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.2) !important;
    }

    /* Text inside input */
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {
        background-color: transparent !important;
        color: #ffffff !important;
        caret-color: #00F5FF !important;
    }

    /* Placeholder text */
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder {
        color: rgba(255, 255, 255, 0.35) !important;
    }

    /* Password eye/toggle icon */
    div[data-baseweb="input"] button,
    div[data-baseweb="base-input"] button {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.7) !important;
        border: none !important;
    }
    div[data-baseweb="input"] button:hover,
    div[data-baseweb="base-input"] button:hover {
        color: #00D9FF !important;
    }

    /* ── Dark theme for selectbox ── */
    div[data-baseweb="select"] > div {
        background-color: rgba(10, 20, 20, 0.95) !important;
        border: 1px solid rgba(0, 217, 255, 0.35) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: rgba(0, 217, 255, 0.65) !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] {
        background-color: rgba(10, 20, 20, 0.98) !important;
        border: 1px solid rgba(0, 217, 255, 0.35) !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="menu"] li {
        color: rgba(255,255,255,0.85) !important;
    }
    div[data-baseweb="menu"] li:hover {
        background-color: rgba(0, 217, 255, 0.18) !important;
    }

    /* Input label */
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stForm"] label {
        color: rgba(255, 255, 255, 0.75) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }

    /* ── Form submit button ── */
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"],
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #00D9FF, #7CFF00) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(0, 217, 255, 0.35) !important;
    }
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"] p,
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"] span,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] p,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(0, 217, 255, 0.5) !important;
        color: #000000 !important;
    }
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover p,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover p {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* ── Navigation buttons ── */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: rgba(0, 217, 255, 0.10) !important;
        color: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(0, 217, 255, 0.30) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        background: rgba(0, 217, 255, 0.20) !important;
        border-color: rgba(0, 217, 255, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """
