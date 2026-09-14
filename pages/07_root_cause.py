import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.root_cause import calculate_correlations, analyze_root_cause_pillars
from src.visualisations import create_correlation_heatmap

init_session_state()

st.title("🌲 07. Root Cause & Driver Tree Analysis")
st.caption("Deconstruct operational drivers across Capacity, Demand, Process, Complexity, and Quality pillars.")

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})

if df is None:
    st.warning("⚠️ Please load an operational dataset first.")
    st.stop()

if not mappings:
    st.warning("⚠️ **Workflow Gate:** Please confirm column mappings on **03. Column Mapping** before accessing Root Cause Analysis.")
    st.stop()

st.info("⚠️ **Analytical Disclaimer:** Observed correlations highlight statistical co-movement across operational drivers, NOT proven causation.")

st.session_state.audit_logger.log("ROOT_CAUSE_ANALYSIS_RUN", "Executed driver tree and correlation analysis.")

# 1. Driver Pillars
kpi_res = st.session_state.get("kpi_results", {})
qa_rep = st.session_state.get("qa_report", {})
pillars = analyze_root_cause_pillars(df, mappings, kpi_res, qa_rep)

st.subheader("🏛️ Operational Driver Pillars")
p1, p2, p3, p4 = st.columns(4)

with p1:
    st.markdown("#### 👥 Capacity Pillar")
    cap_info = pillars.get("capacity", {})
    st.caption(f"Risk: `{cap_info.get('risk_level', 'Low')}`")
    for item in cap_info.get("findings", [])[:3]:
        st.markdown(f"- {item}")

with p2:
    st.markdown("#### 📥 Demand Pillar")
    dem_info = pillars.get("demand", {})
    st.caption(f"Risk: `{dem_info.get('risk_level', 'Low')}`")
    for item in dem_info.get("findings", [])[:3]:
        st.markdown(f"- {item}")

with p3:
    st.markdown("#### ⚙️ Process Pillar")
    proc_info = pillars.get("process", {})
    st.caption(f"Risk: `{proc_info.get('risk_level', 'Low')}`")
    for item in proc_info.get("findings", [])[:3]:
        st.markdown(f"- {item}")

with p4:
    st.markdown("#### 🎯 Complexity & Quality")
    cplx_info = pillars.get("complexity", {})
    st.caption(f"Risk: `{cplx_info.get('risk_level', 'Low')}`")
    for item in cplx_info.get("findings", [])[:3]:
        st.markdown(f"- {item}")

# 2. Correlation Matrix
st.markdown("---")
st.subheader("🔗 Operational Driver Correlation Matrix")
num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c in mappings]
if not num_cols:
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

corr_res = calculate_correlations(df, num_cols)

if "error" in corr_res:
    st.warning(corr_res["error"])
else:
    corr_matrix = corr_res["pearson_matrix"]
    fig_corr = create_correlation_heatmap(corr_matrix, title="Pearson Correlation Matrix (Operational Drivers)")
    st.plotly_chart(fig_corr, use_container_width=True)
    
    if corr_res.get("significant_pairs"):
        st.markdown("#### 🔍 Statistically Significant Associations")
        for pair in corr_res["significant_pairs"]:
            st.markdown(f"- **`{pair['variable_1']}`** ↔ **`{pair['variable_2']}`**: *{pair['relationship']}* (Pearson r = `{pair['pearson_r']}`, p = `{pair['pearson_p']}`)")
