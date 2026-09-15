"""
pages/1_Asset_Health.py
Standalone Streamlit page: Renewable Asset Health deep-dive.
Accessible via the Streamlit multi-page sidebar when running app.py.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, sys

sys.path.append(os.path.abspath("src"))

st.set_page_config(page_title="Asset Health | GridPulse AI", layout="wide")
st.title("🔧 Renewable Asset Health")
st.caption("Deep-dive into anomaly scores and root-cause diagnostics for each tracked asset.")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading asset data…")
def _load():
    try:
        anomaly    = pd.read_csv("outputs/anomaly_model/current_asset_status.csv")
        root_cause = pd.read_csv("outputs/root_cause/root_cause_predictions.csv")
        return anomaly, root_cause
    except FileNotFoundError as e:
        st.error(f"Missing file: {e}")
        st.stop()

anomaly_df, root_cause_df = _load()

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])
asset_type_opts = ["All"] + sorted(anomaly_df["asset_type"].unique().tolist()) if "asset_type" in anomaly_df.columns else ["All"]
selected_type   = col_f1.selectbox("Asset Type", asset_type_opts)
show_anomalies  = col_f2.checkbox("Show anomalies only", value=False)

filtered = anomaly_df.copy()
if selected_type != "All" and "asset_type" in filtered.columns:
    filtered = filtered[filtered["asset_type"] == selected_type]
if show_anomalies and "anomaly_label" in filtered.columns:
    filtered = filtered[filtered["anomaly_label"] != "NORMAL"]

# ── Anomaly score scatter ─────────────────────────────────────────────────────
st.subheader("Anomaly Scores by Asset")
if "anomaly_score" in filtered.columns and "asset_id" in filtered.columns:
    color_map = {"NORMAL": "#24a148", "ANOMALY": "#da1e28", "WARNING": "#f1c21b"}
    colors = filtered["anomaly_label"].map(color_map).fillna("#6c7a8d").tolist() if "anomaly_label" in filtered.columns else ["#0f62fe"] * len(filtered)

    fig = go.Figure(go.Scatter(
        x=filtered["asset_id"],
        y=filtered["anomaly_score"],
        mode="markers",
        marker=dict(color=colors, size=11, line=dict(width=1, color="#222")),
        text=filtered.get("anomaly_label", pd.Series([""] * len(filtered))),
        hovertemplate="<b>%{x}</b><br>Score: %{y:.4f}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", height=360,
        xaxis_title="Asset ID", yaxis_title="Anomaly Score",
        margin=dict(l=40, r=20, t=30, b=60),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Required columns (asset_id, anomaly_score) not found in anomaly data.")

# ── Asset table ───────────────────────────────────────────────────────────────
st.subheader("Asset Status Table")
st.dataframe(filtered, use_container_width=True, hide_index=True)

# ── Root cause ────────────────────────────────────────────────────────────────
st.subheader("Root-Cause Diagnostics")
if not root_cause_df.empty:
    st.dataframe(root_cause_df, use_container_width=True, hide_index=True)
else:
    st.info("No root-cause records available.")

st.divider()
st.caption("GridPulse AI · Asset Health page · Frontend branch")
