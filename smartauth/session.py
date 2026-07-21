"""
SmartPrint AI - Streamlit Session Management
Manages user sessions: initialisation, login, logout, and auth guards.
"""

from typing import Optional

import streamlit as st


def init_session() -> None:
    """Initialise all required session-state keys with safe defaults."""
    defaults = {
        "authenticated": False,
        "user": None,
        "current_page": "landing",
        "show_login": True,
        "show_register": False,
        "theme": "dark",
        "notifications_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_session(user_data: dict) -> None:
    """Persist user data into session state after successful authentication."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_data
    st.session_state["current_page"] = "Dashboard"
    st.session_state["show_login"] = False
    st.session_state["show_register"] = False


def logout_session() -> None:
    """Clear user data from session state."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["current_page"] = "landing"
    st.session_state["show_login"] = True
    st.session_state["show_register"] = False
    st.session_state["notifications_count"] = 0


def require_auth() -> bool:
    """
    Guard that checks whether the user is authenticated.

    Returns True if authenticated, False otherwise.
    When not authenticated it also displays an error banner.
    """
    if not st.session_state.get("authenticated", False):
        st.error("🔒 Please log in to access this page.")
        return False
    return True


def require_admin() -> bool:
    """
    Guard that checks whether the user is an authenticated Admin.

    Returns True if the user is an Admin, False otherwise.
    When not authorised it also displays an error banner.
    """
    if not require_auth():
        return False

    user = st.session_state.get("user")
    if not user or user.get("role") != "Admin":
        st.error("⛔ You do not have admin privileges to access this page.")
        return False
    return True


def get_current_user() -> Optional[dict]:
    """Return the current user dict from session state, or None."""
    return st.session_state.get("user")


def is_admin() -> bool:
    """Quick check for admin role without displaying errors."""
    user = st.session_state.get("user")
    return bool(user and user.get("role") == "Admin")
