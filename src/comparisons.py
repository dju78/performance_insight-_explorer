"""Comparison Analysis Engine for Performance Insight Explorer.
Segment comparisons by team, department, location, category, case type, or status.
Calculates raw totals, means, medians, and normalised rates with small-sample warnings.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def compare_groups(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str,
    denominator_col: Optional[str] = None,
    min_sample_threshold: int = 5
) -> Dict[str, Any]:
    """Generate comprehensive group comparison with ranking, variance from average, and rate normalisation."""
    if group_col not in df.columns or metric_col not in df.columns:
        return {"error": f"Group '{group_col}' or Metric '{metric_col}' missing from data."}
        
    work_df = df[[group_col, metric_col] + ([denominator_col] if denominator_col and denominator_col in df.columns else [])].copy()
    work_df[group_col] = work_df[group_col].fillna("Unknown").astype(str).str.strip()
    work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors="coerce")
    work_df = work_df.dropna(subset=[metric_col])
    
    if len(work_df) == 0:
        return {"error": f"No numeric records found for metric '{metric_col}'."}
        
    # Group aggregation
    agg_funcs = {
        metric_col: ["count", "sum", "mean", "median", "std", "min", "max"]
    }
    
    if denominator_col and denominator_col in work_df.columns:
        work_df[denominator_col] = pd.to_numeric(work_df[denominator_col], errors="coerce").fillna(0)
        agg_funcs[denominator_col] = ["sum", "mean"]
        
    grouped = work_df.groupby(group_col).agg(agg_funcs)
    
    # Flatten multi-index
    comp_rows = []
    overall_mean = float(work_df[metric_col].mean())
    overall_sum = float(work_df[metric_col].sum())
    
    for grp_name, row in grouped.iterrows():
        count_val = int(row[(metric_col, "count")])
        sum_val = float(row[(metric_col, "sum")])
        mean_val = float(row[(metric_col, "mean")])
        med_val = float(row[(metric_col, "median")])
        std_val = float(row[(metric_col, "std")]) if not np.isnan(row[(metric_col, "std")]) else 0.0
        min_val = float(row[(metric_col, "min")])
        max_val = float(row[(metric_col, "max")])
        
        rate_val = None
        if denominator_col and denominator_col in work_df.columns:
            denom_sum = float(row[(denominator_col, "sum")])
            rate_val = round((sum_val / denom_sum), 2) if denom_sum > 0 else np.nan
            
        var_from_mean = round(mean_val - overall_mean, 2)
        var_pct_from_mean = round(((mean_val - overall_mean) / overall_mean * 100.0) if overall_mean != 0 else 0.0, 2)
        
        comp_rows.append({
            "group": str(grp_name),
            "sample_count": count_val,
            "total_sum": round(sum_val, 2),
            "mean": round(mean_val, 2),
            "median": round(med_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "normalised_rate": rate_val,
            "var_from_benchmark": var_from_mean,
            "var_pct_benchmark": var_pct_from_mean,
            "is_small_sample": (count_val < min_sample_threshold)
        })
        
    comp_df = pd.DataFrame(comp_rows)
    
    # Rank by rate if available, else by mean
    rank_col = "normalised_rate" if denominator_col and "normalised_rate" in comp_df and comp_df["normalised_rate"].notna().sum() > 0 else "mean"
    comp_df = comp_df.sort_values(by=rank_col, ascending=False).reset_index(drop=True)
    comp_df["rank"] = comp_df.index + 1
    
    top_performer = comp_df.iloc[0]["group"] if len(comp_df) > 0 else "N/A"
    bottom_performer = comp_df.iloc[-1]["group"] if len(comp_df) > 0 else "N/A"
    small_sample_groups = comp_df[comp_df["is_small_sample"]]["group"].tolist()
    
    return {
        "comparison_df": comp_df,
        "group_col": group_col,
        "metric_col": metric_col,
        "denominator_col": denominator_col,
        "overall_mean": round(overall_mean, 2),
        "overall_sum": round(overall_sum, 2),
        "top_performer": top_performer,
        "bottom_performer": bottom_performer,
        "small_sample_groups": small_sample_groups,
        "group_count": len(comp_df)
    }
