"""
IntelliPrint Nexus - Enhanced Notifications (Phase 3)
Grouped by date, colour-coded by type, unread highlights, mark-all-read.
"""

import streamlit as st
from datetime import datetime, date

from smartdb.crud import get_user_notifications


_TYPE_CONFIG = {
    "success": {"icon": "✅", "color": "#10b981", "bg": "rgba(16,185,129,.08)", "border": "rgba(16,185,129,.2)"},
    "warning": {"icon": "⚠️", "color": "#f59e0b", "bg": "rgba(245,158,11,.08)",  "border": "rgba(245,158,11,.2)"},
    "error":   {"icon": "❌", "color": "#ef4444", "bg": "rgba(239,68,68,.08)",   "border": "rgba(239,68,68,.2)"},
    "info":    {"icon": "ℹ️", "color": "#3b82f6", "bg": "rgba(59,130,246,.08)",  "border": "rgba(59,130,246,.2)"},
}
_DEFAULT_CFG = {"icon": "🔔", "color": "#6b7280", "bg": "rgba(107,114,128,.06)", "border": "rgba(107,114,128,.15)"}

_EVENT_ICONS = {
    "upload":     ("✅", "success"),
    "ai":         ("🤖", "info"),
    "payment":    ("💳", "success"),
    "queue":      ("📋", "info"),
    "printing":   ("🖨️", "info"),
    "50%":        ("📊", "info"),
    "completed":  ("✅", "success"),
    "ready":      ("📦", "success"),
    "pickup":     ("📦", "success"),
    "collected":  ("🎉", "success"),
    "cancelled":  ("❌", "warning"),
    "failed":     ("⚠️", "error"),
}


def _guess_type(title: str, stored_type: str) -> str:
    """Determine notification type from stored type or title keywords."""
    if stored_type and stored_type in _TYPE_CONFIG:
        return stored_type
    title_l = title.lower()
    for kw, (_, t) in _EVENT_ICONS.items():
        if kw in title_l:
            return t
    return "info"


def show_notifications():
    """Render the enhanced notification center."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_notif_css())

    # ── Header ────────────────────────────────────────────────────────────────
    st.html("""
    <div class="notif-header">
        <div class="notif-title">🔔 Notification Center</div>
        <div class="notif-sub">Stay updated on all your print job events</div>
    </div>
    """)

    # ── Fetch notifications ───────────────────────────────────────────────────
    notifs = []
    try:
        notifs = get_user_notifications(user_id) or []
    except Exception as e:
        st.error(f"Could not load notifications: {e}")
        return

    unread_count = sum(1 for n in notifs if not n.get("is_read"))

    # ── Controls ──────────────────────────────────────────────────────────────
    hc1, hc2, hc3 = st.columns([2, 1, 1])
    with hc1:
        if unread_count:
            st.html(f"""
            <div class="notif-unread-badge">
                🔴 {unread_count} unread notification{"s" if unread_count != 1 else ""}
            </div>
            """)
    with hc2:
        if st.button("✅ Mark All Read", key="notif_mark_all", use_container_width=True):
            try:
                from smartdb.crud_ext import mark_all_notifications_read
                count = mark_all_notifications_read(user_id)
                st.success(f"{count} notification(s) marked as read.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with hc3:
        if st.button("🔄 Refresh", key="notif_refresh", use_container_width=True):
            st.rerun()

    if not notifs:
        st.html("""
        <div class="notif-empty">
            <div style="font-size:3rem;">📭</div>
            <div class="notif-empty-title">No Notifications</div>
            <div class="notif-empty-sub">You're all caught up! Notifications appear here after printing events.</div>
        </div>
        """)
        return

    # ── Filter tabs ───────────────────────────────────────────────────────────
    tab_all, tab_unread, tab_success, tab_warning = st.tabs([
        f"📬 All ({len(notifs)})",
        f"🔴 Unread ({unread_count})",
        "✅ Success",
        "⚠️ Alerts",
    ])

    def _render_notif_list(items):
        if not items:
            st.html('<div class="notif-empty-sub" style="padding:16px;">Nothing here yet.</div>')
            return

        # Group by date
        groups: dict = {}
        for n in items:
            ts = n.get("created_at")
            try:
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", ""))
                elif ts:
                    dt = ts
                else:
                    dt = None
            except Exception:
                dt = None

            if dt:
                d = dt.date()
                today   = datetime.utcnow().date()
                yest    = date.fromordinal(today.toordinal() - 1)
                if d == today:
                    grp = "Today"
                elif d == yest:
                    grp = "Yesterday"
                else:
                    grp = dt.strftime("%B %d, %Y")
            else:
                grp = "Earlier"
            groups.setdefault(grp, []).append((n, dt))

        order = ["Today", "Yesterday"]
        keys  = order + [k for k in groups if k not in order]

        for grp in keys:
            if grp not in groups:
                continue
            st.html(f'<div class="notif-date-group">{grp}</div>')
            for n, dt in groups[grp]:
                ntype = _guess_type(n.get("title", ""), n.get("notification_type", ""))
                cfg   = _TYPE_CONFIG.get(ntype, _DEFAULT_CFG)
                is_unread = not n.get("is_read", True)
                time_str = dt.strftime("%H:%M") if dt else "—"

                st.html(f"""
                <div class="notif-card {'notif-unread' if is_unread else ''}"
                     style="background:{cfg['bg']};border-color:{cfg['border']};">
                    <div class="notif-card-icon" style="color:{cfg['color']};">{cfg['icon']}</div>
                    <div class="notif-card-body">
                        <div class="notif-card-title" style="color:{'#fff' if is_unread else 'rgba(255,255,255,.8)'};">
                            {n.get('title', 'Notification')}
                            {'<span class="notif-new-dot"></span>' if is_unread else ''}
                        </div>
                        <div class="notif-card-msg">{n.get('message', '')}</div>
                    </div>
                    <div class="notif-card-time">{time_str}</div>
                </div>
                """)

    with tab_all:
        _render_notif_list(notifs)
    with tab_unread:
        _render_notif_list([n for n in notifs if not n.get("is_read")])
    with tab_success:
        _render_notif_list([n for n in notifs
                            if _guess_type(n.get("title", ""), n.get("notification_type", "")) == "success"])
    with tab_warning:
        _render_notif_list([n for n in notifs
                            if _guess_type(n.get("title", ""), n.get("notification_type", "")) in ("warning", "error")])


def _notif_css() -> str:
    return """<style>
