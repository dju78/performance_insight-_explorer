"""Statistical and Quantitative Analysis Engine for Performance Insight Explorer.
Calculates descriptive distributions, time-series run charts / control limits, group comparisons with effect sizes,
and Pareto concentration curves.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


def calculate_descriptive_stats(series: pd.Series) -> Dict[str, Any]:
    """Calculate comprehensive robust summary statistics for a numeric series."""
    clean_s = pd.to_numeric(series, errors="coerce").dropna()
    n = len(clean_s)
    if n == 0:
        return {"n": 0}

    mean_val = float(clean_s.mean())
    std_val = float(clean_s.std()) if n > 1 else 0.0
    med_val = float(clean_s.median())
    q25 = float(clean_s.quantile(0.25))
    q75 = float(clean_s.quantile(0.75))
    iqr = q75 - q25

    skew = float(stats.skew(clean_s)) if n >= 3 else 0.0
    kurt = float(stats.kurtosis(clean_s)) if n >= 4 else 0.0

    return {
        "n": n,
        "sum": round(float(clean_s.sum()), 2),
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "median": round(med_val, 2),
        "min": round(float(clean_s.min()), 2),
        "max": round(float(clean_s.max()), 2),
        "q10": round(float(clean_s.quantile(0.10)), 2),
        "q25": round(q25, 2),
        "q75": round(q75, 2),
        "q90": round(float(clean_s.quantile(0.90)), 2),
        "iqr": round(iqr, 2),
        "skewness": round(skew, 2),
        "kurtosis": round(kurt, 2)
    }


def calculate_control_chart_limits(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    aggregation: str = "mean"
) -> pd.DataFrame:
    """Calculate Shewhart Statistical Process Control (SPC) / Run Chart limits (CL, UCL, LCL)."""
    if df is None or date_col not in df.columns or metric_col not in df.columns:
        return pd.DataFrame()

    temp_df = df.dropna(subset=[date_col, metric_col]).copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df = temp_df.dropna(subset=[date_col])
    temp_df[metric_col] = pd.to_numeric(temp_df[metric_col], errors="coerce")

    # Group by date
    if aggregation == "sum":
        grouped = temp_df.groupby(date_col)[metric_col].sum().reset_index()
    else:
        grouped = temp_df.groupby(date_col)[metric_col].mean().reset_index()

    grouped = grouped.sort_values(by=date_col).reset_index(drop=True)
    if len(grouped) == 0:
        return pd.DataFrame()

    center_line = float(grouped[metric_col].mean())
    stdev = float(grouped[metric_col].std()) if len(grouped) > 1 else 0.0

    grouped["center_line"] = center_line
    grouped["ucl_3sigma"] = center_line + (3.0 * stdev)
    grouped["lcl_3sigma"] = max(0.0, center_line - (3.0 * stdev))
    grouped["warn_upper_2sigma"] = center_line + (2.0 * stdev)
    grouped["warn_lower_2sigma"] = max(0.0, center_line - (2.0 * stdev))

    # Identify special cause outliers
    grouped["is_special_cause"] = (grouped[metric_col] > grouped["ucl_3sigma"]) | (grouped[metric_col] < grouped["lcl_3sigma"])
    grouped["mom_change_pct"] = grouped[metric_col].pct_change() * 100.0

    return grouped


def calculate_group_comparison_statistics(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str
) -> Dict[str, Any]:
    """Calculate between-group comparisons, rankings, variance contributions, and statistical tests."""
    if df is None or group_col not in df.columns or metric_col not in df.columns:
        return {"groups_table": pd.DataFrame(), "anova_p_value": None, "cohens_d": None}

    clean_df = df.dropna(subset=[group_col, metric_col]).copy()
    clean_df[metric_col] = pd.to_numeric(clean_df[metric_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[metric_col])

    if len(clean_df) == 0:
        return {"groups_table": pd.DataFrame(), "anova_p_value": None, "cohens_d": None}

    # Group summaries
    grouped = clean_df.groupby(group_col)[metric_col].agg(
        count="count",
        sum="sum",
        mean="mean",
        std="std",
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75)
    ).reset_index()

    overall_mean = clean_df[metric_col].mean()
    total_sum = clean_df[metric_col].sum()

    grouped["pct_of_total_volume"] = (grouped["sum"] / total_sum * 100.0) if total_sum > 0 else 0.0
    grouped["variance_from_overall_mean"] = grouped["mean"] - overall_mean
    grouped["variance_pct_from_overall"] = (grouped["variance_from_overall_mean"] / overall_mean * 100.0) if overall_mean != 0 else 0.0

    # Quartile ranking
    if len(grouped) >= 4:
        grouped["quartile"] = pd.qcut(grouped["mean"], 4, labels=["Q4 (Lowest)", "Q3", "Q2", "Q1 (Highest)"])
    else:
        grouped["quartile"] = "N/A"

    grouped = grouped.sort_values(by="mean", ascending=False).reset_index(drop=True)

    # ANOVA F-test across groups
    unique_groups = clean_df[group_col].unique()
    group_arrays = [clean_df[clean_df[group_col] == g][metric_col].values for g in unique_groups if len(clean_df[clean_df[group_col] == g]) >= 3]

    p_value = None
    f_stat = None
    if len(group_arrays) >= 2:
        try:
            f_stat, p_value = stats.f_oneway(*group_arrays)
            p_value = float(p_value)
            f_stat = float(f_stat)
        except Exception:
            pass

    # Cohen's d between Top Group and Bottom Group
    cohens_d = None
    if len(unique_groups) >= 2:
        top_grp = grouped.iloc[0][group_col]
        bot_grp = grouped.iloc[-1][group_col]
        s1 = clean_df[clean_df[group_col] == top_grp][metric_col].values
        s2 = clean_df[clean_df[group_col] == bot_grp][metric_col].values
        if len(s1) >= 2 and len(s2) >= 2:
            n1, n2 = len(s1), len(s2)
            var1, var2 = np.var(s1, ddof=1), np.var(s2, ddof=1)
            pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            if pooled_std > 0:
                cohens_d = round(float((np.mean(s1) - np.mean(s2)) / pooled_std), 2)

    return {
        "groups_table": grouped,
        "overall_mean": round(float(overall_mean), 2),
        "total_volume": round(float(total_sum), 2),
        "anova_f_stat": round(f_stat, 2) if f_stat is not None else None,
        "anova_p_value": round(p_value, 4) if p_value is not None else None,
        "is_statistically_significant": (p_value < 0.05) if p_value is not None else False,
        "cohens_d": cohens_d
    }


def calculate_pareto_curve(
    df: pd.DataFrame,
    category_col: str,
    measure_col: str
) -> pd.DataFrame:
    """Compute Pareto 80/20 concentration ranking table."""
    if df is None or category_col not in df.columns or measure_col not in df.columns:
        return pd.DataFrame()

    clean_df = df.dropna(subset=[category_col, measure_col]).copy()
    clean_df[measure_col] = pd.to_numeric(clean_df[measure_col], errors="coerce").fillna(0)

    grouped = clean_df.groupby(category_col)[measure_col].sum().reset_index()
    grouped = grouped.sort_values(by=measure_col, ascending=False).reset_index(drop=True)

    total_val = grouped[measure_col].sum()
    if total_val == 0:
        return grouped

    grouped["share_pct"] = (grouped[measure_col] / total_val) * 100.0
    grouped["cumulative_share_pct"] = grouped["share_pct"].cumsum()
    grouped["is_top_80pct"] = grouped["cumulative_share_pct"] <= 80.0

    return grouped
