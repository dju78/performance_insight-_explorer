import streamlit as st
import pandas as pd
import plotly.express as px
from src.state import init_session_state
from src.metrics import calculate_kpi_summary, evaluate_target_variance

init_session_state()

st.title("📈 04. Performance Overview & KPI Dashboard")

df = st.session_state.get("clean_df")
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
granularity = st.session_state.get("row_granularity", "Record")

if df is None:
    st.warning("⚠️ Please upload a dataset first.")
    st.stop()

if not mappings:
    st.warning("⚠️ No confirmed column mappings found. Please go to **03. Column Mapping** and confirm mappings first.")
    st.stop()

st.info(f"📊 **Analysis Granularity:** 1 Row = `{granularity}` | **Total Volume:** {len(df):,} records")

# Compute KPIs
kpis = calculate_kpi_summary(df, mappings, target_dirs)

if not kpis:
    st.warning("No numeric metrics or targets mapped yet.")
else:
    st.subheader("🎯 Operational KPI Scorecard")
    cols = st.columns(min(len(kpis), 4))
    
    for i, (kpi_name, kpi_data) in enumerate(kpis.items()):
        col = cols[i % min(len(kpis), 4)]
        with col:
            val_str = f"{kpi_data['actual']:,.2f}" if isinstance(kpi_data['actual'], (int, float)) else str(kpi_data['actual'])
            
            if kpi_data.get("target") is not None:
                var_str = f"{kpi_data['variance_pct']:+.1f}% vs Target" if kpi_data['variance_pct'] is not None else "Target: None"
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
st.subheader("📊 Primary Metric Distribution")

# Plot distribution of numeric columns
num_cols = [c for c in df.select_dtypes(include=['number']).columns if c in mappings]
if not num_cols:
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

if num_cols:
    selected_metric = st.selectbox("Select Metric to Visualize", num_cols)
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
        # Group by first category column if available
        cat_cols = [c for c in df.columns if df[c].dtype == 'object' or str(df[c].dtype) == 'category']
        if cat_cols:
            group_col = st.selectbox("Group By Category", cat_cols)
            summary_grp = df.groupby(group_col)[selected_metric].agg(['count', 'mean', 'median']).reset_index()
            fig_bar = px.bar(
                summary_grp, x=group_col, y='mean',
                title=f"Mean {selected_metric} by {group_col}",
                color='mean',
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No categorical columns available for grouping.")
