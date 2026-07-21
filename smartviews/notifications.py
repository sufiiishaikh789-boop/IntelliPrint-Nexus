"""
SmartPrint AI - Notifications Page
User notifications with read/unread styling, mark-as-read, and empty state.
"""

import streamlit as st


import re

def _clean_html(html: str) -> str:
    """Clean indentations, comments, and newlines that confuse streamlit's markdown parser."""
    # Remove HTML comments to prevent markdown parser from falling back to text/code block
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())

from smartdb.crud import get_user_notifications, mark_notification_read


def show_notifications():
    """Render the notifications page."""

    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_clean_html(_notif_css()))

    st.markdown(_clean_html("""
        <div class="notif-header">
            <div class="notif-icon">🔔</div>
            <div class="notif-title">Notifications</div>
            <div class="notif-subtitle">Stay updated on your print jobs</div>
        </div>
        """),
        unsafe_allow_html=True,)

    # ── Fetch notifications ──────────────────────────────────────────────
    notifications = []
    try:
        notifications = get_user_notifications(user_id) or []
    except Exception:
        pass

    unread_count = sum(1 for n in notifications if not n.get("is_read", False))

    if unread_count > 0:
        st.markdown(_clean_html(f'<div class="unread-badge">{unread_count} unread notification(s)</div>'),
            unsafe_allow_html=True,)

    # ── Empty state ──────────────────────────────────────────────────────
    if not notifications:
        st.markdown(_clean_html("""
            <div class="empty-notif">
                <div style="font-size:4rem;margin-bottom:16px;">🔕</div>
                <div style="font-size:1.2rem;font-weight:700;color:rgba(255,255,255,0.7);">
                    No Notifications
                </div>
                <div style="font-size:0.88rem;color:rgba(255,255,255,0.35);margin-top:6px;">
                    You're all caught up! Notifications about your print jobs will appear here.
                </div>
            </div>
            """),
            unsafe_allow_html=True,)
        return

    # ── Mark all as read button ──────────────────────────────────────────
    if unread_count > 0:
        if st.button("✅  Mark All as Read", key="mark_all_read"):
            for notif in notifications:
                if not notif.get("is_read", False):
                    try:
                        mark_notification_read(notif.get("id"))
                    except Exception:
                        pass
            st.success("All notifications marked as read!")
            st.rerun()

    # ── Notification list ────────────────────────────────────────────────
    for idx, notif in enumerate(notifications):
        is_read = notif.get("is_read", False)
        card_class = "notif-card-read" if is_read else "notif-card-unread"
        notif_type = notif.get("type", "info")
        type_icon = _type_icon(notif_type)
        title = notif.get("title", "Notification")
        message = notif.get("message", "")
        created_at = notif.get("created_at", "")[:16]

        st.markdown(_clean_html(f"""
            <div class="notif-card {card_class}">
                <div class="nc-left">
                    <div class="nc-icon">{type_icon}</div>
                </div>
                <div class="nc-body">
                    <div class="nc-title">{title}</div>
                    <div class="nc-message">{message}</div>
                    <div class="nc-time">{created_at}</div>
                </div>
                <div class="nc-dot {'nc-dot-unread' if not is_read else ''}"></div>
            </div>
            """),
            unsafe_allow_html=True,)

        if not is_read:
            if st.button(
                f"Mark as Read",
                key=f"mark_read_{notif.get('id', idx)}",
                use_container_width=False,
            ):
                try:
                    mark_notification_read(notif.get("id"))
                except Exception:
                    pass
                st.rerun()


def _type_icon(notif_type: str) -> str:
    return {
        "success": "✅",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "print": "🖨️",
        "payment": "💳",
    }.get(notif_type, "🔔")


# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════
def _notif_css() -> str:
    return """
    <style>
    .notif-header { text-align: center; padding: 20px 0 10px; }
    .notif-icon { font-size: 3rem; margin-bottom: 8px; }
    .notif-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #00F5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .notif-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }

    .unread-badge {
        background: rgba(239,68,68,0.15);
        color: #ef4444;
        padding: 8px 18px;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: center;
        margin: 12px 0;
    }

    .empty-notif {
        text-align: center;
        padding: 60px 20px;
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(255,255,255,0.1);
        border-radius: 16px;
        margin: 24px 0;
    }

    .notif-card {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 18px 20px;
        border-radius: 14px;
        margin-bottom: 10px;
        transition: transform 0.2s ease, background 0.2s ease;
        position: relative;
    }
    .notif-card:hover { transform: translateX(4px); }

    .notif-card-unread {
        background: rgba(0,217,255,0.06);
        border: 1px solid rgba(0,217,255,0.15);
    }
    .notif-card-read {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
    }

    .nc-left { flex-shrink: 0; }
    .nc-icon { font-size: 1.6rem; }
    .nc-body { flex: 1; }
    .nc-title { font-weight: 700; color: #fff; font-size: 0.95rem; margin-bottom: 4px; }
    .nc-message { color: rgba(255,255,255,0.55); font-size: 0.85rem; line-height: 1.5; }
    .nc-time { color: rgba(255,255,255,0.3); font-size: 0.75rem; margin-top: 6px; }
    .nc-dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
        margin-top: 6px;
    }
    .nc-dot-unread {
        background: #00D9FF;
        box-shadow: 0 0 8px rgba(0,217,255,0.5);
    }
    </style>
    """
