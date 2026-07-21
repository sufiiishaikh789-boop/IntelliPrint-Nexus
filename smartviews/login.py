"""
SmartPrint AI - Login Page
Clean, glassmorphism login form with authentication integration.
"""

import streamlit as st
import re


def _clean_html(html: str) -> str:
    """Clean indentations, comments, and newlines that confuse streamlit's markdown parser."""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


from smartauth.security import authenticate_user
from smartauth.session import login_session


def show_login():
    """Render the login page."""

    st.html(_clean_html(_login_css()))

    # ── Centered card ────────────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1.2, 2, 1.2])
    with col_c:
        st.markdown(_clean_html("""
            <div class="login-header">
                <div class="login-icon">🔐</div>
                <div class="login-title">Welcome Back</div>
                <div class="login-subtitle">Sign in to continue to SmartPrint AI</div>
            </div>
            """),
            unsafe_allow_html=True,)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username_field"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password_field"
            )
            submitted = st.form_submit_button(
                "🔑  Sign In", use_container_width=True
            )

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                auth_res = authenticate_user(username, password)
                if auth_res and auth_res.get("success"):
                    login_session(auth_res.get("user"))
                    st.success("Login successful! Redirecting…")
                    st.rerun()
                else:
                    msg = auth_res.get("message", "Invalid username or password.") if auth_res else "Invalid username or password."
                    st.error(msg)

        # ── Links ────────────────────────────────────────────────────────
        st.markdown(_clean_html("<br>"), unsafe_allow_html=True)
        link_col1, link_col2 = st.columns(2)
        with link_col1:
            if st.button("📝  Create Account", key="login_go_register", use_container_width=True):
                st.session_state["current_page"] = "register"
                st.rerun()
        with link_col2:
            if st.button("🏠  Back to Home", key="login_go_home", use_container_width=True):
                st.session_state["current_page"] = "landing"
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════
def _login_css() -> str:
    return """
    <style>
    /* ── Force dark background for login page ──────────────────── */
    .stApp, .stApp > div, section.main, section.main > div,
    .block-container, html, body, [class*="css"] {
        background-color: #0a0a12 !important;
        color: #ffffff !important;
    }

    .login-header {
        text-align: center;
        padding: 30px 0 10px;
    }
    .login-icon {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    .login-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #7CFF00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .login-subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 0.95rem;
        margin-bottom: 10px;
    }

    /* ── Dark theme for ALL input fields on login page ── */
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

    /* Input label */
    div[data-testid="stTextInput"] label,
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
