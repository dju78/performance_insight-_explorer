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

# Identify default mapped date and metric fields
mapped_dates = [c for c, r in mappings.items() if r in ["date", "reporting_period"] and c in df.columns]
mapped_metrics = [c for c, r in mappings.items() if r in ["completed", "actual", "received", "target", "processing_time", "hours_used", "hours_available", "cost", "quality_measure", "customer_measure"] and c in df.columns]
mapped_groups = ["<None>"] + [c for c, r in mappings.items() if r in ["team", "department", "branch", "location", "category"] and c in df.columns]

if not mapped_dates:
    st.error("No confirmed Date or Reporting Period column found in mappings. Please map a Date/Period column on Page 03.")
    st.stop()

if not mapped_metrics:
    st.error("No confirmed numeric performance metric found in mappings. Please map at least one metric on Page 03.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
selected_date = c1.selectbox("Confirmed Date / Period Field:", mapped_dates)
selected_metric = c2.selectbox("Confirmed Performance Metric:", mapped_metrics)
selected_group = c3.selectbox("Split by Dimension (Optional):", mapped_groups)
agg_choice = c4.selectbox("Aggregation Method:", ["sum", "mean"])

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
