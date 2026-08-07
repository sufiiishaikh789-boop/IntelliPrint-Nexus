"""
IntelliPrint Nexus — Unified Enterprise Design System
Blue/Purple AI palette. Production-grade. University-ready.
"""

import streamlit as st


def inject_premium_css() -> None:
    """Inject the complete enterprise design system stylesheet."""
    st.html(_CSS)


_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════
   0. FONTS
   ═══════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════════════════════════════════
   1. DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════════ */
:root {
  /* ── Brand Colors ── */
  --blue-300:   #93C5FD;
  --blue-400:   #60A5FA;
  --blue-500:   #3B82F6;
  --blue-600:   #2563EB;
  --purple-400: #A78BFA;
  --purple-500: #8B5CF6;
  --purple-600: #7C3AED;
  --cyan-400:   #67E8F9;
  --cyan-500:   #06B6D4;
  --green-400:  #34D399;
  --green-500:  #10B981;
  --amber-400:  #FBBF24;
  --amber-500:  #F59E0B;
  --red-400:    #F87171;
  --red-500:    #EF4444;

  /* ── Semantic Aliases ── */
  --primary:        var(--blue-500);
  --primary-light:  var(--blue-400);
  --primary-dark:   var(--blue-600);
  --primary-glow:   rgba(59,130,246,0.25);
  --accent:         var(--purple-500);
  --accent-light:   var(--purple-400);
  --accent-glow:    rgba(139,92,246,0.22);
  --success:        var(--green-500);
  --success-bg:     rgba(16,185,129,0.10);
  --success-border: rgba(16,185,129,0.28);
  --warning:        var(--amber-500);
  --warning-bg:     rgba(245,158,11,0.10);
  --warning-border: rgba(245,158,11,0.28);
  --danger:         var(--red-500);
  --danger-bg:      rgba(239,68,68,0.10);
  --danger-border:  rgba(239,68,68,0.28);
  --info:           var(--cyan-500);
  --info-bg:        rgba(6,182,212,0.10);
  --info-border:    rgba(6,182,212,0.28);

  /* ── Background Layers ── */
  --bg-base:    #060811;
  --bg-main:    #080B14;
  --bg-card:    #0D1117;
  --bg-panel:   #0A0E18;
  --bg-surface: #111827;
  --bg-input:   #0D1117;
  --bg-hover:   rgba(59,130,246,0.06);

  /* ── Text ── */
  --text-primary: #F8FAFC;
  --text-main:    #F8FAFC;
  --text-secondary:#CBD5E1;
  --text-muted:   #94A3B8;
  --text-dim:     #64748B;
  --text-disabled:#475569;

  /* ── Borders ── */
  --border:        rgba(255,255,255,0.07);
  --border-color:  rgba(255,255,255,0.07);
  --border-subtle: rgba(255,255,255,0.04);
  --border-active: rgba(59,130,246,0.45);
  --border-hover:  rgba(255,255,255,0.14);

  /* ── Shadows ── */
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.4);
  --shadow-sm: 0 2px 6px rgba(0,0,0,0.45);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.5);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.55);
  --shadow-xl: 0 16px 48px rgba(0,0,0,0.6);
  --shadow-2xl:0 24px 64px rgba(0,0,0,0.65);
  --shadow-glow-blue:   0 0 24px rgba(59,130,246,0.3);
  --shadow-glow-purple: 0 0 24px rgba(139,92,246,0.28);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04);

  /* ── Border Radius ── */
  --radius-xs:   4px;
  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;
  --radius-xl:   20px;
  --radius-2xl:  24px;
  --radius-full: 9999px;

  /* ── Spacing ── */
  --space-1: 4px;  --space-2: 8px;   --space-3: 12px;
  --space-4: 16px; --space-5: 20px;  --space-6: 24px;
  --space-7: 28px; --space-8: 32px;  --space-10: 40px;
  --space-12: 48px;--space-16: 64px;

  /* ── Typography ── */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --text-xs:   0.75rem;
  --text-sm:   0.875rem;
  --text-base: 1rem;
  --text-lg:   1.125rem;
  --text-xl:   1.25rem;
  --text-2xl:  1.5rem;
  --text-3xl:  1.875rem;
  --text-4xl:  2.25rem;

  /* ── Animation ── */
  --ease:         cubic-bezier(0.4,0,0.2,1);
  --ease-spring:  cubic-bezier(0.34,1.2,0.64,1);
  --ease-out:     cubic-bezier(0,0,0.2,1);
  --anim-fast:    150ms;
  --anim-base:    250ms;
  --anim-slow:    400ms;

  /* ── Gradients ── */
  --grad-primary:  linear-gradient(135deg, var(--blue-500), var(--purple-500));
  --grad-blue:     linear-gradient(135deg, var(--blue-400), var(--blue-600));
  --grad-purple:   linear-gradient(135deg, var(--purple-400), var(--purple-600));
  --grad-success:  linear-gradient(135deg, var(--green-400), var(--cyan-500));
  --grad-warning:  linear-gradient(135deg, var(--amber-400), var(--red-400));
  --grad-text-h1:  linear-gradient(135deg, #fff 25%, var(--blue-400) 65%, var(--purple-400) 100%);
}

