"""
utils/context_builder.py
Thin wrapper around PATH-10 operator_brief helpers.
Adds caching and a fallback mechanism so the UI never hard-crashes.
"""

import streamlit as st
import dateutil.parser
from datetime import timedelta
from typing import Optional


def get_demo_timestamp(data: dict, scenario: str, zone: str, build_fn) -> Optional[str]:
    """
    Walk the simulation output to find a timestamp that matches the
    requested scenario characteristics.

    Parameters
    ----------
    data       : dict of pipeline DataFrames
    scenario   : scenario label string
    zone       : zone_id string
    build_fn   : callable — build_operator_context(data, ts, zone)

    Returns
    -------
    ISO timestamp string, or None if not found.
    """
    for _, row in data["sim"].iterrows():
        if row["zone_id"] != zone:
            continue
        ts_dec = (
            dateutil.parser.parse(row["target_timestamp"]) - timedelta(minutes=60)
        ).strftime("%Y-%m-%d %H:%M:%S")
        try:
            ctx = build_fn(data, ts_dec, zone)
        except Exception:
            continue

        flag = ctx["operator_decision"]["decision_flag"]
        adv  = ctx["simulation"]["adverse_counterfactual"]

        if scenario == "Demo A – Normal" and flag == "GREEN":
            return ts_dec
        if scenario == "Demo B – High Stress" and flag in ("YELLOW", "RED") and not adv:
            return ts_dec
        if scenario == "Demo C – Adverse Counterfactual" and flag == "RED" and adv:
            return ts_dec

    return None


@st.cache_data(show_spinner=False, ttl=30)
def cached_context(data_key: str, ts: str, zone: str, _build_fn, _data: dict) -> dict:
    """
    Cache the operator context to avoid redundant recomputation on reruns.
    `data_key` is a lightweight hash-like key so Streamlit can detect staleness.
    """
    return _build_fn(_data, ts, zone)
