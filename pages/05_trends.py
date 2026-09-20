"""Page 05: Statistical Process Control, Time-Series & Trend Analysis.
Features:
- Shewhart SPC Run Charts (Center line, 3-sigma UCL/LCL, 2-sigma warning bands)
- Period-over-Period (MoM / YoY) growth velocity
- Special-cause outlier detection and volatility analysis
- Plain-English trend interpretation with statistical assumption warnings
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from core.constants import WorkflowStage
from core.state import init_session_state, get_working_df, advance_workflow_stage
from modules.analysis.stats_engine import calculate_control_chart_limits, calculate_descriptive_stats

init_session_state()

st.title("📈 Stage 7 & 9: Time-Series & Statistical Process Control")
st.markdown("Evaluate process stability, longitudinal trends, and special-cause variation over time.")

df = get_working_df()
if df is None:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

confirmed = st.session_state.get("confirmed_mappings", {})

# Identify Date & Metric Columns
date_cols = [c for c, r in confirmed.items() if r in ["date", "reporting_period"]]
if not date_cols:
    date_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["date", "month", "period", "timestamp", "time"])]

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if not date_cols or not num_cols:
    st.info("ℹ️ Longitudinal time-series analysis requires at least one chronological date/period column and one numeric metric column.")
    st.stop()

# Selection Controls
c_s1, c_s2, c_s3 = st.columns(3)
with c_s1:
    date_col = st.selectbox("Chronological Date / Period Column", date_cols)
with c_s2:
    metric_col = st.selectbox("Performance Metric Column", num_cols)
with c_s3:
    agg_choice = st.selectbox("Aggregation Method", ["mean", "sum"])

# Compute SPC Run Chart Table
spc_df = calculate_control_chart_limits(df, date_col, metric_col, agg_choice)
st.session_state.trend_summary = spc_df

if spc_df.empty:
    st.warning("Could not compute time series for selected columns.")
    st.stop()

# Plot Interactive Shewhart SPC Run Chart
st.subheader(f"📊 Statistical Process Control (SPC) Run Chart: {metric_col}")

fig = go.Figure()

# Actual Series
fig.add_trace(go.Scatter(
    x=spc_df[date_col],
    y=spc_df[metric_col],
    mode="lines+markers",
    name="Observed Metric",
    line=dict(color="#0d6efd", width=2.5),
    marker=dict(size=7)
))

# Center Line
fig.add_trace(go.Scatter(
    x=spc_df[date_col],
    y=spc_df["center_line"],
    mode="lines",
    name="Process Mean (Center Line)",
    line=dict(color="#198754", dash="dash", width=2)
))

# Upper Control Limit (UCL 3-Sigma)
fig.add_trace(go.Scatter(
    x=spc_df[date_col],
    y=spc_df["ucl_3sigma"],
    mode="lines",
    name="UCL (Mean + 3σ)",
    line=dict(color="#dc3545", dash="dot", width=1.5)
))

# Lower Control Limit (LCL 3-Sigma)
fig.add_trace(go.Scatter(
    x=spc_df[date_col],
    y=spc_df["lcl_3sigma"],
    mode="lines",
    name="LCL (Mean - 3σ)",
    line=dict(color="#dc3545", dash="dot", width=1.5)
))

# Highlight Special Cause Outliers
special_points = spc_df[spc_df["is_special_cause"] == True]
if not special_points.empty:
    fig.add_trace(go.Scatter(
        x=special_points[date_col],
        y=special_points[metric_col],
        mode="markers",
        name="🚨 Special Cause (>3σ)",
        marker=dict(color="#dc3545", size=12, symbol="triangle-up")
    ))

fig.update_layout(
    title=f"Process Stability & Control Limits for {metric_col}",
    xaxis_title=date_col,
    yaxis_title=f"{metric_col} ({agg_choice})",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# Trend Summary KPI Cards
st.markdown("---")
c_k1, c_k2, c_k3, c_k4 = st.columns(4)

center_val = float(spc_df["center_line"].iloc[0])
latest_val = float(spc_df[metric_col].iloc[-1])
first_val = float(spc_df[metric_col].iloc[0])
total_change_pct = ((latest_val - first_val) / max(first_val, 0.001)) * 100.0
special_count = int(spc_df["is_special_cause"].sum())

with c_k1:
    st.metric("Process Baseline Mean", f"{center_val:,.2f}")
with c_k2:
    st.metric("Latest Period Value", f"{latest_val:,.2f}")
with c_k3:
    st.metric("Overall Trajectory", f"{total_change_pct:+.1f}%")
with c_k4:
    st.metric("Special Cause Outliers", f"{special_count} Periods", delta=None)

# Plain-English Trend Interpretation
st.markdown("---")
st.subheader("💡 Plain-English Operational Interpretation")
if special_count == 0:
    st.success(f"✅ **Stable Process:** Performance in `{metric_col}` is operating in statistical control within normal ±3σ common-cause variation bounds.")
else:
    st.warning(f"⚠️ **Process Instability Detected:** {special_count} reporting period(s) breached the 3-sigma Upper/Lower control limits. These represent special-cause operational events (e.g. system outages, sudden demand surges, policy shifts) that warrant root-cause investigation.")

# Statistical Assumptions & Limitations Disclosure
with st.expander("🛡️ Statistical Assumptions & Time-Series Limitations", expanded=False):
    st.markdown("""
    - **Equally Spaced Intervals:** Control chart algorithms assume uniform sampling frequency across periods.
    - **Normality Approximation:** 3-sigma control limits utilize standard deviation bounds which assume approximately normal error distributions.
    - **Association vs Causation:** Period-over-period improvements reflect observed temporal patterns and do not establish causal intervention impact without longitudinal regression controls.
    """)

st.markdown("---")
if st.button("Proceed to Stage 8 (Comparisons & Cohorts) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_09_TRENDS)
    st.success("Trend analysis stage completed.")