/* ═══════════════════════════════════════════════════════════════════
   2. GLOBAL RESET & BASE
   ═══════════════════════════════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: var(--font-sans) !important;
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
}

/* ── Core app shells ── */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="stMainArea"],
.main, .css-1d391kg, .css-fg4pbf, .e1f1d6gn0 {
  background-color: var(--bg-main) !important;
  background:       var(--bg-main) !important;
  color:            var(--text-main) !important;
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
  max-width:     1340px !important;
  padding-top:   2rem   !important;
  padding-bottom:90px   !important;
  padding-left:  2.5rem !important;
  padding-right: 2.5rem !important;
}

/* ── Dialogs / Modals ── */
[data-testid="stDialog"],
[data-testid="stDialogContent"],
[data-baseweb="dialog"],
[role="dialog"],
div[aria-modal="true"] {
  background-color: var(--bg-panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xl) !important;
  color: var(--text-main) !important;
  box-shadow: var(--shadow-2xl) !important;
}

/* ── Containers & Expanders ── */
[data-testid="stContainer"],
[data-testid="stExpander"] > details,
[data-testid="stExpander"] summary ~ div {
  background-color: transparent !important;
}

/* ── Tab panels ── */
[data-testid="stTabContent"],
[role="tabpanel"] { background-color: transparent !important; }

/* ── Popovers & Tooltips ── */
[data-baseweb="tooltip"],
[data-testid="stTooltipContent"] {
  background-color: var(--bg-surface) !important;
  color: var(--text-main) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-size: var(--text-sm) !important;
}

/* ── Forms ── */
[data-testid="stForm"],
[data-testid="stFormSubmitButton"] { background-color: transparent !important; }

/* ── Markdown containers ── */
[data-testid="stMarkdown"],
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"] { background-color: transparent !important; }

/* ── Metric containers ── */
[data-testid="stMetric"],
[data-testid="stMetricContainer"] { background-color: transparent !important; }

/* ── Catch-all ── */
div[class^="st-"], div[class*=" st-"] { background-color: inherit; }

/* ═══════════════════════════════════════════════════════════════════
   3. HIDE STREAMLIT CHROME
   ═══════════════════════════════════════════════════════════════════ */
