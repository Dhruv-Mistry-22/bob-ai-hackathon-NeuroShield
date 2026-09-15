"""
components/alert_banners.py
Safety flag banner renderer for the GridPulse AI dashboard.
GREEN / YELLOW / RED banners with operator guidance.
"""

import streamlit as st

_STYLES = {
    "GREEN":  ("rgba(36,161,72,0.15)",  "#24a148", "#6ef09a", "🟢 GREEN — NORMAL OPERATION"),
    "YELLOW": ("rgba(241,194,27,0.15)", "#f1c21b", "#f5d76e", "🟡 YELLOW — OPERATOR REVIEW REQUIRED"),
    "RED":    ("rgba(218,30,40,0.15)",  "#da1e28", "#ff8389", "🔴 RED — OPERATOR APPROVAL REQUIRED"),
}


def render_banner(flag: str, explanation: str) -> None:
    """
    Render a colour-coded safety banner.

    Parameters
    ----------
    flag        : one of 'GREEN', 'YELLOW', 'RED'
    explanation : human-readable explanation text from the operator brief
    """
    bg, border, text_color, heading = _STYLES.get(
        flag.upper(), ("rgba(100,100,100,0.15)", "#888", "#ccc", f"⚪ {flag}")
    )
    st.markdown(
        f"""
        <div style="
            padding:14px 18px;
            border-radius:5px;
            margin:8px 0 18px;
            font-size:.92rem;
            font-weight:500;
            line-height:1.5;
            background:{bg};
            border:1px solid {border};
            color:{text_color};
        ">
            <b>{heading}</b><br>{explanation}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_disclaimer() -> None:
    """Render the persistent decision-support disclaimer."""
    st.markdown(
        """
        <div style="
            padding:10px 16px;
            border-radius:4px;
            background:rgba(55,55,70,0.5);
            border:1px solid #444;
            font-size:.82rem;
            color:#a0a8b4;
            margin-bottom:14px;
        ">
            ⚠️ <b>DECISION SUPPORT ONLY</b> — GridPulse AI does not execute grid-control commands.
            All recommendations require operator review and approval.
        </div>
        """,
        unsafe_allow_html=True,
    )
