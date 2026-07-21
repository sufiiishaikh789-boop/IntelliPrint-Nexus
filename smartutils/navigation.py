"""
SmartPrint AI - Floating Dock Navigation

Implementation: Real st.button() widgets + explicit st.rerun().

  • Every icon is a REAL Streamlit st.button().
  • Clicking sets st.session_state["current_page"] then calls st.rerun().
  • Zero JavaScript. Zero HTML fake buttons. Zero hidden elements.
  • CSS styles the 11-column stHorizontalBlock as a fixed glass pill
    using the CSS :has() selector (Chrome 105+, Firefox 121+, Safari 15.4+).
"""

import streamlit as st
from smartauth.session import is_admin, logout_session


def navigate_to(page: str) -> None:
    """Update current page in session state."""
    st.session_state["current_page"] = page


# ── Navigation items: (emoji, label, page_key) ───────────────────────────────

_STUDENT_ITEMS = [
    ("🏠",  "Home",      "Dashboard"),
    ("📤",  "Upload",    "Submit Print Job"),
    ("📋",  "Queue",     "Track Order"),
    ("💳",  "Pay",       "Payments"),
    ("🖨️", "Print",     "AI Analysis"),
    ("🤖",  "AI",        "AI Assistant"),
    ("🔔",  "Alerts",    "Notifications"),
    ("📜",  "History",   "My Print Jobs"),
    ("👤",  "Profile",   "Profile"),
    ("⚙️", "Settings",  "Settings"),
    ("🚪",  "Logout",    "__logout__"),
]

_ADMIN_ITEMS = [
    ("🏠",  "Home",      "Dashboard"),
    ("📤",  "Upload",    "Submit Print Job"),
    ("🔧",  "Queue",     "Queue Management"),
    ("🖨️", "Printers",  "Printer Management"),
    ("💳",  "Pay",       "Payments"),
    ("🤖",  "AI",        "AI Assistant"),
    ("🔔",  "Alerts",    "Notifications"),
    ("👤",  "Profile",   "Profile"),
    ("🛠️", "Admin",     "Admin Panel"),
    ("⚙️", "Settings",  "Settings"),
    ("🚪",  "Logout",    "__logout__"),
]

# CSS selector that uniquely targets our 11-column dock row.
# No other part of the app uses st.columns(11).
_DOCK = '[data-testid="stHorizontalBlock"]:has([data-testid="stColumn"]:nth-child(11))'