.notif-header { padding:14px 0 10px; margin-bottom:1rem; }
.notif-title {
    font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.notif-sub { color:rgba(255,255,255,.4); font-size:.88rem; margin-top:4px; }

.notif-unread-badge {
    display:inline-block;
    background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.25);
    border-radius:20px; padding:6px 14px;
    font-size:.8rem; color:#fca5a5; font-weight:600;
}

.notif-date-group {
    font-size:.72rem; font-weight:700; color:rgba(255,255,255,.4);
    text-transform:uppercase; letter-spacing:.6px;
    margin:14px 0 6px; padding-bottom:4px;
    border-bottom:1px solid rgba(255,255,255,.06);
}

.notif-card {
    display:flex; align-items:flex-start; gap:12px;
    padding:12px 14px; border-radius:12px;
    border:1px solid rgba(255,255,255,.08);
    margin-bottom:6px; transition:background .2s;
}
.notif-unread { box-shadow:0 0 0 1px rgba(0,217,255,.2); }
.notif-card-icon { font-size:1.3rem; flex-shrink:0; margin-top:2px; }
.notif-card-body { flex:1; }
.notif-card-title { font-size:.88rem; font-weight:600; position:relative; display:inline-block; }
.notif-card-msg { font-size:.8rem; color:rgba(255,255,255,.5); margin-top:3px; line-height:1.4; }
.notif-card-time { font-size:.72rem; color:rgba(255,255,255,.3); white-space:nowrap; margin-top:2px; }

.notif-new-dot {
    display:inline-block; width:7px; height:7px;
    background:#ef4444; border-radius:50%;
    margin-left:6px; vertical-align:middle;
}

.notif-empty {
    text-align:center; padding:60px 20px;
    background:rgba(255,255,255,.02); border:1px dashed rgba(255,255,255,.08);
    border-radius:16px; margin:20px 0;
}
.notif-empty-title { font-size:1.1rem; font-weight:700; color:rgba(255,255,255,.6); margin:10px 0 6px; }
.notif-empty-sub   { font-size:.85rem; color:rgba(255,255,255,.35); }
</style>"""
