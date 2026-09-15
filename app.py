"""
GridPulse AI — Operator Dashboard
Frontend branch: refactored layout with sidebar navigation,
collapsible sections, and explicit zone/time controls.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dateutil.parser
from datetime import timedelta
import os
import sys

sys.path.append(os.path.abspath("src"))
from operator_brief import (
    get_latest_valid_timestamp,
    build_operator_context,
    render_deterministic_brief,
)

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GridPulse AI | Operator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# THEME — same dark control-room palette, cleaner variable names
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    /* ---- layout ---- */
    .block-container { padding-top: 1.2rem; }

    /* ---- KPI cards ---- */
    .kpi-card {
        background: #1a1a2e;
        padding: 18px 22px;
        border-radius: 6px;
        border-left: 4px solid #0f62fe;
        margin-bottom: 16px;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #a8b0bc;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }
    .kpi-number {
        font-size: 1.65rem;
        font-weight: 700;
        color: #e8eaed;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #6c7a8d;
        margin-top: 2px;
    }

    /* ---- safety banners ---- */
    .banner {
        padding: 14px 18px;
        border-radius: 5px;
        margin: 8px 0 18px;
        font-size: 0.92rem;
        font-weight: 500;
        line-height: 1.5;
    }
    .banner-green  { background: rgba(36,161,72,0.15);  border: 1px solid #24a148; color: #6ef09a; }
    .banner-yellow { background: rgba(241,194,27,0.15); border: 1px solid #f1c21b; color: #f5d76e; }
    .banner-red    { background: rgba(218,30,40,0.15);  border: 1px solid #da1e28; color: #ff8389; }

    /* ---- section dividers ---- */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #c9d1d9;
        border-bottom: 1px solid #30363d;
        padding-bottom: 4px;
        margin: 20px 0 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading pipeline outputs…")
def load_outputs():
    paths = {
        "demand":     "outputs/demand_model/demand_predictions.csv",
        "renewable":  "outputs/renewable_model/renewable_predictions.csv",
        "anomaly":    "outputs/anomaly_model/current_asset_status.csv",
        "root_cause": "outputs/root_cause/root_cause_predictions.csv",
        "grid_risk":  "outputs/grid_risk/grid_risk_predictions.csv",
        "opt":        "outputs/optimization/optimization_actions.csv",
        "sim":        "outputs/simulation/baseline_vs_optimized.csv",
    }
    try:
        return {k: pd.read_csv(v) for k, v in paths.items()}
    except FileNotFoundError as exc:
        st.error(f"Missing pipeline output: {exc}")
        st.stop()


data = load_outputs()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/flash-on.png", width=42)
    st.markdown("### GridPulse AI")
    st.caption("Decision-support system · v2.0")
    st.divider()

    zones = sorted(data["demand"]["zone_id"].unique().tolist())
    selected_zone = st.selectbox("📍 Zone", zones)

    scenario = st.radio(
        "🎭 Scenario",
        ["Live / Latest", "Demo A – Normal", "Demo B – High Stress", "Demo C – Adverse"],
        index=0,
    )
    st.divider()
    st.caption("⚠️ **DECISION SUPPORT ONLY**\nRecommendations require operator approval. Not for autonomous control.")

# ──────────────────────────────────────────────────────────────────────────────
# TIMESTAMP RESOLUTION
# ──────────────────────────────────────────────────────────────────────────────
latest_ts = get_latest_valid_timestamp(data)


def find_demo_ts(scenario_label: str, zone: str):
    for _, row in data["sim"].iterrows():
        if row["zone_id"] != zone:
            continue
        ts_dec = (
            dateutil.parser.parse(row["target_timestamp"]) - timedelta(minutes=60)
        ).strftime("%Y-%m-%d %H:%M:%S")
        try:
            ctx = build_operator_context(data, ts_dec, zone)
        except Exception:
            continue
        flag = ctx["operator_decision"]["decision_flag"]
        adv = ctx["simulation"]["adverse_counterfactual"]
        if scenario_label == "Demo A – Normal" and flag == "GREEN":
            return ts_dec
        if scenario_label == "Demo B – High Stress" and flag in ("YELLOW", "RED") and not adv:
            return ts_dec
        if scenario_label == "Demo C – Adverse" and flag == "RED" and adv:
            return ts_dec
    return None


if scenario == "Live / Latest":
    selected_ts = latest_ts
else:
    demo_ts = find_demo_ts(scenario, selected_zone)
    if demo_ts is None:
        st.sidebar.warning("Scenario unavailable for this zone — using live.")
        selected_ts = latest_ts
    else:
        selected_ts = demo_ts

# Build context
try:
    ctx = build_operator_context(data, selected_ts, selected_zone)
except Exception as exc:
    st.error(f"Context error: {exc}")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
col_title, col_ts = st.columns([3, 1])
col_title.markdown("## ⚡ GRIDPULSE AI — Operator Dashboard")
col_ts.markdown(f"<div style='text-align:right;color:#6c7a8d;font-size:0.8rem;padding-top:14px'>Zone: <b>{selected_zone}</b><br>{selected_ts}</div>", unsafe_allow_html=True)

# Safety banner
flag = ctx["operator_decision"]["decision_flag"]
explanation = ctx["operator_decision"]["explanation"]
flag_map = {
    "GREEN":  ("banner-green",  "🟢 GREEN — NORMAL OPERATION"),
    "YELLOW": ("banner-yellow", "🟡 YELLOW — OPERATOR REVIEW REQUIRED"),
    "RED":    ("banner-red",    "🔴 RED — OPERATOR APPROVAL REQUIRED"),
}
css_cls, label = flag_map.get(flag, ("banner-yellow", f"⚪ {flag}"))
st.markdown(f"<div class='banner {css_cls}'><b>{label}</b><br>{explanation}</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────────────────────────────────────────
def kpi(col, label, value, sub=""):
    col.markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-number'>{value}</div>"
        f"<div class='kpi-sub'>{sub}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "Demand (now)", f"{ctx['current_state']['demand_mw']:.1f} MW", "current load")
kpi(c2, "Renewables (now)", f"{ctx['current_state']['renewable_mw']:.1f} MW", "solar + wind")
kpi(c3, "Transmission Util", f"{ctx['current_state']['transmission_utilization_pct']*100:.1f}%", "line loading")
kpi(c4, "Grid Risk", ctx["grid_forecast"]["transmission_risk"], "predicted level")
kpi(c5, "Curtailment", f"{ctx['current_state']['curtailment_mw']:.1f} MW", "currently curtailed")

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 Overview", "📈 Forecast", "🔧 Asset Health", "⚙️ Optimisation", "🔁 Simulation", "📋 Operator Brief"])

# ── TAB 1: Overview ───────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("<div class='section-title'>60-Minute Horizon</div>", unsafe_allow_html=True)
    o1, o2, o3, o4 = st.columns(4)
    kpi(o1, "Pred. Demand (+60m)", f"{ctx['demand_forecast']['predicted_demand_60m']:.1f} MW")
    kpi(o2, "Pred. Renewables (+60m)", f"{ctx['renewable_forecast']['renewable_60m']:.1f} MW")
    kpi(o3, "Pred. Risk", ctx["grid_forecast"]["transmission_risk"])
    kpi(o4, "Curtailment Risk", f"{ctx['grid_forecast']['curtailment_probability']:.0%}")

    st.markdown("<div class='section-title'>Recommended Action</div>", unsafe_allow_html=True)
    action_mw = ctx["optimization"]["action_mw"]
    if action_mw > 0:
        st.info(
            f"**{ctx['optimization']['action']}** via `{ctx['optimization']['resource_type']}` "
            f"— **{action_mw:.1f} MW** | {ctx['optimization']['reason']}"
        )
    else:
        st.success("✅ No action recommended — grid within normal parameters.")

# ── TAB 2: Forecast ───────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("<div class='section-title'>Observed vs Forecast (+60 min)</div>", unsafe_allow_html=True)
    categories = ["Demand (MW)", "Renewables (MW)", "Curtailment (MW)"]
    observed = [
        ctx["current_state"]["demand_mw"],
        ctx["current_state"]["renewable_mw"],
        ctx["current_state"]["curtailment_mw"],
    ]
    forecast = [
        ctx["demand_forecast"]["predicted_demand_60m"],
        ctx["renewable_forecast"]["renewable_60m"],
        ctx["grid_forecast"]["curtailment_predicted_mw"],
    ]
    fig = go.Figure(data=[
        go.Bar(name="Observed (t)", x=categories, y=observed, marker_color="#0f62fe"),
        go.Bar(name="Forecast (t+60)", x=categories, y=forecast, marker_color="#6929c4"),
    ])
    fig.update_layout(barmode="group", template="plotly_dark", height=380,
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: Asset Health ───────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("<div class='section-title'>Renewable Asset Alerts</div>", unsafe_allow_html=True)
    alerts = ctx.get("asset_alerts", [])
    if alerts:
        df_alerts = pd.DataFrame(alerts)
        st.dataframe(df_alerts, use_container_width=True, hide_index=True)
    else:
        st.success("✅ All assets operating within normal bounds.")

# ── TAB 4: Optimisation ───────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("<div class='section-title'>Decision Logic Chain</div>", unsafe_allow_html=True)
    st.markdown("""
