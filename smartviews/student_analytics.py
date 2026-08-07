"""
IntelliPrint Nexus - Student Analytics Page (Phase 3)
6 interactive Plotly charts showing printing behaviour and trends.
"""

import streamlit as st
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


_CHART_BG = "rgba(0,0,0,0)"
_FONT_COLOR = "rgba(255,255,255,0.6)"
_GRID_COLOR = "rgba(255,255,255,0.05)"
_MARGIN = dict(l=10, r=10, t=30, b=10)
_COLORS_GRADIENT = ["#3B82F6", "#3b82f6", "#7c3aed", "#ec4899", "#f59e0b", "#10b981"]


def _base_layout(title: str = "", height: int = 280) -> dict:
    return dict(
        paper_bgcolor=_CHART_BG,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_FONT_COLOR, size=11),
        margin=_MARGIN,
        height=height,
        title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,.6)"), x=0.02),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    font=dict(color="rgba(255,255,255,.5)")),
    )


def show_student_analytics():
    """Render the full student analytics dashboard."""
    user    = st.session_state.get("user", {})
    user_id = user.get("id", 0)

    st.html(_analytics_css())

    st.html("""
    <div class="an-header">
        <div class="an-title">📊 My Print Analytics</div>
        <div class="an-sub">Insights into your printing behaviour and trends</div>
    </div>
    """)

    # ── Load data ─────────────────────────────────────────────────────────────
    analytics = {}
    all_jobs  = []
    try:
        from smartdb.crud_ext import get_student_analytics
        from smartdb.crud import get_user_jobs
        analytics = get_student_analytics(user_id) or {}
        all_jobs  = get_user_jobs(user_id) or []
    except Exception as e:
        st.warning(f"Could not load analytics data: {e}")
        return

    if not all_jobs:
        st.html("""
        <div class="an-empty">
            <div style="font-size:3rem;">📊</div>
            <div class="an-empty-title">No data yet</div>
            <div class="an-empty-sub">Print some documents to see your analytics here.</div>
        </div>
        """)
        return

    # ── Summary strip ─────────────────────────────────────────────────────────
    sc = st.columns(4)
    for col, (icon, label, val, color) in zip(sc, [
        ("📄", "Total Pages",  analytics.get("total_pages", 0),               "#3B82F6"),
        ("💰", "Total Spent",  f"₹{analytics.get('total_spent', 0):.2f}",     "#10b981"),
        ("♻️", "Paper Saved",  f"{analytics.get('paper_saved', 0)} sheets",   "#84cc16"),
        ("🌿", "CO₂ Saved",    f"{analytics.get('co2_saved', 0):.3f} kg",     "#22c55e"),
    ]):
        with col:
            st.html(f"""
            <div class="an-stat" style="border-left:3px solid {color};">
                <div class="an-stat-icon">{icon}</div>
                <div class="an-stat-val" style="color:{color};">{val}</div>
                <div class="an-stat-lbl">{label}</div>
            </div>
            """)

    if not _PLOTLY:
        st.warning("📊 Install `plotly` (`pip install plotly`) to view charts.")
        return

    # ── Row 1: Monthly pages + Monthly spending ────────────────────────────────
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        monthly_p = analytics.get("monthly_pages", {})
        if monthly_p:
            sorted_m = sorted(monthly_p.keys(), key=lambda m: datetime.strptime(m, "%b %Y"))
            vals = [monthly_p[k] for k in sorted_m]
            fig = go.Figure(go.Bar(
                x=sorted_m, y=vals, name="Pages",
                marker=dict(color=vals, colorscale=[[0, "#3b82f6"], [1, "#3B82F6"]],
                            line=dict(width=0)),
                hovertemplate="%{x}: %{y} pages<extra></extra>",
            ))
            fig.update_layout(**_base_layout("📄 Monthly Pages Printed"))
            fig.update_xaxes(showgrid=False, tickfont=dict(color="rgba(255,255,255,.45)"))
            fig.update_yaxes(gridcolor=_GRID_COLOR, tickfont=dict(color="rgba(255,255,255,.35)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">📄 Monthly Pages — No data yet</div>')

    with r1c2:
        monthly_s = analytics.get("monthly_spend", {})
        if monthly_s:
            sorted_m = sorted(monthly_s.keys(), key=lambda m: datetime.strptime(m, "%b %Y"))
            vals = [monthly_s[k] for k in sorted_m]
            fig = go.Figure(go.Scatter(
                x=sorted_m, y=vals, mode="lines+markers",
                line=dict(color="#10b981", width=2),
                marker=dict(size=7, color="#10b981"),
                fill="tozeroy", fillcolor="rgba(16,185,129,.1)",
                hovertemplate="₹%{y:.2f}<extra></extra>",
            ))
            fig.update_layout(**_base_layout("💰 Monthly Spending (₹)"))
            fig.update_xaxes(showgrid=False, tickfont=dict(color="rgba(255,255,255,.45)"))
            fig.update_yaxes(gridcolor=_GRID_COLOR, tickfont=dict(color="rgba(255,255,255,.35)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">💰 Monthly Spending — No data yet</div>')

    # ── Row 2: Color vs B&W + Duplex vs Simplex ────────────────────────────────
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        color_j = analytics.get("color_jobs", 0)
        bw_j    = analytics.get("bw_jobs", 0)
        if color_j + bw_j > 0:
            fig = go.Figure(go.Pie(
                labels=["Black & White", "Colour"],
                values=[bw_j, color_j],
                marker=dict(colors=["#6b7280", "#ec4899"]),
                hole=0.55,
                hovertemplate="%{label}: %{value} jobs (%{percent})<extra></extra>",
                textfont=dict(color="white"),
            ))
            fig.update_layout(**_base_layout("🎨 Colour vs B&W"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">🎨 Colour vs B&W — No data</div>')

    with r2c2:
        dup_j = analytics.get("duplex_jobs", 0)
        sim_j = analytics.get("simplex_jobs", 0)
        if dup_j + sim_j > 0:
            fig = go.Figure(go.Pie(
                labels=["Simplex (1-side)", "Duplex (2-side)"],
                values=[sim_j, dup_j],
                marker=dict(colors=["#3b82f6", "#10b981"]),
                hole=0.55,
                hovertemplate="%{label}: %{value} jobs (%{percent})<extra></extra>",
                textfont=dict(color="white"),
            ))
            fig.update_layout(**_base_layout("📄 Simplex vs Duplex"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">📄 Duplex — No data</div>')

    # ── Row 3: Printer usage + Peak hours ─────────────────────────────────────
    r3c1, r3c2 = st.columns(2)

    with r3c1:
        from collections import Counter
        try:
            from smartdb.crud import get_all_printers
            printer_map = {p["id"]: p.get("name", f"Printer {p['id']}")
                           for p in (get_all_printers() or [])}
        except Exception:
            printer_map = {}

        pid_counts = Counter(
            printer_map.get(j.get("printer_id"), "Unknown")
            for j in all_jobs if j.get("printer_id")
        )
        if pid_counts:
            names = list(pid_counts.keys())
            counts = list(pid_counts.values())
            fig = go.Figure(go.Bar(
                x=counts, y=names, orientation="h",
                marker=dict(color=_COLORS_GRADIENT[:len(names)]),
                hovertemplate="%{y}: %{x} jobs<extra></extra>",
            ))
            fig.update_layout(**_base_layout("🖨️ Printer Usage"))
            fig.update_xaxes(gridcolor=_GRID_COLOR, tickfont=dict(color="rgba(255,255,255,.35)"))
            fig.update_yaxes(showgrid=False, tickfont=dict(color="rgba(255,255,255,.55)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">🖨️ Printer Usage — No data</div>')

    with r3c2:
        # Peak hours histogram
        hours = []
        for j in all_jobs:
            ts = j.get("submitted_at") or j.get("created_at")
            if ts:
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace("Z", ""))
                    hours.append(ts.hour)
                except Exception:
                    pass

        if hours:
            from collections import Counter as _C
            hc = _C(hours)
            all_hours = list(range(24))
            vals = [hc.get(h, 0) for h in all_hours]
            labels = [f"{h:02d}:00" for h in all_hours]
            fig = go.Figure(go.Bar(
                x=labels, y=vals,
                marker=dict(color=vals, colorscale=[[0, "#7c3aed"], [1, "#3B82F6"]],
                            line=dict(width=0)),
                hovertemplate="%{x}: %{y} jobs<extra></extra>",
            ))
            fig.update_layout(**_base_layout("⏰ Peak Printing Hours"))
            fig.update_xaxes(showgrid=False, tickfont=dict(color="rgba(255,255,255,.35)"),
                             tickangle=45)
            fig.update_yaxes(gridcolor=_GRID_COLOR, tickfont=dict(color="rgba(255,255,255,.35)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.html('<div class="an-empty-chart">⏰ Peak Hours — No data</div>')

    # ── Detailed stats table ───────────────────────────────────────────────────
    st.html('<div class="an-section-title">📋 Detailed Statistics</div>')
    stats = [
        ("Total Jobs",          analytics.get("total_jobs", 0),          "jobs"),
        ("Total Pages",         analytics.get("total_pages", 0),         "pages"),
        ("Total Documents",     analytics.get("total_docs", 0),          "files"),
        ("Total Spent",         f"₹{analytics.get('total_spent', 0):.2f}", ""),
        ("Completed Jobs",      analytics.get("completed_jobs", 0),      "jobs"),
        ("Colour Jobs",         analytics.get("color_jobs", 0),          "jobs"),
        ("B&W Jobs",            analytics.get("bw_jobs", 0),             "jobs"),
        ("Duplex Jobs",         analytics.get("duplex_jobs", 0),         "jobs"),
        ("Today's Jobs",        analytics.get("todays_jobs", 0),         "jobs"),
        ("Paper Saved",         analytics.get("paper_saved", 0),         "sheets"),
        ("CO₂ Saved",           f"{analytics.get('co2_saved', 0):.3f}",  "kg"),
        ("Avg Wait Time",       f"{analytics.get('avg_wait_min', 0):.1f}", "min"),
    ]
    tc1, tc2 = st.columns(2)
    for i, (label, val, unit) in enumerate(stats):
        with (tc1 if i % 2 == 0 else tc2):
            st.html(f"""
            <div class="an-stat-row">
                <span class="an-stat-row-label">{label}</span>
                <span class="an-stat-row-val">{val} <span class="an-unit">{unit}</span></span>
            </div>
            """)


def _analytics_css() -> str:
    return """<style>
.an-header { padding:14px 0 10px; margin-bottom:1rem; }
.an-title {
    font-size:1.8rem; font-weight:800;
    background:linear-gradient(135deg,#3B82F6,#8B5CF6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.an-sub { color:rgba(255,255,255,.4); font-size:.88rem; margin-top:4px; }

.an-stat {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
    border-radius:12px; padding:14px 16px; margin-bottom:12px;
}
.an-stat-icon { font-size:1.4rem; }
.an-stat-val { font-size:1.5rem; font-weight:800; margin-top:2px; }
.an-stat-lbl { font-size:.68rem; color:rgba(255,255,255,.4);
               text-transform:uppercase; letter-spacing:.4px; margin-top:3px; }

.an-empty {
    text-align:center; padding:60px 20px;
    background:rgba(255,255,255,.02); border:1px dashed rgba(255,255,255,.08);
    border-radius:16px; margin:20px 0;
}
.an-empty-title { font-size:1.1rem; font-weight:700; color:rgba(255,255,255,.6); margin:10px 0 6px; }
.an-empty-sub { color:rgba(255,255,255,.35); font-size:.85rem; }
.an-empty-chart {
    text-align:center; padding:40px 20px;
    background:rgba(255,255,255,.02); border:1px dashed rgba(255,255,255,.06);
    border-radius:12px; color:rgba(255,255,255,.35); font-size:.85rem; margin:4px 0;
}

.an-section-title {
    font-size:.95rem; font-weight:700; color:rgba(255,255,255,.7);
    text-transform:uppercase; letter-spacing:.5px; margin:1.4rem 0 10px;
}
.an-stat-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 12px; background:rgba(255,255,255,.02);
    border:1px solid rgba(255,255,255,.05); border-radius:8px; margin-bottom:4px;
}
.an-stat-row-label { font-size:.82rem; color:rgba(255,255,255,.6); }
.an-stat-row-val { font-size:.92rem; font-weight:700; color:#fff; }
.an-unit { font-size:.7rem; color:rgba(255,255,255,.35); font-weight:400; }
</style>"""