def _build_dock_css(items: list, current: str) -> str:
    """Return a <style> block that visually styles the dock."""
    n = len(items)

    # 1-based index of the active page (for nth-child CSS)
    active_nth = 1
    for i, (_, _, pk) in enumerate(items):
        if pk == current:
            active_nth = i + 1
            break

    logout_nth = n  # logout is always last

    # Per-item tooltip: one ::before rule per nth-child position
    tips = []
    for i, (_, label, _) in enumerate(items):
        safe = label.replace("'", "\\'")
        nth = i + 1
        tips.append(f"""
{_DOCK} [data-testid="stColumn"]:nth-child({nth}) button::before {{
    content: '{safe}' !important;
    position: absolute !important;
    bottom: calc(100% + 10px) !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    background: rgba(8,8,20,.95) !important;
    color: #e2e8f0 !important;
    font-size: .68rem !important;
    font-weight: 600 !important;
    letter-spacing: .03em !important;
    white-space: nowrap !important;
    padding: 4px 8px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    pointer-events: none !important;
    opacity: 0 !important;
    transition: opacity .18s ease !important;
    z-index: 1000001 !important;
}}
{_DOCK} [data-testid="stColumn"]:nth-child({nth}) button:hover::before {{
    opacity: 1 !important;
}}""")

    tips_css = "\n".join(tips)

    return f"""<style>
/* ═════════════════════════════════════════════════════
   FLOATING DOCK CONTAINER
   Targets stHorizontalBlock with exactly 11 stColumns.
   ═════════════════════════════════════════════════════ */
{_DOCK} {{
    position:        fixed !important;
    bottom:          16px !important;
    left:            50% !important;
    transform:       translateX(-50%) !important;
    z-index:         999999 !important;
    display:         flex !important;
    flex-direction:  row !important;
    align-items:     center !important;
    justify-content: center !important;
    gap:             8px !important;
    padding:         10px 18px !important;
    width:           max-content !important;
    max-width:       calc(100vw - 32px) !important;
    background:      rgba(8,8,20,.88) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border:          1px solid rgba(255,255,255,.10) !important;
    border-radius:   28px !important;
    box-shadow:      0 16px 48px rgba(0,0,0,.65),
                     inset 0 1px 0 rgba(255,255,255,.08) !important;
}}

/* Remove default column flex sizing */
{_DOCK} [data-testid="stColumn"] {{
    width:     auto !important;
    min-width: 0 !important;
    flex:      0 0 auto !important;
    padding:   0 !important;
}}

/* Collapse inner vertical wrappers */
{_DOCK} [data-testid="stVerticalBlock"],
{_DOCK} [data-testid="stVerticalBlockBorderWrapper"] {{
    gap:     0 !important;
    padding: 0 !important;
    min-height: 0 !important;
}}

{_DOCK} [data-testid="stButtonContainer"] {{
    display: flex !important;
    justify-content: center !important;
    padding: 0 !important;
    margin:  0 !important;
    width:   auto !important;
}}

/* ═════════════════════════════════════════════════════
   ICON BUTTONS  – 48 × 48 glass squares
   ═════════════════════════════════════════════════════ */
{_DOCK} button,
{_DOCK} [data-testid="stBaseButton-secondary"] {{
    position:        relative !important;
    width:           48px !important;
    height:          48px !important;
    min-width:       48px !important;
    max-width:       48px !important;
    padding:         0 !important;
    margin:          0 !important;
    background:      rgba(255,255,255,.07) !important;
    border:          1px solid rgba(255,255,255,.10) !important;
    border-radius:   14px !important;
    display:         flex !important;
    align-items:     center !important;
    justify-content: center !important;
    cursor:          pointer !important;
    transition:      all .25s ease !important;
    font-size:       1.35rem !important;
    line-height:     1 !important;
    color:           rgba(255,255,255,.85) !important;
    box-shadow:      none !important;
    overflow:        visible !important;
    flex-shrink:     0 !important;
}}

{_DOCK} button p,
{_DOCK} button span,
{_DOCK} button div {{
    font-size:   1.35rem !important;
    line-height: 1 !important;
    margin:      0 !important;
    padding:     0 !important;
    color:       inherit !important;
}}

/* ═════════════════════════════════════════════════════
   HOVER – purple lift
   ═════════════════════════════════════════════════════ */
{_DOCK} button:hover {{
    background:   rgba(0,217,255,.18) !important;
    border-color: rgba(0,217,255,.60) !important;
    transform:    translateY(-5px) scale(1.10) !important;
    box-shadow:   0 8px 24px rgba(0,217,255,.40) !important;
    color:        #fff !important;
}}

/* ═════════════════════════════════════════════════════
   ACTIVE BUTTON – column {active_nth}
   ═════════════════════════════════════════════════════ */
{_DOCK} [data-testid="stColumn"]:nth-child({active_nth}) button {{
    background:   rgba(0,217,255,.22) !important;
    border-color: rgba(0,217,255,.65) !important;
    transform:    scale(1.08) !important;
    box-shadow:   0 6px 20px rgba(0,217,255,.45) !important;
    color:        #fff !important;
}}

/* Cyan dot under active button */
{_DOCK} [data-testid="stColumn"]:nth-child({active_nth}) button::after {{
    content:       '' !important;
    position:      absolute !important;
    bottom:        -7px !important;
    left:          50% !important;
    transform:     translateX(-50%) !important;
    width:         6px !important;
    height:        6px !important;
    background:    #00D9FF !important;
    border-radius: 50% !important;
    box-shadow:    0 0 6px #00D9FF, 0 0 12px rgba(0,217,255,.4) !important;
    pointer-events: none !important;
}}

/* ═════════════════════════════════════════════════════
   LOGOUT – column {logout_nth} red hover
   ═════════════════════════════════════════════════════ */
{_DOCK} [data-testid="stColumn"]:nth-child({logout_nth}) button:hover {{
    background:   rgba(239,68,68,.25) !important;
    border-color: rgba(239,68,68,.60) !important;
    box-shadow:   0 8px 24px rgba(239,68,68,.40) !important;
}}

/* ═════════════════════════════════════════════════════
   TOOLTIPS – per-column ::before content
   ═════════════════════════════════════════════════════ */
{tips_css}

/* ═════════════════════════════════════════════════════
   CONTENT OFFSET – keep body above the fixed dock
   ═════════════════════════════════════════════════════ */
[data-testid="stMainBlockContainer"],
.block-container,
.appview-container .main .block-container {{
    padding-bottom: 90px !important;
}}

/* ═════════════════════════════════════════════════════
   RESPONSIVE – Tablet (≤ 860px)
   ═════════════════════════════════════════════════════ */
@media (max-width: 860px) {{
    {_DOCK} {{
        gap:     6px !important;
        padding: 8px 14px !important;
    }}
    {_DOCK} button {{
        width:     42px !important;
        height:    42px !important;
        min-width: 42px !important;
        font-size: 1.15rem !important;
    }}
}}

/* ═════════════════════════════════════════════════════
   RESPONSIVE – Mobile (≤ 600px) – scroll strip
   ═════════════════════════════════════════════════════ */
@media (max-width: 600px) {{
    {_DOCK} {{
        left:             10px !important;
        right:            10px !important;
        transform:        none !important;
        width:            calc(100vw - 20px) !important;
        max-width:        calc(100vw - 20px) !important;
        overflow-x:       auto !important;
        -webkit-overflow-scrolling: touch !important;
        scroll-snap-type: x mandatory !important;
        scrollbar-width:  none !important;
        justify-content:  flex-start !important;
        gap:              5px !important;
        padding:          7px 10px !important;
        border-radius:    20px !important;
    }}
    {_DOCK}::-webkit-scrollbar {{ display: none !important; }}
    {_DOCK} button {{
        width:     36px !important;
        height:    36px !important;
        min-width: 36px !important;
        font-size: 1rem !important;
        scroll-snap-align: start !important;
    }}
    {_DOCK} button::before {{ display: none !important; }}
}}

/* ═════════════════════════════════════════════════════
   RESPONSIVE – Very small phones (≤ 390px)
   ═════════════════════════════════════════════════════ */
@media (max-width: 390px) {{
    {_DOCK} {{
        gap: 4px !important;
        padding: 6px 8px !important;
    }}
    {_DOCK} button {{
        width:     30px !important;
        height:    30px !important;
        min-width: 30px !important;
        font-size: .85rem !important;
    }}
}}
</style>"""


