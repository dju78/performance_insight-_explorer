import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.comparisons import compare_groups
from src.visualisations import create_comparison_bar

init_session_state()

st.title("⚖️ 06. Operational Comparisons & Cohorts")
st.caption("Rank operational units, compare quartile throughput distributions, and benchmark segment variance.")

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})

if df is None:
    st.warning("⚠️ Please load an operational dataset first.")
    st.stop()

if not mappings:
    st.warning("⚠️ **Workflow Gate:** Please confirm column mappings on **03. Column Mapping** before running analytical comparisons.")
    st.stop()

# Group by confirmed dimensions
mapped_dims = [c for c, r in mappings.items() if r in ["team", "department", "branch", "location", "category"] and c in df.columns]
mapped_metrics = [c for c, r in mappings.items() if r in ["completed", "actual", "received", "target", "processing_time", "hours_used", "hours_available", "cost", "quality_measure", "customer_measure"] and c in df.columns]
mapped_denoms = ["<None>"] + [c for c, r in mappings.items() if r in ["fte", "staff", "hours_available"] and c in df.columns]

if not mapped_dims:
    st.error("No confirmed Dimension column (Team, Dept, Location, Category) found in mappings. Please map a dimension on Page 03.")
    st.stop()

if not mapped_metrics:
    st.error("No confirmed Performance Metric found in mappings. Please map at least one metric on Page 03.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
selected_group = c1.selectbox("Confirmed Dimension to Compare:", mapped_dims)
selected_metric = c2.selectbox("Primary Performance Metric:", mapped_metrics)
selected_denom = c3.selectbox("Capacity Denominator (Optional):", mapped_denoms)
agg_choice = c4.selectbox("Metric Aggregation:", ["sum", "mean"])

denom_param = None if selected_denom == "<None>" else selected_denom
comp_res = compare_groups(df, selected_group, selected_metric, denom_param, agg_choice)

if "error" in comp_res:
    st.error(comp_res["error"])
else:
    st.session_state.audit_logger.log(
        "COMPARISON_ANALYSIS_RUN",
        f"Compared groups in '{selected_group}' on '{selected_metric}'",
        details={"group_count": comp_res["group_count"], "iqr_ratio": comp_res.get("iqr_ratio")}
    )
    
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Compared Groups", comp_res["group_count"])
    m2.metric("Top Performer", comp_res.get("top_group", "N/A"), f"{comp_res.get('top_value', 0):,.2f}")
    m3.metric("Lowest Performer", comp_res.get("bottom_group", "N/A"), f"{comp_res.get('bottom_value', 0):,.2f}")
    m4.metric("Variance Spread (Max / Min)", f"{comp_res.get('variance_ratio', 1.0):.2f}x")
    
    st.markdown("#### 📊 Comparative League Table")
    comp_df = comp_res["comparison_df"]
    fig_comp = create_comparison_bar(comp_df, selected_group, "value", title=f"Comparison of '{selected_metric}' by '{selected_group}'")
    st.plotly_chart(fig_comp, use_container_width=True)
    
    st.markdown("#### 📋 Detailed Group Breakdown")
    st.dataframe(comp_df, use_container_width=True)