header[data-testid="stHeader"]   { display: none !important; height: 0 !important; }
footer[data-testid="stFooter"]   { display: none !important; }
.stDeployButton                  { display: none !important; }
div[data-testid="stToolbar"]     { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
#smart-nav-dock                  { display: none !important; }

/* ═══════════════════════════════════════════════════════════════════
   4. TYPOGRAPHY
   ═══════════════════════════════════════════════════════════════════ */
h1, h2, h3, h4, h5, h6 {
  color:          var(--text-primary) !important;
  letter-spacing: -0.02em !important;
  line-height:    1.2 !important;
}

h1 {
  background:            var(--grad-text-h1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip:       text;
  font-weight: 800 !important;
  font-size:   var(--text-3xl) !important;
  margin-bottom: var(--space-4) !important;
}

h2 { font-weight: 700 !important; font-size: var(--text-2xl) !important; }
h3 { font-weight: 600 !important; font-size: var(--text-xl)  !important; }
h4 { font-weight: 600 !important; font-size: var(--text-lg)  !important; }

p, span, label, div { color: var(--text-main); }
p { color: var(--text-muted) !important; line-height: 1.65; }

/* Prevent global p rule bleeding into buttons */
button p, button span, button div,
[data-testid^="stBaseButton"] p,
[data-testid^="stBaseButton"] span,
[data-testid^="stBaseButton"] div { line-height: inherit !important; }

/* ═══════════════════════════════════════════════════════════════════
   5. CARDS & PANELS
   ═══════════════════════════════════════════════════════════════════ */

/* ── Base card (used everywhere) ── */
.ip-card,
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
  background:    var(--bg-card) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow:    var(--shadow-card) !important;
  transition:    transform var(--anim-base) var(--ease),
                 box-shadow var(--anim-base) var(--ease),
                 border-color var(--anim-base) var(--ease) !important;
}

.ip-card { padding: var(--space-6) !important; }

/* ── Glass variant (backdrop blur) ── */
.glass-card {
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  padding: var(--space-6) !important;
}

/* ── Hover lift ── */
.ip-card-hover:hover,
.glass-card:hover,
.elevated-card:hover {
  transform:    translateY(-3px) !important;
  box-shadow:   var(--shadow-lg) !important;
  border-color: var(--border-hover) !important;
}

/* ── Featured / highlighted card ── */
.ip-card-featured {
  background:    linear-gradient(145deg, rgba(59,130,246,0.07), rgba(139,92,246,0.04)) !important;
  border-color:  rgba(59,130,246,0.2) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow:    var(--shadow-card), var(--shadow-glow-blue) !important;
}

/* ── Metric card variant ── */
.ip-metric-card {
  background:    var(--bg-card) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding:       var(--space-6) !important;
  box-shadow:    var(--shadow-card) !important;
  text-align:    center;
}

/* ═══════════════════════════════════════════════════════════════════
   6. INPUTS & FORM CONTROLS
   ═══════════════════════════════════════════════════════════════════ */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
  background-color: var(--bg-input) !important;
  border:           1px solid var(--border) !important;
  border-radius:    var(--radius-md) !important;
  color:            var(--text-main) !important;
  transition:       border-color var(--anim-base) var(--ease),
                    box-shadow   var(--anim-base) var(--ease) !important;
}

div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within > div,
div[data-baseweb="select"]:focus-within > div {
  border-color: var(--primary) !important;
  box-shadow:   0 0 0 3px var(--primary-glow) !important;
}

input, textarea {
  color:            var(--text-main) !important;
  background-color: transparent !important;
  font-family:      var(--font-sans) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
  background:    var(--bg-input) !important;
  border:        1px dashed rgba(59,130,246,0.35) !important;
  border-radius: var(--radius-lg) !important;
  transition:    border-color var(--anim-base) var(--ease) !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--primary) !important;
  background:   rgba(59,130,246,0.04) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   7. BUTTONS
   ═══════════════════════════════════════════════════════════════════ */

/* ── Primary ── */
button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background:    var(--grad-primary) !important;
  color:         #ffffff !important;
  border:        none !important;
  border-radius: var(--radius-md) !important;
  padding:       10px 24px !important;
  font-weight:   700 !important;
  font-size:     var(--text-sm) !important;
  box-shadow:    0 4px 14px rgba(59,130,246,0.35) !important;
  transition:    all var(--anim-base) var(--ease) !important;
  letter-spacing:-0.01em !important;
}

