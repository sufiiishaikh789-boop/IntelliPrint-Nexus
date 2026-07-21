import streamlit as st

# ═══════════════════════════════════════════════════════════════
# SMARTPRINT AI - Main Application Entry Point
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SmartPrint AI — Intelligent Printing System",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "mailto:support@smartprint.edu",
        "About": "SmartPrint AI v2.0 — AI-Powered University Printing Platform",
    },
)

# ─── Initialize Database ─────────────────────────────────────
from smartdb.models import init_db
from smartdb.crud import seed_printers

@st.cache_resource
def _bootstrap_database():
    init_db()
    seed_printers()
    return True

_bootstrap_database()

# ─── Session & Styles ────────────────────────────────────────
from smartauth.session import init_session
from smartutils.styles import inject_premium_css
from smartutils.navigation import render_dock, render_floating_chat
from smartutils.queue_manager import start_queue_manager_thread

init_session()
inject_premium_css()
start_queue_manager_thread()


# ─── Import Views ────────────────────────────────────────────
def _safe_import(module_path, func_name):
    """Safely import a view function, returning a placeholder if not yet available."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, func_name)
    except (ImportError, AttributeError) as e:
        def _placeholder():
            st.info(f"🚧 This page is being built. Please refresh in a moment.")
        return _placeholder

from smartviews.landing import show_landing
from smartviews.login import show_login
from smartviews.register import show_register

show_student_dashboard = _safe_import("smartviews.student_dashboard", "show_student_dashboard")
show_upload = _safe_import("smartviews.upload", "show_upload")
show_queue_tracking = _safe_import("smartviews.queue_tracking", "show_queue_tracking")
show_print_history = _safe_import("smartviews.print_history", "show_print_history")
show_notifications = _safe_import("smartviews.notifications", "show_notifications")
show_profile = _safe_import("smartviews.profile", "show_profile")
show_settings = _safe_import("smartviews.settings", "show_settings")
show_payment = _safe_import("smartviews.payment", "show_payment")
show_ai_analysis = _safe_import("smartviews.ai_analysis", "show_ai_analysis")
show_ai_assistant = _safe_import("smartviews.ai_assistant", "show_ai_assistant")
show_admin_dashboard = _safe_import("smartviews.admin_dashboard", "show_admin_dashboard")
show_admin_queue = _safe_import("smartviews.admin_queue", "show_admin_queue")
show_admin_printers = _safe_import("smartviews.admin_printers", "show_admin_printers")

# ─── Navigation & Utilities ───────────────────────────────────
# We will render the dock and floating chat at the very end of the page rendering


# ─── Page Router ──────────────────────────────────────────────
authenticated = st.session_state.get("authenticated", False)

if "nav_route" in st.query_params:
    st.session_state["current_page"] = st.query_params["nav_route"]
    st.query_params.clear() 

page = st.session_state.get("current_page", "landing")

if not authenticated:
    # Unauthenticated routes
    if page == "register":
        show_register()
    elif page == "login":
        show_login()
    else:
        show_landing()
else:
    # Authenticated routes
    user = st.session_state.get("user", {})
    role = user.get("role", "Student") if user else "Student"

    PAGE_MAP = {
        "Dashboard": show_admin_dashboard if role == "Admin" else show_student_dashboard,
        "Submit Print Job": show_upload,
        "My Print Jobs": show_print_history,
        "Track Order": show_queue_tracking,
        "Payments": show_payment,
        "AI Assistant": show_ai_assistant,
        "AI Analysis": show_ai_analysis,
        "Notifications": show_notifications,
        "Profile": show_profile,
        "Settings": show_settings,
        "Admin Panel": show_admin_dashboard,
        "Queue Management": show_admin_queue,
        "Printer Management": show_admin_printers,
        "User Management": lambda: st.info("👥 User Management coming soon!"),
        "Analytics": lambda: st.info("📈 Analytics coming soon!"),
    }

    handler = PAGE_MAP.get(page, show_student_dashboard)
    handler()
    
    # Render Dock & Chat (always rendered on top for authenticated users)
    render_dock()
    render_floating_chat()

