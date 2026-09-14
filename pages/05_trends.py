"""Page 05: Trend Analysis & Time-Series Dynamics."""
import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.trends import calculate_trends
from src.visualisations import create_trend_chart

init_session_state()

st.title("⏱️ 5. Trend Analysis & Time Dynamics")
st.caption("Chronological time-series trajectories, period-over-period changes, peaks, troughs, and sustained directions.")

df = get_working_df()
if df is None:
    st.warning("⚠️ Please load an operational dataset first.")
else:
    date_candidates = [c for c in df.columns if any(k in c.lower() for k in ["date", "month", "period", "year", "time", "week"])]
    numeric_candidates = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    group_candidates = ["<None>"] + [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() <= 20]
    
    if not date_candidates or not numeric_candidates:
        st.error("Dataset requires at least one date/period column and one numeric metric column for trend analysis.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        selected_date = c1.selectbox("Select Date / Period Field:", date_candidates)
        selected_metric = c2.selectbox("Select Numeric Metric:", numeric_candidates)
        selected_group = c3.selectbox("Split by Group (Optional):", group_candidates)
        agg_choice = c4.selectbox("Aggregation Type:", ["sum", "mean"])
        
        group_col_param = None if selected_group == "<None>" else selected_group
        trend_res = calculate_trends(df, selected_date, selected_metric, group_col_param, agg_choice)
        
        if "error" in trend_res:
            st.error(trend_res["error"])
        else:
            st.markdown("---")
            h1, h2, h3, h4 = st.columns(4)
            h1.metric("Net Period Change", f"{trend_res['net_change']:+,.2f}", f"{trend_res['net_pct_change']:+,.1f}%")
            if trend_res.get("peak"):
                h2.metric("Peak Period", trend_res['peak']['period'], f"{trend_res['peak']['value']:,.2f}")
            if trend_res.get("trough"):
                h3.metric("Trough Period", trend_res['trough']['period'], f"{trend_res['trough']['value']:,.2f}")
                
            dir_str = "Neutral / Volatile"
            if trend_res.get("sustained_increase"):
                dir_str = "🟢 Sustained Rise (>=3 periods)"
            elif trend_res.get("sustained_decrease"):
                dir_str = "🔴 Sustained Fall (>=3 periods)"
            h4.metric("Trajectory Character", dir_str)
            
            st.markdown("#### 📈 Interactive Time-Series Trajectory")
            trend_df = trend_res["trend_df"]
            fig_tr = create_trend_chart(trend_df, "period", "value", title=f"Trend for '{selected_metric}' over '{selected_date}'", y_label=selected_metric)
            st.plotly_chart(fig_tr, use_container_width=True)
            
            st.markdown("#### 📋 Period-over-Period Analytical Table")
            st.dataframe(trend_df, use_container_width=True)
