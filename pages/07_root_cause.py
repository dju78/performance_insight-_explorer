"""Page 07: Root Cause Workspace & Exception Analysis."""
import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.root_cause import analyze_root_cause_pillars, calculate_correlations
from src.visualisations import create_scatter_correlation

init_session_state()

st.title("🔍 7. Root Cause Workspace & Exception Analysis")
st.caption("Synthesize operational drivers across 5 structured pillars: Demand, Capacity, Process, Complexity, and Data Quality.")

df = get_working_df()
if df is None or not st.session_state.confirmed_mappings:
    st.warning("⚠️ Please load data and complete column mapping to activate Root Cause analysis.")
else:
    kpi_res = st.session_state.get("kpi_results") or {}
    qa_report = st.session_state.get("qa_report") or {}
    
    pillars = analyze_root_cause_pillars(df, st.session_state.confirmed_mappings, kpi_res, qa_report)
    
    st.markdown("### 🏛️ The 5 Operational Pillars")
    
    p_cols = st.columns(5)
    p_keys = ["demand", "capacity", "process", "complexity", "data_quality"]
    for idx, p_key in enumerate(p_keys):
        p_data = pillars[p_key]
        with p_cols[idx]:
            st.markdown(f"**{p_data['title']}**")
            risk = p_data.get("risk_level", "Low")
            if risk == "High":
                st.error("Risk: HIGH")
            elif risk == "Medium":
                st.warning("Risk: MEDIUM")
            else:
                st.success("Risk: LOW")
            for f_text in p_data["findings"]:
                st.caption(f"• {f_text}")
                
    st.markdown("---")
    
    st.subheader("📊 Statistical Association Matrix (Pearson & Spearman)")
    st.info("⚠️ **CRITICAL GOVERNANCE NOTICE:** Association does not demonstrate causation. External operational factors, unrecorded case complexity, and system changes can confound correlations.")
    
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) >= 2:
        selected_corrs = st.multiselect("Select variables to correlate:", numeric_cols, default=numeric_cols[:min(4, len(numeric_cols))])
        if len(selected_corrs) >= 2:
            corr_res = calculate_correlations(df, selected_corrs)
            if "error" in corr_res:
                st.error(corr_res["error"])
            else:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("**Pearson Correlation Matrix (Linear):**")
                    st.dataframe(corr_res["pearson_matrix"], use_container_width=True)
                with col_c2:
                    st.markdown("**Spearman Correlation Matrix (Rank/Non-Linear):**")
                    st.dataframe(corr_res["spearman_matrix"], use_container_width=True)
                    
                if corr_res.get("significant_pairs"):
                    st.markdown("**Identified Statistical Associations (|r| >= 0.4):**")
                    st.dataframe(pd.DataFrame(corr_res["significant_pairs"]), use_container_width=True)
                    
                sc_c1, sc_c2 = st.columns(2)
                x_var = sc_c1.selectbox("Scatter X-Axis:", selected_corrs, index=0)
                y_var = sc_c2.selectbox("Scatter Y-Axis:", selected_corrs, index=1)
                fig_sc = create_scatter_correlation(df, x_var, y_var, title=f"Scatter: {x_var} vs {y_var}", x_label=x_var, y_label=y_var)
                st.plotly_chart(fig_sc, use_container_width=True)
