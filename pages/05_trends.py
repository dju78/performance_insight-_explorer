import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.trends import calculate_trends
from src.visualisations import create_trend_chart

init_session_state()

st.title("⏱️ 05. Trend Analysis & Time Dynamics")
st.caption("Chronological time-series trajectories, period-over-period changes, peaks, troughs, and trajectory classification.")

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})

if df is None:
    st.warning("⚠️ Please load an operational dataset first.")
    st.stop()

if not mappings:
    st.warning("⚠️ **Workflow Gate:** Please confirm column mappings on **03. Column Mapping** before running trend analysis.")
    st.stop()

# Identify default mapped date and metric fields (filtering out _primary placeholder collisions)
mapped_dates = [c for c, r in mappings.items() if r in ["date", "reporting_period"] and c in df.columns and not c.endswith("_primary")]
mapped_metrics = [c for c, r in mappings.items() if r in ["completed", "actual", "received", "target", "processing_time", "hours_used", "hours_available", "cost", "quality_measure", "customer_measure", "other_measure"] and c in df.columns and not c.endswith("_primary")]
mapped_groups = ["<None>"] + [c for c, r in mappings.items() if r in ["team", "department", "branch", "location", "category"] and c in df.columns and not c.endswith("_primary")]

# Fallbacks if confirmed mappings are minimal
if not mapped_dates:
    mapped_dates = [c for c in df.columns if any(k in c.lower() for k in ["month", "date", "period"]) and not c.endswith("_primary")]
if not mapped_metrics:
    mapped_metrics = [c for c in df.columns if any(k in c.lower() for k in ["avail", "hour", "score", "pct", "%", "target", "cost"]) and not c.endswith("_primary")]

if not mapped_dates:
    st.error("No confirmed Date or Reporting Period column found in mappings. Please map a Date/Period column on Page 03.")
    st.stop()

if not mapped_metrics:
    st.error("No confirmed numeric performance metric found in mappings. Please map at least one metric on Page 03.")
    st.stop()

# Intelligent default selection
date_idx = 0
for idx, d in enumerate(mapped_dates):
    if "reporting month" in d.lower():
        date_idx = idx
        break

metric_idx = 0
for idx, m in enumerate(mapped_metrics):
    if "availability" in m.lower() or "%" in m:
        metric_idx = idx
        break

c1, c2, c3, c4 = st.columns(4)
selected_date = c1.selectbox("Confirmed Date / Period Field:", mapped_dates, index=date_idx)
selected_metric = c2.selectbox("Confirmed Performance Metric:", mapped_metrics, index=metric_idx)
selected_group = c3.selectbox("Split by Dimension (Optional):", mapped_groups, index=0)

# Default to mean for percentages/rates, sum for counts
is_rate_metric = any(k in selected_metric.lower() for k in ["%", "rate", "avail", "pct", "score", "ratio", "time", "tat"])
default_agg_idx = 1 if is_rate_metric else 0
agg_choice = c4.selectbox("Aggregation Method:", ["sum", "mean"], index=default_agg_idx)

group_param = None if selected_group == "<None>" else selected_group
trend_res = calculate_trends(df, selected_date, selected_metric, group_param, agg_choice)

if "error" in trend_res:
    st.error(trend_res["error"])
else:
    st.session_state["trend_summary"] = trend_res
    st.session_state.audit_logger.log(
        "TREND_ANALYSIS_RUN",
        f"Executed trend analysis for '{selected_metric}' over '{selected_date}'",
        details={"net_pct_change": trend_res["net_pct_change"], "trajectory": trend_res["trajectory_class"]}
    )
    
    st.markdown("---")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Net Period Change", f"{trend_res['net_change']:+,.2f}", f"{trend_res['net_pct_change']:+,.1f}%")
    if trend_res.get("peak"):
        h2.metric("Peak Period", trend_res['peak']['period'], f"{trend_res['peak']['value']:,.2f}")
    if trend_res.get("trough"):
        h3.metric("Trough Period", trend_res['trough']['period'], f"{trend_res['trough']['value']:,.2f}")
        
    traj_class = trend_res.get("trajectory_class", "Mixed / Volatile")
    h4.metric("Trajectory Character", traj_class)
    
    st.markdown("#### 📈 Interactive Time-Series Trajectory")
    trend_df = trend_res["trend_df"]
    fig_tr = create_trend_chart(trend_df, "period", "value", title=f"Trend for '{selected_metric}' over '{selected_date}'", y_label=selected_metric)
    st.plotly_chart(fig_tr, use_container_width=True)
    
    st.markdown("#### 📋 Period-over-Period Analytical Table")
    st.dataframe(trend_df, use_container_width=True)
