"""
components/sidebar.py
Sidebar builder for the GridPulse AI dashboard.
Centralises all sidebar controls so app.py stays lean.
"""

import streamlit as st
import pandas as pd
from typing import Tuple


def render_sidebar(data: dict) -> Tuple[str, str]:
    """
    Render the full sidebar and return (selected_zone, selected_scenario).

    Parameters
    ----------
    data : dict of DataFrames loaded from pipeline outputs

    Returns
    -------
    selected_zone     : str  zone_id chosen by the operator
    selected_scenario : str  one of the scenario labels
    """
    with st.sidebar:
        # Logo / branding
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>"
            "<span style='font-size:1.8rem'>⚡</span>"
            "<span style='font-size:1.1rem;font-weight:700;color:#e8eaed'>GridPulse AI</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Operator Dashboard · v2.0 · Frontend branch")
        st.divider()

        # Zone picker
        zones = sorted(data["demand"]["zone_id"].unique().tolist())
        selected_zone = st.selectbox("📍 Grid Zone", zones, help="Select the transmission zone to monitor.")

        st.divider()

        # Scenario picker
        scenarios = [
            "Live / Latest",
            "Demo A – Normal",
            "Demo B – High Stress",
            "Demo C – Adverse Counterfactual",
        ]
        selected_scenario = st.radio(
            "🎭 Scenario",
            scenarios,
            index=0,
            help="Switch between live data and pre-loaded demo scenarios.",
        )

        st.divider()

        # Info panel
        with st.expander("ℹ️ About"):
            st.markdown(
                """
**GridPulse AI** is a decision-support system for grid operators.

- Forecasts demand & renewables up to **60 minutes ahead**
- Detects **asset anomalies** via hybrid ML
- Proposes **constrained optimisation** actions
- Validates via **counterfactual simulation**
- Surfaces a deterministic **operator brief**

*Not for autonomous grid control.*
                """
            )

        st.markdown(
            "<div style='font-size:.75rem;color:#555;text-align:center;margin-top:20px'>"
            "Kakkad Priyansh · frontend branch"
            "</div>",
            unsafe_allow_html=True,
        )

    return selected_zone, selected_scenario
