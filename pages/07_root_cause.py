"""Page 07: Structured Root-Cause Analysis (RCA) & Driver Diagnostics.
Features:
- Structured 10-step diagnostic RCA workflow
- Bivariate correlation and multivariate OLS driver importance ranking
- Evidence strength grading (Confirmed, Strongly Supported, Possible, Requires Evidence)
- Interactive 5-Whys tree and Ishikawa Fishbone categorization workspace
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.constants import WorkflowStage
from core.state import init_session_state, get_working_df, advance_workflow_stage, log_audit_event
from modules.diagnostics.root_cause_engine import (
    evaluate_driver_correlations, calculate_driver_importance_regression
)

init_session_state()

st.title("🔬 Stage 10: Root-Cause Diagnostics & Driver Trees")
st.markdown("Investigate operational drivers, rank evidence strength, and record qualitative operational context.")

df = get_working_df()
if df is None:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if len(num_cols) < 2:
    st.info("ℹ️ Driver analysis requires at least two numeric measures (one target outcome and one candidate driver).")
    st.stop()

# -------------------------------------------------------------
# 1. DRIVER CORRELATION & REGRESSION ANALYSIS
# -------------------------------------------------------------
st.subheader("1️⃣ Statistical Driver Importance & Evidence Ranking")

c_r1, c_r2 = st.columns(2)
with c_r1:
    target_kpi = st.selectbox("Target Outcome Metric (Dependent Variable Y)", num_cols, index=0)
with c_r2:
    candidate_drivers = st.multiselect(
        "Candidate Operational Drivers (Independent Variables X)",
        [c for c in num_cols if c != target_kpi],
        default=[c for c in num_cols if c != target_kpi][:4]
    )

if candidate_drivers:
    driver_results = evaluate_driver_correlations(df, target_kpi, candidate_drivers)
    reg_summary = calculate_driver_importance_regression(df, target_kpi, candidate_drivers)
    st.session_state.root_cause_summary = {"drivers": driver_results, "regression": reg_summary}

    if reg_summary.get("r_squared") is not None:
        st.markdown(f"**Multivariate OLS Regression Fit ($R^2$):** `{reg_summary['r_squared']:.1%}` of variance in `{target_kpi}` is explained by selected candidate drivers.")

    # Driver Cards
    for d in driver_results:
        driver_name = d["driver_field"]
        r_val = d["pearson_r"]
        r_sq = d["r_squared"]
        p_val = d["p_value"]
        tier = d["evidence_tier"]
        conf = d["confidence"]
        interp = d["interpretation"]

        tier_icon = "🟢" if "Confirmed" in tier else ("🟡" if "Strongly" in tier else ("🟠" if "Possible" in tier else "⚪"))

        with st.expander(f"{tier_icon} **{driver_name}** | Pearson $r={r_val:+.2f}$ | $R^2={r_sq:.1%}$ | $p={p_val:.4f}$ | Evidence: **{tier}**", expanded=("Confirmed" in tier)):
            st.markdown(f"**Interpretation:** {interp}")
            st.markdown(f"**Confidence Level:** {conf}")
            st.caption(f"🔒 **Governance Caveat:** {d['caveat']}")

            # Scatter plot with trendline
            clean_sub = df[[driver_name, target_kpi]].dropna()
            if len(clean_sub) >= 5:
                fig_scatter = px.scatter(
                    clean_sub,
                    x=driver_name,
                    y=target_kpi,
                    trendline="ols",
                    title=f"Scatter Relationship: {driver_name} vs {target_kpi}"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

# -------------------------------------------------------------
# 2. QUALITATIVE 5-WHYS WORKSPACE
# -------------------------------------------------------------
st.markdown("---")
st.subheader("2️⃣ Qualitative 5-Whys Diagnostic Workspace")
st.caption("Capture progressive root-cause questioning grounded in operational observations.")

whys = st.session_state.get("five_whys_notes", ["", "", "", "", ""])
updated_whys = []

why_labels = [
    "1. Why is there an operational shortfall or bottleneck?",
    "2. Why did that specific condition occur?",
    "3. Why was that not prevented or absorbed by capacity?",
    "4. Why does the underlying process or policy permit this?",
    "5. Root Cause: What fundamental systemic improvement is required?"
]

for idx, label in enumerate(why_labels):
    val = whys[idx] if idx < len(whys) else ""
    ans = st.text_input(label, value=val, key=f"why_input_{idx}", placeholder=f"Explain cause {idx+1}...")
    updated_whys.append(ans)

st.session_state.five_whys_notes = updated_whys

# -------------------------------------------------------------
# 3. ISHIKAWA / FISHBONE CATEGORIES
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3️⃣ Fishbone (Ishikawa) Cause Categorization")
st.caption("Organize operational context into standard enterprise diagnostic categories.")

fishbone = st.session_state.get("fishbone_categories", {})
cols_fish = st.columns(3)

categories = list(fishbone.keys())
for idx, cat_name in enumerate(categories):
    col_idx = idx % 3
    with cols_fish[col_idx]:
        st.markdown(f"**{cat_name}**")
        notes_str = "\n".join(fishbone[cat_name])
        new_notes = st.text_area(f"Causes for {cat_name}", value=notes_str, key=f"fish_area_{cat_name}", height=80, label_visibility="collapsed")
        st.session_state.fishbone_categories[cat_name] = [line.strip() for line in new_notes.split("\n") if line.strip()]

st.markdown("---")
if st.button("Proceed to Stage 12 (Evidence Insights) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_10_ROOT_CAUSE)
    st.success("Root-cause diagnostic stage recorded.")
