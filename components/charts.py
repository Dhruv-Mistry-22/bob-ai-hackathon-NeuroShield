"""
components/charts.py
Plotly chart factory for the GridPulse AI dashboard.
All charts use the plotly_dark template to match the control-room theme.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional


PALETTE = {
    "blue":   "#0f62fe",
    "purple": "#6929c4",
    "green":  "#24a148",
    "yellow": "#f1c21b",
    "red":    "#da1e28",
    "grey":   "#6c7a8d",
}


def observed_vs_forecast_bar(
    categories: list[str],
    observed: list[float],
    forecast: list[float],
    title: str = "Observed vs Forecast (+60 min)",
) -> go.Figure:
    """Grouped bar chart comparing observed vs forecast values."""
    fig = go.Figure(data=[
        go.Bar(name="Observed (t)",    x=categories, y=observed, marker_color=PALETTE["blue"]),
        go.Bar(name="Forecast (t+60)", x=categories, y=forecast, marker_color=PALETTE["purple"]),
    ])
    fig.update_layout(
        title=title,
        barmode="group",
        template="plotly_dark",
        height=380,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def asset_health_scatter(
    df: pd.DataFrame,
    asset_col: str = "asset_id",
    score_col: str = "anomaly_score",
    label_col: Optional[str] = "anomaly_label",
    title: str = "Asset Anomaly Scores",
) -> go.Figure:
    """Scatter plot of asset anomaly scores with colour-coded status."""
    colors = []
    if label_col and label_col in df.columns:
        color_map = {"NORMAL": PALETTE["green"], "ANOMALY": PALETTE["red"], "WARNING": PALETTE["yellow"]}
        colors = df[label_col].map(color_map).fillna(PALETTE["grey"]).tolist()
    else:
        colors = [PALETTE["blue"]] * len(df)

    fig = go.Figure(go.Scatter(
        x=df[asset_col],
        y=df[score_col],
        mode="markers",
        marker=dict(color=colors, size=10, line=dict(width=1, color="#222")),
        text=df[label_col] if label_col and label_col in df.columns else None,
    ))
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=340,
        xaxis_title="Asset",
        yaxis_title="Anomaly Score",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def simulation_comparison_bar(
    baseline_curtailment: float,
    optimised_curtailment: float,
    baseline_overloads: int,
    optimised_overloads: int,
) -> go.Figure:
    """Side-by-side bar comparing baseline vs optimised simulation outcomes."""
    fig = go.Figure(data=[
        go.Bar(
            name="Baseline",
            x=["Curtailment (MWh)", "Overload Intervals"],
            y=[baseline_curtailment, baseline_overloads],
            marker_color=PALETTE["grey"],
        ),
        go.Bar(
            name="Optimised",
            x=["Curtailment (MWh)", "Overload Intervals"],
            y=[optimised_curtailment, optimised_overloads],
            marker_color=PALETTE["blue"],
        ),
    ])
    fig.update_layout(
        title="Baseline vs Simulated Optimised",
        barmode="group",
        template="plotly_dark",
        height=340,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig
