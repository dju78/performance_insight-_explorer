"""Page 06: Cohort Comparisons, Statistical Significance & Pareto Analysis.
Features:
- Group variance decomposition & quartile rankings
- ANOVA F-test, p-values, Cohen's d effect sizes, and practical significance
- Pareto 80/20 concentration curve
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path for Streamlit Cloud deployment
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.security import is_index_like_column
from core.state import init_session_state, get_working_df, advance_workflow_stage
from modules.analysis.stats_engine import calculate_group_comparison_statistics, calculate_pareto_curve

init_session_state()

st.title("👥 Stage 8: Comparisons, Cohorts & Significance")
st.markdown("Compare operational cohorts, test statistical significance ($p$-values, effect sizes), and identify performance concentration.")

df = get_working_df()
if df is None or len(df) == 0:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

confirmed = st.session_state.get("confirmed_mappings", {})

# Identify Grouping & Metric Columns (excluding index-like columns)
group_cols = [
    c for c, r in confirmed.items()
    if r in ["team", "department", "region", "product_service", "customer_segment", "category"]
    and c in df.columns and not is_index_like_column(c, df[c])
]
if not group_cols:
    group_cols = [
        c for c in df.select_dtypes(include=["object", "category", "string"]).columns
        if not is_index_like_column(c, df[c])
    ]

num_cols = [
    c for c in df.select_dtypes(include=[np.number]).columns
    if not is_index_like_column(c, df[c]) and not pd.api.types.is_bool_dtype(df[c])
]

if not group_cols or not num_cols:
    st.info("ℹ️ Group comparisons require at least one categorical dimension and one numeric metric column.")
    st.stop()

c_g1, c_g2 = st.columns(2)
with c_g1:
    group_col = st.selectbox("Cohort / Grouping Dimension", group_cols)
with c_g2:
    distinct_metrics = [c for c in num_cols if c != group_col]
    metric_idx = num_cols.index(distinct_metrics[0]) if distinct_metrics else 0
    metric_col = st.selectbox("Performance Metric to Compare", num_cols, index=metric_idx)

if str(group_col).strip() == str(metric_col).strip():
    st.warning("⚠️ Select different columns for the cohort grouping dimension and performance metric.")
    st.stop()

# Run Comparison Statistics
comp_results = calculate_group_comparison_statistics(df, group_col, metric_col)
st.session_state.comparison_summary = comp_results

groups_table = comp_results["groups_table"]

if groups_table.empty:
    st.warning("No valid records for the selected group and metric combination.")
    st.stop()

# -------------------------------------------------------------
# 1. COHORT PERFORMANCE & RANKING TABLE
# -------------------------------------------------------------
st.subheader(f"📊 Cohort Performance Ranking: {group_col} on {metric_col}")

# Visual Bar Chart
fig_bar = px.bar(
    groups_table,
    x=group_col,
    y="mean",
    color="mean",
    color_continuous_scale="Blues",
    text="mean",
    title=f"Mean {metric_col} by {group_col}"
)
fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig_bar.add_hline(
    y=comp_results["overall_mean"],
    line_dash="dash",
    line_color="red",
    annotation_text=f"Enterprise Mean: {comp_results['overall_mean']:.2f}"
)
st.plotly_chart(fig_bar, use_container_width=True)

# Statistical Significance Summary Banner
p_val = comp_results.get("anova_p_value")
f_stat = comp_results.get("anova_f_stat")
cohen_d = comp_results.get("cohens_d")
is_sig = comp_results.get("is_statistically_significant", False)

c_s1, c_s2, c_s3, c_s4 = st.columns(4)
with c_s1:
    st.metric("Enterprise Overall Mean", f"{comp_results['overall_mean']:,.2f}")
with c_s2:
    st.metric("ANOVA F-Statistic", f"{f_stat:.2f}" if f_stat is not None else "N/A")
with c_s3:
    st.metric("ANOVA p-value", f"{p_val:.4f}" if p_val is not None else "N/A")
with c_s4:
    st.metric("Cohen's d Effect Size", f"{cohen_d:.2f}" if cohen_d is not None else "N/A")

if is_sig:
    st.success(f"✅ **Statistically Significant Disparity (p < 0.05):** Performance differences between {group_col} cohorts are highly unlikely to be random noise ($p = {p_val:.4f}$, Cohen's $d = {cohen_d}$).")
else:
    st.info("ℹ️ **No Statistically Significant Difference:** Cohort variations fall within normal sampling noise ($p \\ge 0.05$).")

# Summary Table
st.markdown("##### 📋 Detailed Cohort Breakdown")
st.dataframe(groups_table, use_container_width=True)

# -------------------------------------------------------------
# 2. PARETO 80/20 CONCENTRATION ANALYSIS
# -------------------------------------------------------------
st.markdown("---")
st.subheader(f"🎯 Pareto 80/20 Concentration Curve: {group_col}")
st.caption("Identifies the vital few cohorts driving the majority (80%) of operational volume.")

pareto_df = calculate_pareto_curve(df, group_col, metric_col)

if not pareto_df.empty:
    fig_pareto = px.bar(
        pareto_df,
        x=group_col,
        y="share_pct",
        text="share_pct",
        title=f"Pareto Share % by {group_col}"
    )
    fig_pareto.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig_pareto, use_container_width=True)

st.markdown("---")
if st.button("Proceed to Stage 10 (Root-Cause Diagnostics) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_10_ROOT_CAUSE)
    st.success("Comparison stage completed.")
