import streamlit as st
import pandas as pd
import plotly.express as px
from src.state import init_session_state, get_working_df
from src.metrics import calculate_kpi_summary

init_session_state()

st.title("📈 04. Performance Overview & KPI Dashboard")

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
granularity = st.session_state.get("row_granularity", "Record")

if df is None:
    st.warning("⚠️ Please upload a dataset on Page 01 first.")
    st.stop()

if not mappings:
    st.warning("⚠️ **Workflow Gate:** Please confirm column mappings on **03. Column Mapping** before viewing the Performance Overview.")
    st.stop()

# Log KPI run once per session state change
if not st.session_state.get("kpi_results"):
    st.session_state["kpi_results"] = calculate_kpi_summary(df, confirmed_mappings=mappings, target_directions=target_dirs)
    st.session_state.audit_logger.log("KPI_ANALYSIS_RUN", "Calculated KPI summary metrics from confirmed mappings.")

kpis = st.session_state.get("kpi_results", {})

st.info(f"📊 **Analysis Granularity:** 1 Row = `{granularity}` | **Filtered Volume:** {len(df):,} records")

if not kpis:
    st.warning("No operational metrics calculated based on current mappings.")
else:
    st.subheader("🎯 Operational KPI Scorecard")
    kpi_items = list(kpis.items())
    cols = st.columns(min(len(kpi_items), 4))
    
    for i, (kpi_name, kpi_data) in enumerate(kpi_items):
        col = cols[i % min(len(kpi_items), 4)]
        with col:
            val = kpi_data.get('actual')
            val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            unit = kpi_data.get('unit', '')
            if unit:
                val_str = f"{val_str} {unit}"
                
            if kpi_data.get("target") is not None:
                var_pct = kpi_data.get('variance_pct')
                var_str = f"{var_pct:+.1f}% vs Target" if var_pct is not None else "Target: None"
                direction_label = kpi_data.get("direction", "higher_is_better")
                is_favorable = kpi_data.get("is_favorable")
                
                status_icon = "🟢" if is_favorable else ("🔴" if is_favorable is False else "⚪")
                st.metric(
                    label=f"{status_icon} {kpi_data['display_name']}",
                    value=val_str,
                    delta=var_str,
                    delta_color="normal" if is_favorable else ("inverse" if is_favorable is False else "off")
                )
                st.caption(f"Target: {kpi_data['target']:,.2f} | Direction: {direction_label.replace('_', ' ').title()}")
            else:
                st.metric(label=kpi_data['display_name'], value=val_str)

st.markdown("---")
st.subheader("📊 Metric Distribution & Segmentation")

num_cols = [c for c in df.select_dtypes(include=['number']).columns if c in mappings]
if not num_cols:
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

if num_cols:
    selected_metric = st.selectbox("Select Metric to Inspect", num_cols)
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        fig_hist = px.histogram(
            df, x=selected_metric, nbins=30,
            title=f"Distribution of {selected_metric}",
            marginal="box",
            color_discrete_sequence=["#1f77b4"]
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with c_chart2:
        cat_cols = [c for c in df.columns if c in mappings and mappings[c] in ["team", "department", "branch", "location", "category"]]
        if not cat_cols:
            cat_cols = [c for c in df.columns if df[c].dtype == 'object' or str(df[c].dtype) == 'category']
            
        if cat_cols:
            group_col = st.selectbox("Group By Dimension", cat_cols)
            summary_grp = df.groupby(group_col)[selected_metric].agg(['count', 'mean', 'median']).reset_index()
            fig_bar = px.bar(
                summary_grp, x=group_col, y='mean',
                title=f"Mean {selected_metric} by {group_col}",
                color='mean',
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No categorical grouping dimension available.")
