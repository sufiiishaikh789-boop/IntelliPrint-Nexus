"""
SmartPrint AI - Global Dark Theme CSS
Premium dark UI with glassmorphism, deep dark backgrounds, and Cyberpunk Green + Electric Blue accents.
"""

import streamlit as st


def inject_premium_css() -> None:
    """Inject the complete premium dark-theme stylesheet into the Streamlit app."""
    st.html(_CSS)


_CSS = """
<style>
/* =================================================================
   0. Google Fonts — Inter
   ================================================================= */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* =================================================================
   1. Root Variables — Cyberpunk Green + Electric Blue Theme
   ================================================================= */
:root {
    --primary:        #00D9FF;
    --primary-light:  #00F5FF;
    --primary-dark:   #00B7FF;
    --secondary:      #7CFF00;
    --accent:         #10b981;

    --bg-main:        #050505;
    --bg-card:        #0C1212;
    --bg-panel:       #0A0F12;
    --bg-input:       #0d1a1a;

    --text-main:      #FFFFFF;
    --text-muted:     #A0AEC0;
    --text-dim:       #64748b;

    --border-color:   rgba(255,255,255,0.08);
    --border-active:  rgba(0,217,255,0.50);

    --success: #10b981;
    --warning: #f59e0b;
    --danger:  #ef4444;
    --info:    #00D9FF;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.5);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.6);
    --shadow-xl: 0 20px 50px rgba(0,0,0,0.7);
    --shadow-3d: 0 15px 35px rgba(0,0,0,0.5), 0 5px 15px rgba(0,0,0,0.4);
    --shadow-glow: 0 0 20px rgba(0,217,255,0.25);
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* =================================================================
   2. Global Dark Background — Streamlit 1.59.x comprehensive override
   ================================================================= */

/* ── Core app shells ── */
html,
body,
.stApp,
#root,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="stMainArea"],
.main,
.css-1d391kg,
.css-fg4pbf,
.e1f1d6gn0 {
    background-color: var(--bg-main) !important;
    background: var(--bg-main) !important;
    color: var(--text-main) !important;
}

/* ── Block containers ── */
[data-testid="stMainBlockContainer"],
[data-testid="stBottomBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stHorizontalBlock"],
.block-container,
.appview-container .main .block-container,
[data-testid="column"],
[data-testid="stColumn"] {
    background-color: transparent !important;
}

[data-testid="stMainBlockContainer"],
.block-container,
.appview-container .main .block-container {
    max-width: 1300px !important;
    padding-top: 2rem !important;
    padding-bottom: 90px !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
}

/* ── Dialogs / Modals ── */
[data-testid="stDialog"],
[data-testid="stDialogContent"],
[data-baseweb="dialog"],
[role="dialog"],
div[aria-modal="true"] {
    background-color: var(--bg-panel) !important;
    color: var(--text-main) !important;
}

/* ── Containers & Expanders ── */
[data-testid="stContainer"],
[data-testid="stExpander"] > details,
[data-testid="stExpander"] summary ~ div {
    background-color: transparent !important;
}

/* ── Tab panels ── */
[data-testid="stTabContent"],
[role="tabpanel"] {
    background-color: transparent !important;
}

/* ── Popovers & Tooltips ── */
[data-baseweb="tooltip"],
[data-testid="stTooltipContent"] {
    background-color: var(--bg-panel) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-color) !important;
}

/* ── Forms ── */
[data-testid="stForm"],
[data-testid="stFormSubmitButton"] {
    background-color: transparent !important;
}

/* ── Markdown containers ── */
[data-testid="stMarkdown"],
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"] {
    background-color: transparent !important;
}

/* ── Metric containers ── */
[data-testid="stMetric"],
[data-testid="stMetricContainer"] {
    background-color: transparent !important;
}

/* ── Catch-all: any Streamlit-injected div that defaults white ── */
div[class^="st-"],
div[class*=" st-"] {
    background-color: inherit;
}


/* =================================================================
   3. Hide Streamlit Chrome
   ================================================================= */
header[data-testid="stHeader"]  { display: none !important; height: 0 !important; }
footer[data-testid="stFooter"]  { display: none !important; }
.stDeployButton                 { display: none !important; }
div[data-testid="stToolbar"]    { display: none !important; }
section[data-testid="stSidebar"]{ display: none !important; }

/* =================================================================
   4. Typography
   ================================================================= */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-main) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
}

h1 {
    background: linear-gradient(135deg, #ffffff 30%, #00F5FF 70%, #7CFF00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800 !important;
    margin-bottom: 1rem !important;
}

p, span, label, div {
    color: var(--text-main);
}

/* p gets muted color globally — but NOT inside buttons (overridden below) */
p { color: var(--text-muted) !important; line-height: 1.6; }

/* Prevent global p/span/div rule from bleeding into buttons */
button p, button span, button div,
[data-testid^="stBaseButton"] p,
[data-testid^="stBaseButton"] span,
[data-testid^="stBaseButton"] div {
    line-height: inherit !important;
}

/* =================================================================
   5. Cards & Panels
   ================================================================= */
.glass-card,
.elevated-card,
.admin-welcome,
.admin-metric,
.admin-sub-card,
.activity-row,
.quality-card,
.printer-card,
.wait-panel,
.success-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-md) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.glass-card {
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    padding: 24px !important;
}

.glass-card:hover,
.elevated-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* =================================================================
   6. Inputs & Form Controls
   ================================================================= */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-main) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within > div,
div[data-baseweb="select"]:focus-within > div {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(0,217,255,0.25) !important;
}

input, textarea {
    color: var(--text-main) !important;
    background-color: transparent !important;
}

/* =================================================================
   7. Buttons — background + shape
   ================================================================= */
button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #00D9FF, #7CFF00) !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(0,217,255,0.4) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,217,255,0.55) !important;
    color: #000000 !important;
}

button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
    background: var(--bg-card) !important;
    color: #ffffff !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background: var(--bg-panel) !important;
    border-color: var(--primary) !important;
    transform: translateY(-1px) !important;
    color: #ffffff !important;
}

/* =================================================================
   7b. Button TEXT visibility — fixes `p { color: muted }` bleed-in
   Streamlit renders button labels inside <p> tags. We must
   explicitly override those for every button variant and state.
   ================================================================= */

/* ── PRIMARY / FORM SUBMIT (bright gradient → black text) ── */
button[kind="primary"] p,
button[kind="primary"] span,
button[kind="primary"] div,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primary"] span,
[data-testid="stBaseButton-primary"] div,
button[kind="primaryFormSubmit"] p,
button[kind="primaryFormSubmit"] span,
button[kind="secondaryFormSubmit"] p,
button[kind="secondaryFormSubmit"] span,
div[data-testid="stForm"] button p,
div[data-testid="stForm"] button span {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

button[kind="primary"]:hover p,
button[kind="primary"]:hover span,
button[kind="primary"]:hover div,
[data-testid="stBaseButton-primary"]:hover p,
[data-testid="stBaseButton-primary"]:hover span,
button[kind="primaryFormSubmit"]:hover p,
button[kind="secondaryFormSubmit"]:hover p,
div[data-testid="stForm"] button:hover p,
div[data-testid="stForm"] button:hover span {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

button[kind="primary"]:active p,
button[kind="primary"]:focus p,
[data-testid="stBaseButton-primary"]:active p,
[data-testid="stBaseButton-primary"]:focus p {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* ── SECONDARY / NAV (dark glass → white text) ── */
button[kind="secondary"] p,
button[kind="secondary"] span,
button[kind="secondary"] div,
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondary"] span,
[data-testid="stBaseButton-secondary"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

button[kind="secondary"]:hover p,
button[kind="secondary"]:hover span,
[data-testid="stBaseButton-secondary"]:hover p,
[data-testid="stBaseButton-secondary"]:hover span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

button[kind="secondary"]:active p,
button[kind="secondary"]:focus p,
[data-testid="stBaseButton-secondary"]:active p,
[data-testid="stBaseButton-secondary"]:focus p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* ── TABS (use muted white, active = cyan) ── */
button[data-testid="stTab"] p,
button[data-testid="stTab"] span,
button[data-testid="stTab"] div {
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
}

/* ── DISABLED state (accessible dim) ── */
button:disabled p,
button:disabled span,
button[disabled] p,
button[disabled] span {
    opacity: 0.5 !important;
}

/* =================================================================
   8. Data Tables / DataFrames
   ================================================================= */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
}

.stDataFrame [data-testid="stTable"] th {
    background-color: var(--bg-panel) !important;
    color: var(--text-main) !important;
    font-weight: 600 !important;
    border-bottom: 1px solid var(--border-color) !important;
}

.stDataFrame [data-testid="stTable"] td {
    color: var(--text-muted) !important;
    border-bottom: 1px solid var(--border-color) !important;
    background-color: var(--bg-card) !important;
}

/* =================================================================
   9. Metrics
   ================================================================= */
[data-testid="stMetricValue"] {
    color: var(--primary-light) !important;
    font-weight: 800 !important;
    font-size: 2.2rem !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.8rem !important;
}

[data-testid="stMetricDelta"] {
    color: var(--accent) !important;
}

/* =================================================================
   10. Selectbox / Dropdown
   ================================================================= */
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label,
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label,
[data-testid="stSlider"] label {
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

[data-baseweb="popover"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
}

[data-baseweb="menu"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
}

[role="option"] {
    color: var(--text-main) !important;
    background: transparent !important;
}

[role="option"]:hover {
    background: rgba(0,217,255,0.15) !important;
}

/* =================================================================
   11. Alerts / Info Boxes
   ================================================================= */
[data-testid="stAlert"],
.stAlert {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: var(--text-main) !important;
}

[data-testid="stInfo"] {
    background: rgba(0,217,255,0.10) !important;
    border-color: rgba(0,217,255,0.28) !important;
}

[data-testid="stSuccess"] {
    background: rgba(16,185,129,0.12) !important;
    border-color: rgba(16,185,129,0.30) !important;
}

[data-testid="stWarning"] {
    background: rgba(245,158,11,0.12) !important;
    border-color: rgba(245,158,11,0.30) !important;
}

[data-testid="stError"] {
    background: rgba(239,68,68,0.12) !important;
    border-color: rgba(239,68,68,0.30) !important;
}

/* =================================================================
   12. Progress Bar / Spinner
   ================================================================= */
[data-testid="stProgressBar"] > div {
    background: var(--bg-card) !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #00D9FF, #7CFF00) !important;
}

/* =================================================================
   13. Expander
   ================================================================= */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-main) !important;
}

/* =================================================================
   14. Tabs
   ================================================================= */
[data-testid="stTabs"] {
    background: transparent !important;
}

button[data-testid="stTab"] {
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
    font-weight: 500 !important;
}

button[data-testid="stTab"][aria-selected="true"] {
    color: var(--primary-light) !important;
    border-bottom: 2px solid var(--primary) !important;
}

/* =================================================================
   15. Scrollbar
   ================================================================= */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-main); }
::-webkit-scrollbar-thumb {
    background: rgba(0,217,255,0.25);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(0,217,255,0.45); }

/* =================================================================
   16. Page-specific class overrides (dashboard custom HTML elements)
   ================================================================= */
.section-title,
.admin-greeting, .admin-name,
.gpu-stat-label, .gpu-stat-value,
.am-label, .am-value, .am-icon,
.act-id, .act-user, .act-doc, .act-time,
.ai-title, .upload-title, .p-name-label,
.qc-filename, .qc-score-num, .pm-val {
    color: var(--text-main) !important;
}

.admin-user-info, .admin-date,
.ai-subtitle, .upload-subtitle,
.p-loc-label, .pm-lbl,
.qc-meta, .qc-rec, .qc-sug, .qc-model, .qc-conf,
.am-label {
    color: var(--text-muted) !important;
}

.pm-val { font-weight: 700 !important; }

/* Legacy nav dock selectors (kept for CSS specificity safety) */
#smart-nav-dock {
    display: none !important;
}

/* =================================================================
   17. Mobile Responsive Overrides
   ================================================================= */

/* Tablet (≤ 900px) — tighten side padding */
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"],
    .block-container,
    .appview-container .main .block-container {
        padding-left:  1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top:   1.5rem !important;
    }
}

/* Mobile (≤ 600px) — minimal side padding, compact layout */
@media (max-width: 600px) {
    [data-testid="stMainBlockContainer"],
    .block-container,
    .appview-container .main .block-container {
        padding-left:   0.75rem !important;
        padding-right:  0.75rem !important;
        padding-top:    1rem   !important;
        padding-bottom: 80px   !important;
    }

    /* Scale headings down */
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; }

    /* Metric values — smaller on phone */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }

    /* Cards — remove hover lift on touch screens */
    .glass-card:hover,
    .elevated-card:hover {
        transform: none !important;
    }

    /* Buttons — full-width feel on mobile */
    button[kind="primary"],
    [data-testid="stBaseButton-primary"],
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        padding: 10px 16px !important;
        font-size: 0.9rem !important;
    }

    /* Expander — readable on small screens */
    [data-testid="stExpander"] summary {
        font-size: 0.9rem !important;
    }
}

/* Very small phones (≤ 390px) */
@media (max-width: 390px) {
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-left:  0.5rem !important;
        padding-right: 0.5rem !important;
    }

    h1 { font-size: 1.35rem !important; }

    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
    }
}

</style>
"""
