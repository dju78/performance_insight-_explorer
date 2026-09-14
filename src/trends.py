"""Trend Analysis Engine for Performance Insight Explorer.
Aggregates time-series, orders chronologically, calculates period changes, peaks, troughs, and sustained direction.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def calculate_trends(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    group_col: Optional[str] = None,
    agg_func: str = "sum"
) -> Dict[str, Any]:
    """Calculate chronological trend series, period-to-period differences, and trend characteristics."""
    if date_col not in df.columns or metric_col not in df.columns:
        return {"error": f"Columns '{date_col}' or '{metric_col}' not found in dataset."}
        
    work_df = df[[date_col, metric_col] + ([group_col] if group_col and group_col in df.columns else [])].copy()
    work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors="coerce")
    
    # Try date parsing
    try:
        work_df["_parsed_date"] = pd.to_datetime(work_df[date_col], errors="coerce")
        has_valid_dates = work_df["_parsed_date"].notna().sum() / max(1, len(work_df)) >= 0.6
    except Exception:
        has_valid_dates = False
        
    if has_valid_dates:
        work_df = work_df.dropna(subset=["_parsed_date", metric_col])
        work_df = work_df.sort_values(by="_parsed_date")
        # Determine period format
        date_span = (work_df["_parsed_date"].max() - work_df["_parsed_date"].min()).days
        if date_span > 180:
            work_df["_period_str"] = work_df["_parsed_date"].dt.strftime("%Y-%m")
        elif date_span > 30:
            work_df["_period_str"] = work_df["_parsed_date"].dt.strftime("%Y-W%W")
        else:
            work_df["_period_str"] = work_df["_parsed_date"].dt.strftime("%Y-%m-%d")
        period_key = "_period_str"
    else:
        work_df = work_df.dropna(subset=[date_col, metric_col])
        work_df[date_col] = work_df[date_col].astype(str)
        work_df = work_df.sort_values(by=date_col)
        period_key = date_col
        
    if len(work_df) == 0:
        return {"error": "No valid observations remaining after filtering dates and numeric metric."}
        
    # Aggregate overall trend
    if agg_func == "mean":
        agg_series = work_df.groupby(period_key, sort=False)[metric_col].mean().reset_index()
    else:
        agg_series = work_df.groupby(period_key, sort=False)[metric_col].sum().reset_index()
        
    agg_series.columns = ["period", "value"]
    agg_series["value"] = agg_series["value"].round(2)
    
    # Period-over-period differences
    agg_series["diff_abs"] = agg_series["value"].diff().round(2)
    agg_series["diff_pct"] = (agg_series["value"].pct_change() * 100.0).round(2)
    agg_series["diff_pct"] = agg_series["diff_pct"].replace([np.inf, -np.inf], np.nan)
    
    # Rolling 3-period mean
    agg_series["rolling_3_mean"] = agg_series["value"].rolling(window=min(3, len(agg_series)), min_periods=1).mean().round(2)
    
    # Trend highlights
    peak_row = agg_series.loc[agg_series["value"].idxmax()] if len(agg_series) > 0 else None
    trough_row = agg_series.loc[agg_series["value"].idxmin()] if len(agg_series) > 0 else None
    
    # Sustained direction detection (3 consecutive periods)
    sustained_increase = False
    sustained_decrease = False
    if len(agg_series) >= 3:
        diffs = agg_series["diff_abs"].dropna().tolist()
        for i in range(len(diffs) - 2):
            if diffs[i] > 0 and diffs[i+1] > 0 and diffs[i+2] > 0:
                sustained_increase = True
            if diffs[i] < 0 and diffs[i+1] < 0 and diffs[i+2] < 0:
                sustained_decrease = True
                
    overall_start_val = float(agg_series["value"].iloc[0])
    overall_end_val = float(agg_series["value"].iloc[-1])
    net_period_change = round(overall_end_val - overall_start_val, 2)
    net_pct_change = round(((overall_end_val - overall_start_val) / overall_start_val * 100.0) if overall_start_val != 0 else 0.0, 2)
    
    # Group breakdown if group_col provided
    grouped_df = None
    if group_col and group_col in df.columns:
        if agg_func == "mean":
            grouped_df = work_df.groupby([period_key, group_col], sort=False)[metric_col].mean().reset_index()
        else:
            grouped_df = work_df.groupby([period_key, group_col], sort=False)[metric_col].sum().reset_index()
        grouped_df.columns = ["period", group_col, "value"]
        grouped_df["value"] = grouped_df["value"].round(2)
        
    return {
        "trend_df": agg_series,
        "grouped_df": grouped_df,
        "period_count": len(agg_series),
        "peak": {"period": str(peak_row["period"]), "value": float(peak_row["value"])} if peak_row is not None else None,
        "trough": {"period": str(trough_row["period"]), "value": float(trough_row["value"])} if trough_row is not None else None,
        "start_value": overall_start_val,
        "end_value": overall_end_val,
        "net_change": net_period_change,
        "net_pct_change": net_pct_change,
        "sustained_increase": sustained_increase,
        "sustained_decrease": sustained_decrease,
        "metric_name": metric_col
    }
