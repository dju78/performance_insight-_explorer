"""Page 06: Group & Segment Comparisons."""
import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.comparisons import compare_groups
from src.visualisations import create_comparison_bar

init_session_state()

st.title("👥 6. Group & Segment Comparisons")
st.caption("Compare performance across teams, branches, categories, or case types with normalised rates and small-sample safeguards.")

df = get_working_df()
if df is None:
    st.warning("⚠️ Please load an operational dataset first.")
else:
    group_candidates = [c for c in df.columns if df[c].nunique() <= 50 and not pd.api.types.is_numeric_dtype(df[c])]
    numeric_candidates = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    denom_candidates = ["<None>"] + [c for c in numeric_candidates if any(k in c.lower() for k in ["fte", "staff", "hours", "cases", "total", "received"])]
    
    if not group_candidates or not numeric_candidates:
        st.error("Comparison requires categorical group dimensions and numeric performance fields.")
    else:
        c1, c2, c3 = st.columns(3)
        selected_group = c1.selectbox("Select Segment / Dimension Field:", group_candidates)
        selected_metric = c2.selectbox("Select Performance Metric:", numeric_candidates)
        selected_denom = c3.selectbox("Normalise by Denominator (Optional):", denom_candidates)
        
        denom_param = None if selected_denom == "<None>" else selected_denom
        comp_res = compare_groups(df, selected_group, selected_metric, denom_param)
        
        if "error" in comp_res:
            st.error(comp_res["error"])
        else:
            st.markdown("---")
            c_top, c_bot, c_avg = st.columns(3)
            c_top.metric("Top Performing Segment", comp_res["top_performer"])
            c_bot.metric("Lowest Segment", comp_res["bottom_performer"])
            c_avg.metric("Overall Population Average", f"{comp_res['overall_mean']:,.2f}")
            
            if comp_res.get("small_sample_groups"):
                st.warning(f"⚠️ Small Sample Warning: Groups {comp_res['small_sample_groups']} contain <5 observations. Interpret rankings cautiously.")
                
            comp_df = comp_res["comparison_df"]
            bar_y = "normalised_rate" if denom_param and "normalised_rate" in comp_df and comp_df["normalised_rate"].notna().sum() > 0 else "mean"
            bar_y_label = f"Rate ({selected_metric} per {denom_param})" if denom_param else f"Mean {selected_metric}"
            
            fig_bar = create_comparison_bar(
                comp_df,
                x_col="group",
                y_col=bar_y,
                title=f"Comparison of '{selected_group}' by {bar_y_label}",
                x_label=selected_group,
                y_label=bar_y_label,
                target_val=comp_res["overall_mean"] if not denom_param else None
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.markdown("#### 📋 Ranked Segment Performance Matrix")
            st.dataframe(comp_df, use_container_width=True)
