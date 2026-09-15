"""
pages/2_Forecast_Explorer.py
Standalone Streamlit page: 60-minute forecast explorer with zone comparison.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, sys

sys.path.append(os.path.abspath("src"))

st.set_page_config(page_title="Forecast Explorer | GridPulse AI", layout="wide")
st.title("📈 Forecast Explorer")
st.caption("Explore demand and renewable forecasts across all zones and time windows.")

@st.cache_data(show_spinner="Loading forecast data…")
def _load():
    try:
        demand    = pd.read_csv("outputs/demand_model/demand_predictions.csv")
        renewable = pd.read_csv("outputs/renewable_model/renewable_predictions.csv")
        return demand, renewable
    except FileNotFoundError as e:
        st.error(f"Missing file: {e}")
        st.stop()

demand_df, renewable_df = _load()

# ── Controls ──────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
zones          = sorted(demand_df["zone_id"].unique().tolist()) if "zone_id" in demand_df.columns else []
selected_zones = c1.multiselect("Zones to compare", zones, default=zones[:3] if len(zones) >= 3 else zones)
metric         = c2.radio("Metric", ["Demand (MW)", "Renewables (MW)"], horizontal=True)

# ── Chart ─────────────────────────────────────────────────────────────────────
st.subheader(f"{metric} — Zone Comparison")

fig = go.Figure()
df_src = demand_df if "Demand" in metric else renewable_df
y_col  = "predicted_demand_mw" if "Demand" in metric else "predicted_renewable_mw"
ts_col = "target_timestamp" if "target_timestamp" in df_src.columns else df_src.columns[0]

COLORS = ["#0f62fe", "#6929c4", "#24a148", "#f1c21b", "#da1e28", "#08bdba"]
for i, zone in enumerate(selected_zones):
    zone_df = df_src[df_src["zone_id"] == zone].copy() if "zone_id" in df_src.columns else df_src.copy()
    if y_col not in zone_df.columns:
        continue
    zone_df = zone_df.sort_values(ts_col) if ts_col in zone_df.columns else zone_df
    fig.add_trace(go.Scatter(
        x=zone_df[ts_col] if ts_col in zone_df.columns else zone_df.index,
        y=zone_df[y_col],
        name=zone,
        mode="lines",
        line=dict(color=COLORS[i % len(COLORS)], width=2),
    ))

fig.update_layout(
    template="plotly_dark",
    height=420,
    xaxis_title="Timestamp",
    yaxis_title=metric,
    legend=dict(orientation="h", y=1.08),
    margin=dict(l=40, r=20, t=40, b=60),
)
st.plotly_chart(fig, use_container_width=True)

# ── Raw table ─────────────────────────────────────────────────────────────────
with st.expander("📄 Raw forecast data"):
    st.dataframe(df_src, use_container_width=True, hide_index=True)

st.divider()
st.caption("GridPulse AI · Forecast Explorer page · Frontend branch")