def render_dock() -> None:
    """
    Render the floating navigation dock.

    Uses REAL st.button() widgets. Clicking sets session state
    and calls st.rerun() — standard Streamlit navigation pattern.
    No JavaScript. No HTML overlays. No hidden buttons.
    """
    user = st.session_state.get("user")
    if not user:
        return

    admin   = is_admin()
    current = st.session_state.get("current_page", "Dashboard")
    items   = _ADMIN_ITEMS if admin else _STUDENT_ITEMS

    # ── CSS: style the dock container and buttons ────────────────────────────
    st.html(_build_dock_css(items, current))

    # ── Real Streamlit buttons – one per nav item ────────────────────────────
    # Pattern: if st.button(): update session_state → st.rerun()
    cols = st.columns(len(items))
    for idx, (emoji, label, page_key) in enumerate(items):
        with cols[idx]:
            clicked = st.button(
                emoji,
                key=f"__dock_{idx:02d}__",
                type="secondary",
                help=label,
            )
            if clicked:
                if page_key == "__logout__":
                    logout_session()
                else:
                    navigate_to(page_key)
                st.rerun()


def render_floating_chat() -> None:
    """Placeholder – floating chat (future feature)."""
    pass


def render_sidebar() -> None:
    """Placeholder – sidebar nav (unused; dock is primary nav)."""
    pass