1. **Demand Forecast** (PATH 3) + **Renewable Forecast** (PATH 4) → predicted supply/demand gap  
2. **Grid Risk** (PATH 7) → transmission risk level  
3. **Optimiser** (PATH 8) → constrained load-balancing action  
4. **Simulation** (PATH 9) → counterfactual validation  
    """)
    with st.expander("Raw optimisation context"):
        st.json(ctx["optimization"])

# ── TAB 5: Simulation ─────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("<div class='section-title'>Baseline vs Simulated Optimised</div>", unsafe_allow_html=True)
    sim = ctx["simulation"]
    s1, s2 = st.columns(2)
    s1.metric("Curtailment (MWh)", f"{sim['optimized_curtailment_mwh']:.2f}",
              f"{sim['curtailment_difference_mwh']:+.2f} MWh", delta_color="inverse")
    s2.metric("Overload Intervals", str(sim["optimized_overload_intervals"]),
              f"{sim['optimized_overload_intervals'] - sim['baseline_overload_intervals']:+d}",
              delta_color="inverse")
    if sim["adverse_counterfactual"]:
        st.error("⚠️ **ADVERSE COUNTERFACTUAL**: Optimised scenario performs worse than baseline under realised conditions. Operator approval required.")

# ── TAB 6: Operator Brief ─────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("<div class='section-title'>AI Operator Brief (PATH 10)</div>", unsafe_allow_html=True)
    st.markdown(render_deterministic_brief(ctx))

# ──────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption("GridPulse AI · Frontend branch · ML predicts → Optimiser recommends → Simulation validates → Human operator decides")
