"""Trend Analysis Engine for Performance Insight Explorer.
Aggregates time-series, orders chronologically, calculates period changes, peaks, troughs,
and classifies overall trajectory (Sustained Rise, Sustained Fall, Mixed / Volatile, Broadly Stable, Recent Rise, Recent Fall).
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def classify_trajectory(trend_df: pd.DataFrame, net_pct_change: float) -> str:
    """Classify overall trajectory character into:
    - Sustained Rise (consistently rising, net change > 0)
    - Sustained Fall (consistently falling, net change < 0)
    - Mixed / Volatile (both rises and falls, or early rise + later fall)
    - Broadly Stable (net change within ±3%, standard deviation low)
    - Recent Rise (recent consecutive periods rising despite flat/down overall)
    - Recent Fall (recent consecutive periods falling despite flat/up overall)
    """
    if trend_df is None or len(trend_df) < 2:
        return "Broadly Stable"
        
    diffs = trend_df["diff_abs"].dropna().tolist()
    if not diffs:
        return "Broadly Stable"
        
    total_diffs = len(diffs)
    pos_count = sum(1 for d in diffs if d > 0)
    neg_count = sum(1 for d in diffs if d < 0)
    
    has_sustained_up = any(diffs[i] > 0 and diffs[i+1] > 0 and diffs[i+2] > 0 for i in range(len(diffs)-2)) if len(diffs) >= 3 else False
    has_sustained_down = any(diffs[i] < 0 and diffs[i+1] < 0 and diffs[i+2] < 0 for i in range(len(diffs)-2)) if len(diffs) >= 3 else False
    
    # If both sustained up and sustained down exist within the same series: Mixed / Volatile
    if has_sustained_up and has_sustained_down:
        return "Mixed / Volatile"
        
    recent_diffs = diffs[-2:] if len(diffs) >= 2 else diffs
    recent_all_pos = all(d > 0 for d in recent_diffs)
    recent_all_neg = all(d < 0 for d in recent_diffs)
    
    # Check if broadly stable
    if abs(net_pct_change) <= 3.0 and pos_count > 0 and neg_count > 0:
        return "Broadly Stable"
        
    # Sustained Rise requires positive net change and dominant positive steps
    if has_sustained_up and net_pct_change > 0:
        if neg_count == 0 or (pos_count / total_diffs >= 0.75):
            return "Sustained Rise"
        return "Mixed / Volatile"
        
    # Sustained Fall requires negative net change and dominant negative steps
    if has_sustained_down and net_pct_change < 0:
        if pos_count == 0 or (neg_count / total_diffs >= 0.75):
            return "Sustained Fall"
        return "Mixed / Volatile"
        
    # Recent directional shifts
    if recent_all_pos and net_pct_change <= 0:
        return "Recent Rise"
    if recent_all_neg and net_pct_change >= 0:
        return "Recent Fall"
        
    if net_pct_change > 5.0 and pos_count > neg_count:
        return "Recent Rise" if recent_all_pos else "Mixed / Volatile"
    elif net_pct_change < -5.0 and neg_count > pos_count:
        return "Recent Fall" if recent_all_neg else "Mixed / Volatile"
        
    return "Mixed / Volatile"


def calculate_trends(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    group_col: Optional[str] = None,
    agg_func: str = "sum"
) -> Dict[str, Any]:
    """Calculate chronological trend series, period-to-period differences, and trajectory classification."""
    if df is None or date_col not in df.columns or metric_col not in df.columns:
        return {"error": f"Columns '{date_col}' or '{metric_col}' not found in dataset."}
        
    if str(date_col).strip() == str(metric_col).strip():
        return {"error": "Select different columns for the chronological period and performance metric."}

    cols_to_extract = [date_col] if date_col == metric_col else [date_col, metric_col]
    if group_col and group_col in df.columns and group_col not in cols_to_extract:
        cols_to_extract.append(group_col)
    work_df = df[cols_to_extract].copy()
    work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors="coerce")
    
    try:
        work_df["_parsed_date"] = pd.to_datetime(work_df[date_col], errors="coerce")
        has_valid_dates = work_df["_parsed_date"].notna().sum() / max(1, len(work_df)) >= 0.6
    except Exception:
        has_valid_dates = False
        
    if has_valid_dates:
        work_df = work_df.dropna(subset=["_parsed_date", metric_col])
        work_df = work_df.sort_values(by="_parsed_date")
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
        
    if agg_func == "mean":
        agg_series = work_df.groupby(period_key, sort=False)[metric_col].mean().reset_index()
    else:
        agg_series = work_df.groupby(period_key, sort=False)[metric_col].sum().reset_index()
        
    agg_series.columns = ["period", "value"]
    agg_series["value"] = agg_series["value"].round(2)
    
    agg_series["diff_abs"] = agg_series["value"].diff().round(2)
    agg_series["diff_pct"] = (agg_series["value"].pct_change() * 100.0).round(2)
    agg_series["diff_pct"] = agg_series["diff_pct"].replace([np.inf, -np.inf], np.nan)
    agg_series["rolling_3_mean"] = agg_series["value"].rolling(window=min(3, len(agg_series)), min_periods=1).mean().round(2)
    
    peak_row = agg_series.loc[agg_series["value"].idxmax()] if len(agg_series) > 0 else None
    trough_row = agg_series.loc[agg_series["value"].idxmin()] if len(agg_series) > 0 else None
    
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
    
    traj_class = classify_trajectory(agg_series, net_pct_change)
    
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
        "trajectory_class": traj_class,
        "metric_name": metric_col
    }


def calculate_trend_summary(
    df: Optional[pd.DataFrame],
    date_col: Optional[str],
    metric_col: Optional[str]
) -> Dict[str, Any]:
    """Calculate quick trend summary with graceful degradation for missing date or metric columns."""
    if df is None or not date_col or not metric_col:
        return {
            "direction": "Insufficient time points",
            "pct_change": 0.0,
            "run_chart_signals": [],
            "reason": "Longitudinal date or metric column not mapped."
        }
    if date_col not in df.columns or metric_col not in df.columns:
        return {
            "direction": "Insufficient time points",
            "pct_change": 0.0,
            "run_chart_signals": [],
            "reason": "Specified columns not present in dataset."
        }
    res = calculate_trends(df, date_col, metric_col)
    if "error" in res:
        return {
            "direction": "Insufficient time points",
            "pct_change": 0.0,
            "run_chart_signals": [],
            "reason": res["error"]
        }
    return {
        "direction": res.get("trajectory", "Stable"),
        "pct_change": res.get("net_pct_change", 0.0),
        "run_chart_signals": res.get("run_chart_signals", []),
        "raw_results": res
    }
