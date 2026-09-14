"""Comparison Analysis Engine for Performance Insight Explorer.
Segment comparisons by team, department, location, category, case type, or status.
Calculates raw totals, means, medians, normalised rates, variance ratios, and IQR spreads with small-sample warnings.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def compare_groups(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str,
    denominator_col: Optional[str] = None,
    agg_func: str = "sum",
    min_sample_threshold: int = 5
) -> Dict[str, Any]:
    """Generate comprehensive group comparison with ranking, variance from average, rate normalisation, and IQR spread."""
    # 1. Parameter Validation & Sanitization
    if df is None or len(df) == 0:
        return {"error": "Dataset is empty."}
        
    if group_col not in df.columns or metric_col not in df.columns:
        return {"error": f"Group '{group_col}' or Metric '{metric_col}' missing from dataset."}
        
    # Standardize agg_func
    if isinstance(agg_func, str):
        agg_func_clean = agg_func.lower().strip()
        if agg_func_clean not in ["sum", "mean"]:
            agg_func_clean = "sum"
    else:
        agg_func_clean = "sum"
        
    # Safeguard min_sample_threshold
    try:
        threshold_int = int(min_sample_threshold)
        if threshold_int < 1:
            threshold_int = 1
    except (ValueError, TypeError):
        threshold_int = 5
        
    # 2. Data Preparation
    cols_to_use = [group_col, metric_col]
    has_denom = bool(denominator_col and denominator_col in df.columns and denominator_col != "<None>")
    if has_denom:
        cols_to_use.append(denominator_col)
        
    work_df = df[cols_to_use].copy()
    work_df[group_col] = work_df[group_col].fillna("Unknown").astype(str).str.strip()
    work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors="coerce")
    work_df = work_df.dropna(subset=[metric_col])
    
    if len(work_df) == 0:
        return {"error": f"No numeric observations found for metric '{metric_col}'."}
        
    overall_mean = float(work_df[metric_col].mean())
    overall_sum = float(work_df[metric_col].sum())
    
    # 3. Group Aggregations
    agg_map = {
        metric_col: ["count", "sum", "mean", "median", "std", "min", "max"]
    }
    if has_denom:
        work_df[denominator_col] = pd.to_numeric(work_df[denominator_col], errors="coerce").fillna(0)
        agg_map[denominator_col] = ["sum", "mean"]
        
    grouped = work_df.groupby(group_col).agg(agg_map)
    
    # Overall benchmark calculation
    if has_denom:
        tot_denom = float(work_df[denominator_col].sum())
        overall_benchmark = (overall_sum / tot_denom) if tot_denom > 0 else np.nan
    else:
        overall_benchmark = overall_sum if agg_func_clean == "sum" else overall_mean
        
    comp_rows = []
    for grp_name, row in grouped.iterrows():
        count_val = int(row[(metric_col, "count")])
        sum_val = float(row[(metric_col, "sum")])
        mean_val = float(row[(metric_col, "mean")])
        med_val = float(row[(metric_col, "median")])
        std_val = float(row[(metric_col, "std")]) if not np.isnan(row[(metric_col, "std")]) else 0.0
        min_val = float(row[(metric_col, "min")])
        max_val = float(row[(metric_col, "max")])
        
        # Primary comparison value
        if has_denom:
            denom_sum = float(row[(denominator_col, "sum")])
            rate_val = round((sum_val / denom_sum), 2) if denom_sum > 0 else np.nan
            active_val = rate_val
        else:
            rate_val = None
            active_val = round(sum_val, 2) if agg_func_clean == "sum" else round(mean_val, 2)
            
        var_from_bench = round(active_val - overall_benchmark, 2) if (active_val is not None and not np.isnan(active_val) and not np.isnan(overall_benchmark)) else np.nan
        var_pct_bench = round((var_from_bench / overall_benchmark * 100.0), 2) if (overall_benchmark and not np.isnan(overall_benchmark) and overall_benchmark != 0 and var_from_bench is not None and not np.isnan(var_from_bench)) else np.nan
        
        comp_rows.append({
            "group": str(grp_name),
            "sample_count": count_val,
            "total_sum": round(sum_val, 2),
            "mean": round(mean_val, 2),
            "median": round(med_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "value": active_val,
            "normalised_rate": rate_val,
            "var_from_benchmark": var_from_bench,
            "var_pct_benchmark": var_pct_bench,
            "is_small_sample": (count_val < threshold_int)
        })
        
    comp_df = pd.DataFrame(comp_rows)
    
    # 4. Sorting & Ranking
    comp_df = comp_df.sort_values(by="value", ascending=False, na_position="last").reset_index(drop=True)
    comp_df["rank"] = comp_df.index + 1
    
    # 5. Summary Statistics & Ratios
    valid_values = comp_df["value"].dropna()
    if len(valid_values) > 0:
        top_group = str(comp_df.iloc[0]["group"])
        top_value = float(comp_df.iloc[0]["value"]) if comp_df.iloc[0]["value"] is not None and not np.isnan(comp_df.iloc[0]["value"]) else 0.0
        bottom_group = str(comp_df.iloc[-1]["group"])
        bottom_value = float(comp_df.iloc[-1]["value"]) if comp_df.iloc[-1]["value"] is not None and not np.isnan(comp_df.iloc[-1]["value"]) else 0.0
        
        min_val_positive = valid_values[valid_values > 0]
        if len(min_val_positive) > 0:
            min_pos = min_val_positive.min()
            max_v = valid_values.max()
            variance_ratio = round(float(max_v / min_pos), 2)
        else:
            variance_ratio = None
            
        q1 = float(valid_values.quantile(0.25))
        q3 = float(valid_values.quantile(0.75))
        iqr = q3 - q1
        iqr_ratio = round(iqr / q1, 2) if q1 > 0 else None
    else:
        top_group = "N/A"
        top_value = 0.0
        bottom_group = "N/A"
        bottom_value = 0.0
        variance_ratio = None
        iqr_ratio = None
        
    small_sample_groups = comp_df[comp_df["is_small_sample"]]["group"].tolist()
    
    return {
        "comparison_df": comp_df,
        "group_count": len(comp_df),
        "top_group": top_group,
        "top_value": top_value,
        "bottom_group": bottom_group,
        "bottom_value": bottom_value,
        "benchmark_value": round(overall_benchmark, 2) if not np.isnan(overall_benchmark) else None,
        "variance_ratio": variance_ratio,
        "iqr_ratio": iqr_ratio,
        "small_sample_groups": small_sample_groups,
        "aggregation": agg_func_clean,
        "metric_col": metric_col,
        "group_col": group_col,
        "denominator_col": denominator_col if has_denom else None,
        "top_performer": top_group,
        "bottom_performer": bottom_group,
        "overall_mean": round(overall_mean, 2),
        "overall_sum": round(overall_sum, 2)
    }
