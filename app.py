import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # suppress TF C++ logs
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")  # disable oneDNN noise

import streamlit as st
# ═══════════════════════════════════════════════════════════════
# IntelliPrint Nexus - Main Application Entry Point
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="IntelliPrint Nexus",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "mailto:support@smartprint.edu",
        "About": "IntelliPrint Nexus — AI-Powered Intelligent Printing, Queue Optimization & Printer Management Platform",
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

# ─── Enterprise startup ───────────────────────────────────────────────────
@st.cache_resource
def _bootstrap_enterprise():
    """Start all background services once (idempotent via cache_resource)."""
    try:
        from smartcore.config import ensure_directories
        ensure_directories()
    except Exception:
        pass

    try:
        from smartcore.background_workers import start_all_workers
        start_all_workers()
    except Exception:
        pass

    return True

_bootstrap_enterprise()

from smartauth.session import init_session
from smartutils.styles import inject_premium_css
from smartutils.navigation import render_dock, render_floating_chat

init_session()
inject_premium_css()

# ─── Start queue manager once (cached so it never runs twice) ────────────
@st.cache_resource
def _bootstrap_queue():
    from smartutils.queue_manager import start_queue_manager_thread
    start_queue_manager_thread()
    return True

_bootstrap_queue()


# ─── Lazy view loader ────────────────────────────────────────────────────
def _safe_import(module_path, func_name):
    """Lazily import a view function only when called (not at startup)."""
    def _loader():
        try:
            import importlib
            mod = importlib.import_module(module_path)
            return getattr(mod, func_name)()
        except Exception as _e:
            import traceback
            st.error(
                f"⚠️ **Page failed to load** — `{module_path}.{func_name}`\n\n"
                f"```\n{traceback.format_exc()}\n```"
            )
    return _loader

# ─── Core views (lightweight — loaded immediately) ───────────────────────
from smartviews.landing import show_landing
from smartviews.login import show_login
from smartviews.register import show_register

# ─── All other views are lazy (only imported when the page is visited) ───
show_student_dashboard   = _safe_import("smartviews.student_dashboard",       "show_student_dashboard")
show_upload              = _safe_import("smartviews.upload",                   "show_upload")
show_queue_tracking      = _safe_import("smartviews.queue_tracking",           "show_queue_tracking")
show_print_history       = _safe_import("smartviews.print_history",            "show_print_history")
show_notifications       = _safe_import("smartviews.notifications",            "show_notifications")
show_profile             = _safe_import("smartviews.profile",                  "show_profile")
show_settings            = _safe_import("smartviews.settings",                 "show_settings")
show_payment             = _safe_import("smartviews.payment",                  "show_payment")
show_ai_analysis         = _safe_import("smartviews.ai_analysis",              "show_ai_analysis")
show_ai_assistant        = _safe_import("smartviews.ai_assistant",             "show_ai_assistant")
show_admin_dashboard     = _safe_import("smartviews.admin_dashboard",          "show_admin_dashboard")
show_admin_queue         = _safe_import("smartviews.admin_queue",              "show_admin_queue")
show_admin_printers      = _safe_import("smartviews.admin_printers",           "show_admin_printers")
show_print_jobs          = _safe_import("smartviews.admin_print_jobs",         "show_print_jobs")
show_admin_payment_mgmt  = _safe_import("smartviews.admin_payment_mgmt",       "show_admin_payment_mgmt")
show_student_management  = _safe_import("smartviews.admin_student_management", "show_student_management")
show_ai_alerts           = _safe_import("smartviews.admin_ai_alerts",          "show_ai_alerts")
show_reports             = _safe_import("smartviews.admin_reports",            "show_reports")
show_admin_digital_twin  = _safe_import("smartviews.admin_digital_twin",       "show_admin_digital_twin")
show_admin_activity      = _safe_import("smartviews.admin_activity",           "show_admin_activity")
show_student_analytics   = _safe_import("smartviews.student_analytics",        "show_student_analytics")
show_support             = _safe_import("smartviews.support",                  "show_support")
show_university_admin    = _safe_import("smartviews.university_admin_dashboard","show_university_admin_dashboard")
show_printer_availability = _safe_import("smartviews.printer_availability",      "show_printer_availability")
show_gpu_monitor          = _safe_import("smartviews.gpu_monitor",                 "show_gpu_monitor")

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

    # Determine Dashboard handler based on role
    if role == "University Admin":
        _dashboard_handler = show_university_admin
    elif role == "Admin":
        _dashboard_handler = show_admin_dashboard
    else:
        _dashboard_handler = show_student_dashboard

    PAGE_MAP = {
        "Dashboard": _dashboard_handler,
        "Submit Print Job": show_upload,
        "My Print Jobs": show_print_history,
        "Track Order": show_queue_tracking,
        "Payments": show_admin_payment_mgmt if role == "Admin" else show_payment,
        "AI Assistant": show_ai_assistant,
        "AI Analysis": show_ai_analysis,
        "Notifications": show_notifications,
        "Profile": show_profile,
        "Settings": show_settings,
        "Admin Panel": show_admin_dashboard,
        "Queue Management": show_admin_queue,
        "Printer Management": show_admin_printers,
        "Print Jobs": show_print_jobs,
        "Student Management": show_student_management,
        "AI Alerts": show_ai_alerts,
        "Reports": show_reports,
        "User Management": lambda: st.info("👥 User Management coming soon!"),
        "Analytics": lambda: st.info("📈 Analytics — check Reports for full analytics."),
        "Digital Twin": show_admin_digital_twin,
        "Activity Log": show_admin_activity,
        "Printer Twin": show_admin_digital_twin,
        "Analytics":    show_student_analytics,
        "Support":      show_support,
        "Printer Availability": show_printer_availability,
        "GPU Monitor":  show_gpu_monitor,
    }

    handler = PAGE_MAP.get(page, show_student_dashboard)
    handler()
    
    # Render Dock & Chat (always rendered on top for authenticated users)
    render_dock()
    render_floating_chat()

