import streamlit as st
import pandas as pd
import numpy as np
import dateutil.parser
from datetime import timedelta
import os
import sys

# Add src to path so we can import from PATH 10
sys.path.append(os.path.abspath('src'))
from operator_brief import get_latest_valid_timestamp, build_operator_context, render_deterministic_brief

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="GridPulse AI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for control room style
st.markdown("""
<style>
    .kpi-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #0f62fe;
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 0.9rem;
        color: #c6c6c6;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff;
    }
    .status-green { color: #24a148; font-weight: bold; }
    .status-yellow { color: #f1c21b; font-weight: bold; }
    .status-red { color: #da1e28; font-weight: bold; }
    
    .alert-banner {
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-weight: 500;
    }
    .alert-green { background-color: rgba(36, 161, 72, 0.2); border: 1px solid #24a148; }
    .alert-yellow { background-color: rgba(241, 194, 27, 0.2); border: 1px solid #f1c21b; }
    .alert-red { background-color: rgba(218, 30, 40, 0.2); border: 1px solid #da1e28; color: #ff8389; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# DATA LOADING (CACHED)
# -----------------------------------------
@st.cache_data
def load_data():
    try:
        data_dicts = {
            'demand': pd.read_csv('outputs/demand_model/demand_predictions.csv'),
            'renewable': pd.read_csv('outputs/renewable_model/renewable_predictions.csv'),
            'anomaly': pd.read_csv('outputs/anomaly_model/current_asset_status.csv'),
            'root_cause': pd.read_csv('outputs/root_cause/root_cause_predictions.csv'),
            'grid_risk': pd.read_csv('outputs/grid_risk/grid_risk_predictions.csv'),
            'opt': pd.read_csv('outputs/optimization/optimization_actions.csv'),
            'sim': pd.read_csv('outputs/simulation/baseline_vs_optimized.csv')
        }
        return data_dicts
    except FileNotFoundError as e:
        st.error(f"❌ Required GridPulse output missing: {e}")
        st.stop()

data_dicts = load_data()

# -----------------------------------------
# HEADER
# -----------------------------------------
st.title("GRIDPULSE AI")
st.markdown("**Grid Load Optimisation & Renewable Energy Performance Advisor**")
st.caption("Forecast. Detect. Explain. Optimize. Simulate. Support operator decisions.")
st.markdown("<div class='alert-banner' style='background-color:#333; border: 1px solid #555;'>⚠️ **DECISION SUPPORT — HUMAN APPROVAL REQUIRED**<br>GridPulse AI is a decision-support system. Recommendations are not automatically executed. Baseline-vs-optimized results are counterfactual simulation estimates, not verified historical operational savings.</div>", unsafe_allow_html=True)

# -----------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------
st.sidebar.header("Controls")

# Zone Selection
zones = data_dicts['demand']['zone_id'].unique().tolist()
# Note: Re: ALL zone aggregation. Due to strict topological constraints on transmission and risk categories, 
# full 'ALL' zone aggregation for this dashboard MVP is restricted to avoid mathematically invalid averages.
# We will only support explicit zones as the optimization pipeline processes per-zone.
selected_zone = st.sidebar.selectbox("Select Zone", zones)

# Timestamp Logic
latest_ts = get_latest_valid_timestamp(data_dicts)

# Scenario Selectors (Demo Mode)
scenario = st.sidebar.radio("Select Scenario", [
    "Live / Latest",
    "Demo A: Normal",
    "Demo B: High Stress",
    "Demo C: Adverse Counterfactual"
])

def get_demo_timestamp(scenario_name, zone_id):
    # Crawl history for exact match just like PATH 10
    sim = data_dicts['sim']
    for i, sim_row in sim.iterrows():
        if sim_row['zone_id'] != zone_id: continue
        ts_target = sim_row['target_timestamp']
        ts_decision = (dateutil.parser.parse(ts_target) - timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
        try:
            ctx = build_operator_context(data_dicts, ts_decision, zone_id)
        except Exception:
            continue
        
        flag = ctx['operator_decision']['decision_flag']
        has_adv = ctx['simulation']['adverse_counterfactual']
        
        if scenario_name == "Demo A: Normal" and flag == 'GREEN': return ts_decision
        if scenario_name == "Demo B: High Stress" and flag in ['YELLOW', 'RED'] and not has_adv: return ts_decision
        if scenario_name == "Demo C: Adverse Counterfactual" and flag == 'RED' and has_adv: return ts_decision
    return None

if scenario == "Live / Latest":
    selected_ts = latest_ts
else:
    demo_ts = get_demo_timestamp(scenario, selected_zone)
    if demo_ts is None:
        st.sidebar.warning(f"Scenario not found for {selected_zone}. Falling back to Live.")
        selected_ts = latest_ts
    else:
        selected_ts = demo_ts

# Generate Context using PATH 10 Engine
try:
    context = build_operator_context(data_dicts, selected_ts, selected_zone)
except Exception as e:
    st.error(f"Error building context for {selected_ts} / {selected_zone}: {e}")
    st.stop()

# -----------------------------------------
# SAFETY BANNER
# -----------------------------------------
flag = context['operator_decision']['decision_flag']
explanation = context['operator_decision']['explanation']

if flag == 'GREEN':
    st.markdown(f"<div class='alert-banner alert-green'>🟢 GREEN — NORMAL OPERATION<br>{explanation}</div>", unsafe_allow_html=True)
elif flag == 'YELLOW':
    st.markdown(f"<div class='alert-banner alert-yellow'>🟡 YELLOW — OPERATOR REVIEW<br>{explanation}</div>", unsafe_allow_html=True)
elif flag == 'RED':
    st.markdown(f"<div class='alert-banner alert-red'>🔴 RED — OPERATOR APPROVAL REQUIRED<br>{explanation}</div>", unsafe_allow_html=True)

# -----------------------------------------
# TOP KPI CARDS
# -----------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)
def kpi(col, title, val):
    col.markdown(f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{val}</div></div>", unsafe_allow_html=True)

kpi(col1, "Current Demand", f"{context['current_state']['demand_mw']:.1f} MW")
kpi(col2, "Current Renewables", f"{context['current_state']['renewable_mw']:.1f} MW")
kpi(col3, "Transmission Util", f"{context['current_state']['transmission_utilization_pct']*100:.1f}%")
kpi(col4, "Grid Risk", f"{context['grid_forecast']['transmission_risk']}")
kpi(col5, "Current Curtailment", f"{context['current_state']['curtailment_mw']:.1f} MW")

# -----------------------------------------
# TABS
# -----------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", "Forecast", "Asset Health", "Optimization", "Before vs After", "AI Operator Brief"
])

with tab1:
    st.subheader("Next 60 Minutes (t+60)")
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Predicted Demand", f"{context['demand_forecast']['predicted_demand_60m']:.1f} MW")
    kpi(c2, "Predicted Renewables", f"{context['renewable_forecast']['renewable_60m']:.1f} MW")
    kpi(c3, "Predicted Risk", f"{context['grid_forecast']['transmission_risk']}")
    kpi(c4, "Curtailment Risk", f"{context['grid_forecast']['curtailment_probability']:.0%}")
    
    st.subheader("Recommended Action (PATH 8)")
    action_mw = context['optimization']['action_mw']
    if action_mw > 0:
        st.info(f"**Action:** {context['optimization']['action']} ({context['optimization']['resource_type']}) - **{action_mw:.1f} MW**")
        st.write(f"**Reason:** {context['optimization']['reason']}")
    else:
        st.success("NO ACTION RECOMMENDED.")

with tab2:
    st.subheader("60-Minute Forecast Details")
    import plotly.graph_objects as go
    
    # We will just plot a simple point for now since full historical timeseries chart is complex
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Demand', 'Renewables', 'Curtailment'], 
                         y=[context['current_state']['demand_mw'], context['current_state']['renewable_mw'], context['current_state']['curtailment_mw']],
                         name='Observed (t)'))
    fig.add_trace(go.Bar(x=['Demand', 'Renewables', 'Curtailment'], 
                         y=[context['demand_forecast']['predicted_demand_60m'], context['renewable_forecast']['renewable_60m'], context['grid_forecast']['curtailment_predicted_mw']],
                         name='Forecast (t+60)'))
    fig.update_layout(title="Observed vs Forecast (+60m)", barmode='group', template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
    
with tab3:
    st.subheader("Renewable Asset Health (PATH 5 & 6)")
    if context['asset_alerts']:
        df_alerts = pd.DataFrame(context['asset_alerts'])
        st.dataframe(df_alerts, use_container_width=True)
    else:
        st.success("No critical or anomalous assets detected.")

with tab4:
    st.subheader("Why this recommendation? (Explainability)")
    st.markdown("""
    **Deterministic Logic Chain:**
    1. **Demand Forecast (PATH 3)** + **Renewable Forecast (PATH 4)**
    2. Determines **Grid Risk (PATH 7)**
    3. Triggers **Optimization Action (PATH 8)**
    4. Validated by **Simulation (PATH 9)**
    """)
    st.write(context['optimization'])

with tab5:
    st.subheader("Baseline vs Simulated Optimized (PATH 9)")
    sim = context['simulation']
    
    c1, c2 = st.columns(2)
    c1.metric("Curtailment (MWh)", f"{sim['optimized_curtailment_mwh']:.2f}", f"{sim['curtailment_difference_mwh']:+.2f} MWh", delta_color="inverse")
    c2.metric("Overload Intervals", f"{sim['optimized_overload_intervals']}", f"{sim['optimized_overload_intervals'] - sim['baseline_overload_intervals']:+d} intervals", delta_color="inverse")
    
    if sim['adverse_counterfactual']:
        st.error("⚠️ **ADVERSE COUNTERFACTUAL DETECTED**: The simulated optimized state performs worse than the historical baseline under realized conditions. Operator approval required.")

with tab6:
    st.subheader("AI Operator Brief (PATH 10)")
    md = render_deterministic_brief(context)
    st.markdown(md)

st.markdown("---")
st.caption("GridPulse AI | ML predicts → Optimizer recommends → Simulation validates → AI explains → Human operator decides")
