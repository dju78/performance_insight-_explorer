"""Visualisation Layer for Performance Insight Explorer.
Builds accessible, publication-ready Plotly charts with clear labels, units, and interactive tooltips.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Professional Color Palette
COLOR_PRIMARY = "#1E3A8A"      # Deep Navy
COLOR_SECONDARY = "#0284C7"    # Sky Blue
COLOR_ACCENT = "#D97706"       # Amber
COLOR_SUCCESS = "#10B981"      # Emerald
COLOR_DANGER = "#EF4444"       # Red
COLOR_NEUTRAL = "#6B7280"      # Slate Gray


def create_trend_chart(
    trend_df: pd.DataFrame,
    x_col: str = "period",
    y_col: str = "value",
    title: str = "Performance Trend Over Time",
    y_label: str = "Value",
    show_rolling: bool = True
) -> go.Figure:
    """Create clean, interactive time-series line chart with optional rolling average."""
    fig = go.Figure()
    
    # Main trend line
    fig.add_trace(go.Scatter(
        x=trend_df[x_col],
        y=trend_df[y_col],
        mode="lines+markers",
        name="Actual Value",
        line=dict(color=COLOR_PRIMARY, width=3),
        marker=dict(size=6, color=COLOR_PRIMARY),
        hovertemplate="<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>"
    ))
    
    # Optional rolling mean
    if show_rolling and "rolling_3_mean" in trend_df.columns:
        fig.add_trace(go.Scatter(
            x=trend_df[x_col],
            y=trend_df["rolling_3_mean"],
            mode="lines",
            name="3-Period Rolling Mean",
            line=dict(color=COLOR_ACCENT, width=2, dash="dot"),
            hovertemplate="<b>%{x}</b><br>3-Period Mean: %{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1F2937")),
        xaxis=dict(title="Reporting Period", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#E5E7EB"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified"
    )
    return fig


def create_comparison_bar(
    comp_df: pd.DataFrame,
    x_col: str = "group",
    y_col: str = "mean",
    title: str = "Group Performance Comparison",
    x_label: str = "Group",
    y_label: str = "Performance Measure",
    target_val: Optional[float] = None
) -> go.Figure:
    """Create ranked comparison bar chart with optional benchmark standard line."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=comp_df[x_col],
        y=comp_df[y_col],
        name="Group Output",
        marker=dict(color=COLOR_SECONDARY),
        hovertemplate="<b>%{x}</b><br>" + f"{y_label}: %{{y:,.2f}}<extra></extra>"
    ))
    
    if target_val is not None:
        fig.add_hline(
            y=target_val,
            line_dash="dash",
            line_color=COLOR_DANGER,
            annotation_text=f"Benchmark ({target_val:.1f})",
            annotation_position="top right"
        )
        
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1F2937")),
        xaxis=dict(title=x_label, tickangle=-25),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#E5E7EB"),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=50)
    )
    return fig


def create_distribution_histogram(
    df: pd.DataFrame,
    val_col: str,
    title: str = "Value Distribution",
    x_label: str = "Value",
    nbins: int = 25
) -> go.Figure:
    """Create distribution histogram with mean and median reference lines."""
    s_clean = pd.to_numeric(df[val_col], errors="coerce").dropna()
    mean_val = float(s_clean.mean()) if len(s_clean) > 0 else 0.0
    med_val = float(s_clean.median()) if len(s_clean) > 0 else 0.0
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=s_clean,
        nbinsx=nbins,
        marker=dict(color=COLOR_PRIMARY, line=dict(color="white", width=1)),
        name="Count"
    ))
    
    fig.add_vline(x=mean_val, line_dash="solid", line_color=COLOR_ACCENT, annotation_text=f"Mean ({mean_val:.1f})", annotation_position="top left")
    fig.add_vline(x=med_val, line_dash="dash", line_color=COLOR_SUCCESS, annotation_text=f"Median ({med_val:.1f})", annotation_position="top right")
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1F2937")),
        xaxis=dict(title=x_label, showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title="Observation Frequency", showgrid=True, gridcolor="#E5E7EB"),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def create_box_plot(
    df: pd.DataFrame,
    val_col: str,
    group_col: Optional[str] = None,
    title: str = "Outlier & Quartile Box Plot",
    y_label: str = "Value"
) -> go.Figure:
    """Create box plot showing quartiles, median, and outlier observations."""
    if group_col and group_col in df.columns:
        fig = px.box(
            df,
            x=group_col,
            y=val_col,
            color=group_col,
            points="all",
            title=title,
            template="plotly_white"
        )
    else:
        fig = px.box(
            df,
            y=val_col,
            points="all",
            title=title,
            template="plotly_white"
        )
        
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1F2937")),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#E5E7EB"),
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False
    )
    return fig


def create_scatter_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "Relationship & Association Analysis",
    x_label: str = "Independent Variable",
    y_label: str = "Dependent Variable"
) -> go.Figure:
    """Create scatter plot with trendline and prominent correlation disclaimer."""
    sub_df = df[[x_col, y_col]].dropna()
    sub_df[x_col] = pd.to_numeric(sub_df[x_col], errors="coerce")
    sub_df[y_col] = pd.to_numeric(sub_df[y_col], errors="coerce")
    sub_df = sub_df.dropna()
    
    fig = px.scatter(
        sub_df,
        x=x_col,
        y=y_col,
        trendline="ols",
        title=title,
        template="plotly_white"
    )
    
    fig.update_traces(marker=dict(size=8, color=COLOR_PRIMARY, opacity=0.7))
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1F2937")),
        xaxis=dict(title=x_label, showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title=y_label, showgrid=True, gridcolor="#E5E7EB"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def create_gauge_kpi(
    value: float,
    title: str = "Target Achievement",
    target_val: float = 100.0,
    unit: str = "%"
) -> go.Figure:
    """Create radial gauge chart for target performance or utilization."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"<b>{title}</b><br><span style='font-size:12px;color:gray'>Benchmark: {target_val}{unit}</span>", "font": {"size": 14}},
        delta={"reference": target_val, "increasing": {"color": COLOR_SUCCESS}, "decreasing": {"color": COLOR_DANGER}},
        gauge={
            "axis": {"range": [0, max(150, value * 1.2)], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": COLOR_PRIMARY},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, target_val * 0.8], "color": "#FEE2E2"},
                {"range": [target_val * 0.8, target_val], "color": "#FEF3C7"},
                {"range": [target_val, max(150, value * 1.2)], "color": "#DCFCE7"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": target_val
            }
        }
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return fig