button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  transform:  translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(59,130,246,0.45), 0 0 0 1px rgba(139,92,246,0.3) !important;
}

button[kind="primary"]:active,
[data-testid="stBaseButton-primary"]:active {
  transform:  translateY(0) !important;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
}

/* ── Secondary ── */
button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
  background:    var(--bg-card) !important;
  color:         var(--text-primary) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-weight:   600 !important;
  font-size:     var(--text-sm) !important;
  transition:    all var(--anim-base) var(--ease) !important;
}

button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
  background:   var(--bg-surface) !important;
  border-color: var(--border-active) !important;
  transform:    translateY(-1px) !important;
  box-shadow:   0 4px 12px rgba(0,0,0,0.3) !important;
}

/* ── Text / ghost ── */
button[kind="tertiary"],
[data-testid="stBaseButton-tertiary"] {
  background:    transparent !important;
  color:         var(--text-muted) !important;
  border:        none !important;
  font-weight:   500 !important;
  transition:    color var(--anim-fast) var(--ease) !important;
}

button[kind="tertiary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
  color: var(--text-primary) !important;
}

/* ── Button text color overrides ── */
button[kind="primary"] p, button[kind="primary"] span, button[kind="primary"] div,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primary"] span,
[data-testid="stBaseButton-primary"] div,
button[kind="primaryFormSubmit"] p, button[kind="primaryFormSubmit"] span,
button[kind="secondaryFormSubmit"] p, button[kind="secondaryFormSubmit"] span,
div[data-testid="stForm"] button p, div[data-testid="stForm"] button span {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[kind="primary"]:hover p, button[kind="primary"]:hover span,
[data-testid="stBaseButton-primary"]:hover p,
[data-testid="stBaseButton-primary"]:hover span,
button[kind="primaryFormSubmit"]:hover p,
button[kind="secondaryFormSubmit"]:hover p,
div[data-testid="stForm"] button:hover p,
div[data-testid="stForm"] button:hover span {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[kind="primary"]:active p, button[kind="primary"]:focus p,
[data-testid="stBaseButton-primary"]:active p,
[data-testid="stBaseButton-primary"]:focus p {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[kind="secondary"] p, button[kind="secondary"] span, button[kind="secondary"] div,
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondary"] span,
[data-testid="stBaseButton-secondary"] div {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[kind="secondary"]:hover p, button[kind="secondary"]:hover span,
[data-testid="stBaseButton-secondary"]:hover p,
[data-testid="stBaseButton-secondary"]:hover span {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[kind="secondary"]:active p, button[kind="secondary"]:focus p,
[data-testid="stBaseButton-secondary"]:active p,
[data-testid="stBaseButton-secondary"]:focus p {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

button[data-testid="stTab"] p, button[data-testid="stTab"] span,
button[data-testid="stTab"] div { color: inherit !important; -webkit-text-fill-color: inherit !important; }

button:disabled p, button:disabled span,
button[disabled] p, button[disabled] span { opacity: 0.45 !important; }

/* ═══════════════════════════════════════════════════════════════════
   8. DATA TABLES
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border-radius: var(--radius-lg);
  overflow:      hidden;
  box-shadow:    var(--shadow-md);
  border:        1px solid var(--border);
}

.stDataFrame [data-testid="stTable"] th {
  background-color: var(--bg-panel) !important;
  color:            var(--text-secondary) !important;
  font-weight:      600 !important;
  font-size:        var(--text-xs) !important;
  text-transform:   uppercase;
  letter-spacing:   0.06em;
  border-bottom:    1px solid var(--border) !important;
  padding:          10px 14px !important;
}

.stDataFrame [data-testid="stTable"] td {
  color:            var(--text-muted) !important;
  border-bottom:    1px solid var(--border-subtle) !important;
  background-color: var(--bg-card) !important;
  font-size:        var(--text-sm) !important;
  padding:          10px 14px !important;
}

/* ═══════════════════════════════════════════════════════════════════
   9. METRICS
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stMetricValue"] {
  color:       var(--blue-400) !important;
  font-weight: 800 !important;
  font-size:   var(--text-3xl) !important;
}

[data-testid="stMetricLabel"] {
  color:          var(--text-muted) !important;
  font-weight:    600 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size:      var(--text-xs) !important;
}

[data-testid="stMetricDelta"] { color: var(--success) !important; }

/* ═══════════════════════════════════════════════════════════════════
   10. SELECTBOX / DROPDOWN
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label,
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label,
[data-testid="stSlider"] label {
  color:       var(--text-muted) !important;
  font-weight: 500 !important;
  font-size:   var(--text-sm) !important;
}

[data-baseweb="popover"] {
  background:    var(--bg-surface) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  box-shadow:    var(--shadow-xl) !important;
}

[data-baseweb="menu"] {
  background: var(--bg-surface) !important;
  border:     1px solid var(--border) !important;
}

[role="option"] { color: var(--text-main) !important; background: transparent !important; }
[role="option"]:hover { background: var(--bg-hover) !important; }
[role="option"][aria-selected="true"] {
  background: rgba(59,130,246,0.12) !important;
  color:      var(--blue-400) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   11. ALERTS
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stAlert"], .stAlert {
  background:    var(--bg-panel) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color:         var(--text-main) !important;
  font-size:     var(--text-sm) !important;
}
[data-testid="stInfo"]    { background: var(--info-bg)    !important; border-color: var(--info-border)    !important; }
[data-testid="stSuccess"] { background: var(--success-bg) !important; border-color: var(--success-border) !important; }
[data-testid="stWarning"] { background: var(--warning-bg) !important; border-color: var(--warning-border) !important; }
[data-testid="stError"]   { background: var(--danger-bg)  !important; border-color: var(--danger-border)  !important; }

/* ═══════════════════════════════════════════════════════════════════
   12. PROGRESS BAR / SPINNER
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stProgressBar"] > div { background: var(--bg-surface) !important; border-radius: var(--radius-full) !important; }
[data-testid="stProgressBar"] > div > div {
  background:    var(--grad-primary) !important;
  border-radius: var(--radius-full) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   13. EXPANDER
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background:    var(--bg-card) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
}
[data-testid="stExpander"] summary { color: var(--text-primary) !important; font-weight: 500 !important; }

/* ═══════════════════════════════════════════════════════════════════
   14. TABS
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stTabs"] { background: transparent !important; }
button[data-testid="stTab"] {
  color:       var(--text-muted) !important;
  background:  transparent !important;
  border:      none !important;
  font-weight: 500 !important;
  font-size:   var(--text-sm) !important;
  padding:     8px 16px !important;
  transition:  color var(--anim-fast) var(--ease) !important;
}
button[data-testid="stTab"]:hover { color: var(--text-primary) !important; }
button[data-testid="stTab"][aria-selected="true"] {
  color:        var(--blue-400) !important;
  border-bottom:2px solid var(--blue-500) !important;
  font-weight:  600 !important;
}

/* ═══════════════════════════════════════════════════════════════════
   15. SCROLLBAR
   ═══════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-main); }
::-webkit-scrollbar-thumb {
  background:    rgba(59,130,246,0.22);
  border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.4); }

/* ═══════════════════════════════════════════════════════════════════
   16. REUSABLE UTILITY CLASSES
   ═══════════════════════════════════════════════════════════════════ */

/* ── Badges ── */
.ip-badge {
  display:        inline-flex;
  align-items:    center;
  gap:            5px;
  padding:        3px 10px;
  border-radius:  var(--radius-full);
  font-size:      var(--text-xs);
  font-weight:    600;
  letter-spacing: 0.03em;
  white-space:    nowrap;
}
.ip-badge-blue   { background: rgba(59,130,246,0.12); color: var(--blue-400);   border: 1px solid rgba(59,130,246,0.25); }
.ip-badge-purple { background: rgba(139,92,246,0.12); color: var(--purple-400); border: 1px solid rgba(139,92,246,0.25); }
.ip-badge-green  { background: var(--success-bg);     color: var(--green-400);  border: 1px solid var(--success-border); }
.ip-badge-amber  { background: var(--warning-bg);     color: var(--amber-400);  border: 1px solid var(--warning-border); }
.ip-badge-red    { background: var(--danger-bg);      color: var(--red-400);    border: 1px solid var(--danger-border);  }
.ip-badge-cyan   { background: var(--info-bg);        color: var(--cyan-400);   border: 1px solid var(--info-border);   }
.ip-badge-muted  { background: rgba(255,255,255,0.05);color: var(--text-muted); border: 1px solid var(--border);        }

/* ── Status Pills (with live dot) ── */
.ip-status {
  display:      inline-flex;
  align-items:  center;
  gap:          6px;
  padding:      4px 12px;
  border-radius:var(--radius-full);
  font-size:    var(--text-xs);
  font-weight:  600;
}
.ip-status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  animation: statusPulse 2s ease-in-out infinite;
}
@keyframes statusPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.45; } }

/* ── Divider ── */
.ip-divider {
  height:     1px;
  background: linear-gradient(90deg, transparent, var(--border) 30%, var(--border) 70%, transparent);
  margin:     var(--space-6) 0;
  position:   relative;
}
.ip-divider::after {
  content:   '';
  position:  absolute;
  top: 0; left: 50%;
  transform: translateX(-50%);
  width:     80px; height: 1px;
  background:linear-gradient(90deg, transparent, var(--primary), transparent);
  animation: divGlow 3s ease-in-out infinite;
}
@keyframes divGlow { 0%,100% { opacity: 0.3; width: 60px; } 50% { opacity: 1; width: 140px; } }

/* ── Section eyebrow label ── */
.ip-eyebrow {
  display:        inline-flex;
  align-items:    center;
  gap:            8px;
  font-size:      var(--text-xs);
  font-weight:    700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color:          var(--blue-400);
  margin-bottom:  var(--space-3);
}

/* ── Page header block ── */
.ip-page-header {
  margin-bottom: var(--space-8);
  padding-bottom:var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
}
.ip-page-title {
  font-size:   var(--text-3xl);
  font-weight: 800;
  color:       var(--text-primary);
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: var(--space-2);
}
.ip-page-subtitle {
  font-size:  var(--text-base);
  color:      var(--text-muted);
  line-height:1.6;
}

/* ── Stat number display ── */
.ip-stat-value {
  font-size:      var(--text-4xl);
  font-weight:    800;
  letter-spacing: -0.04em;
  line-height:    1;
  background:     var(--grad-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.ip-stat-label {
  font-size:      var(--text-xs);
  font-weight:    600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color:          var(--text-dim);
  margin-top:     var(--space-1);
}

/* ── Activity row ── */
.ip-activity-row {
  display:       flex;
  align-items:   center;
  gap:           var(--space-3);
  padding:       var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  transition:    background var(--anim-fast) var(--ease);
}
.ip-activity-row:hover { background: var(--bg-hover); }

/* ── Gradient text utility ── */
.ip-text-gradient {
  background:              var(--grad-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip:         text;
}
.ip-text-blue   { color: var(--blue-400)   !important; }
.ip-text-purple { color: var(--purple-400) !important; }
.ip-text-green  { color: var(--green-400)  !important; }
.ip-text-amber  { color: var(--amber-400)  !important; }
.ip-text-red    { color: var(--red-400)    !important; }
.ip-text-muted  { color: var(--text-muted) !important; }
.ip-text-dim    { color: var(--text-dim)   !important; }

/* ═══════════════════════════════════════════════════════════════════
   17. PAGE-SPECIFIC ELEMENT OVERRIDES
   ═══════════════════════════════════════════════════════════════════ */
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
.am-label { color: var(--text-muted) !important; }

.pm-val { font-weight: 700 !important; }

/* ── Status colors (unified) ── */
.status-pending,   .status-payment_pending { color: var(--amber-400) !important; }
.status-queued     { color: var(--blue-400)   !important; }
.status-printing   { color: var(--cyan-400)   !important; }
.status-completed,
.status-ready,
.status-collected  { color: var(--green-400)  !important; }
.status-cancelled,
.status-failed     { color: var(--red-400)    !important; }

/* ═══════════════════════════════════════════════════════════════════
   18. ANIMATIONS
   ═══════════════════════════════════════════════════════════════════ */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes pulseGlow {
  0%,100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
  50%     { box-shadow: 0 0 0 6px rgba(59,130,246,0.12); }
}
@keyframes spinSlow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.ip-animate-in   { animation: fadeSlideUp var(--anim-slow) var(--ease-out) both; }
.ip-animate-fast { animation: fadeIn var(--anim-fast) var(--ease-out) both; }

/* ── Loading skeleton ── */
.ip-skeleton {
  background:            linear-gradient(90deg, var(--bg-card) 25%, var(--bg-surface) 50%, var(--bg-card) 75%);
  background-size:       200% auto;
  animation:             shimmer 1.8s linear infinite;
  border-radius:         var(--radius-md);
}

/* ═══════════════════════════════════════════════════════════════════
   19. RESPONSIVE BREAKPOINTS
   ═══════════════════════════════════════════════════════════════════ */

/* ── Ultra-wide (≥ 1800px) — more breathing room ── */
@media (min-width: 1800px) {
  [data-testid="stMainBlockContainer"],
  .block-container,
  .appview-container .main .block-container {
    max-width:     1600px !important;
    padding-left:  4rem !important;
    padding-right: 4rem !important;
  }
}

/* ── Large desktop (≥ 1400px) ── */
@media (min-width: 1400px) {
  [data-testid="stMetricValue"] { font-size: 2.4rem !important; }
}

/* ── Tablet (≤ 900px) ── */
@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"],
  .block-container,
  .appview-container .main .block-container {
    padding-left:  1.5rem !important;
    padding-right: 1.5rem !important;
    padding-top:   1.5rem !important;
  }
  h1 { font-size: 1.8rem !important; }
}

/* ── Mobile (≤ 600px) ── */
@media (max-width: 600px) {
  [data-testid="stMainBlockContainer"],
  .block-container,
  .appview-container .main .block-container {
    padding-left:   0.875rem !important;
    padding-right:  0.875rem !important;
    padding-top:    1rem     !important;
    padding-bottom: 80px     !important;
  }
  h1 { font-size: 1.6rem !important; }
  h2 { font-size: 1.3rem !important; }
  h3 { font-size: 1.1rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
  .ip-stat-value { font-size: 2rem !important; }
  .glass-card:hover, .elevated-card:hover, .ip-card-hover:hover {
    transform: none !important;
  }
  button[kind="primary"],
  [data-testid="stBaseButton-primary"],
  button[kind="secondary"],
  [data-testid="stBaseButton-secondary"] {
    padding:   10px 16px !important;
    font-size: var(--text-sm) !important;
  }
  [data-testid="stExpander"] summary { font-size: var(--text-sm) !important; }
}

/* ── Very small (≤ 390px) ── */
@media (max-width: 390px) {
  [data-testid="stMainBlockContainer"],
  .block-container {
    padding-left:  0.5rem !important;
    padding-right: 0.5rem !important;
  }
  h1 { font-size: 1.35rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration:   0.01ms !important;
    transition-duration:  0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}

</style>
"""
