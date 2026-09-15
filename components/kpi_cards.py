"""
components/kpi_cards.py
Reusable KPI card helpers for the GridPulse AI dashboard.
"""

import streamlit as st


def render_kpi(col, label: str, value: str, sub: str = "", accent: str = "#0f62fe") -> None:
    """Render a single KPI card inside *col* (a Streamlit column)."""
    col.markdown(
        f"""
        <div style="
            background:#1a1a2e;
            padding:18px 22px;
            border-radius:6px;
            border-left:4px solid {accent};
            margin-bottom:16px;
        ">
            <div style="font-size:0.78rem;color:#a8b0bc;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{label}</div>
            <div style="font-size:1.65rem;font-weight:700;color:#e8eaed">{value}</div>
            <div style="font-size:0.72rem;color:#6c7a8d;margin-top:2px">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(cols: list, items: list) -> None:
    """
    Render multiple KPI cards in one go.

    Parameters
    ----------
    cols  : list of Streamlit column objects
    items : list of dicts with keys: label, value, sub (optional), accent (optional)
    """
    for col, item in zip(cols, items):
        render_kpi(
            col,
            label=item["label"],
            value=item["value"],
            sub=item.get("sub", ""),
            accent=item.get("accent", "#0f62fe"),
        )


def risk_accent(risk_level: str) -> str:
    """Return a colour accent based on the risk level string."""
    mapping = {
        "LOW":    "#24a148",
        "MEDIUM": "#f1c21b",
        "HIGH":   "#da1e28",
        "CRITICAL": "#ff4444",
    }
    return mapping.get(risk_level.upper(), "#0f62fe")
