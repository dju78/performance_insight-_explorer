"""Statistical and Quantitative Analysis Engine for Performance Insight Explorer.
Calculates descriptive distributions, time-series run charts / control limits, group comparisons with effect sizes,
and Pareto concentration curves.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


def calculate_descriptive_stats(
    series_or_df: Union[pd.Series, pd.DataFrame],
    col: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate comprehensive robust summary statistics for a numeric series or dataframe column."""
    if isinstance(series_or_df, pd.DataFrame):
        if col and col in series_or_df.columns:
            clean_s = pd.to_numeric(series_or_df[col], errors="coerce").dropna()
        else:
            return {"n": 0}
    else:
        clean_s = pd.to_numeric(series_or_df, errors="coerce").dropna()
        
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
    """Calculate Shewhart Statistical Process Control (SPC) / Run Chart limits (CL, UCL, LCL).
    
    Robust against:
    - Identical date and metric columns (e.g. Unnamed: 0)
    - Non-numeric or missing metric data
    - Invalid or unparseable timestamps
    - Single-period or empty data
    - Never raises unhandled exceptions to UI
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
        
    if not date_col or not metric_col:
        return pd.DataFrame()

    if date_col not in df.columns or metric_col not in df.columns:
        return pd.DataFrame()

    # Disallow identical columns for date and metric
    if str(date_col).strip() == str(metric_col).strip():
        return pd.DataFrame()

    try:
        # Build clean two-column working frame with synthetic internal keys to prevent groupby index collisions
        temp_df = pd.DataFrame({
            "__ds__": df[date_col],
            "__y__": df[metric_col]
        })

        temp_df["__y__"] = pd.to_numeric(temp_df["__y__"], errors="coerce")
        temp_df["__ds__"] = pd.to_datetime(temp_df["__ds__"], errors="coerce", format="mixed")
        temp_df = temp_df.dropna(subset=["__ds__", "__y__"])

        if len(temp_df) == 0:
            return pd.DataFrame()

        # Group by parsed date safely
        if aggregation == "sum":
            grouped = temp_df.groupby("__ds__", as_index=False)["__y__"].sum()
        else:
            grouped = temp_df.groupby("__ds__", as_index=False)["__y__"].mean()

        grouped = grouped.sort_values(by="__ds__").reset_index(drop=True)
        if len(grouped) == 0:
            return pd.DataFrame()

        # Rename back to requested column names
        grouped.columns = [date_col, metric_col]

        center_line = float(grouped[metric_col].mean())
        stdev = float(grouped[metric_col].std(ddof=1)) if len(grouped) > 1 else 0.0
        if np.isnan(stdev):
            stdev = 0.0

        grouped["center_line"] = center_line
        grouped["ucl_3sigma"] = center_line + (3.0 * stdev)
        grouped["lcl_3sigma"] = max(0.0, center_line - (3.0 * stdev))
        grouped["warn_upper_2sigma"] = center_line + (2.0 * stdev)
        grouped["warn_lower_2sigma"] = max(0.0, center_line - (2.0 * stdev))

        # Identify special cause outliers
        grouped["is_special_cause"] = (grouped[metric_col] > grouped["ucl_3sigma"]) | (grouped[metric_col] < grouped["lcl_3sigma"])
        grouped["mom_change_pct"] = grouped[metric_col].pct_change() * 100.0
        grouped["mom_change_pct"] = grouped["mom_change_pct"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

        return grouped
    except Exception:
        return pd.DataFrame()


def calculate_group_comparison_statistics(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str
) -> Dict[str, Any]:
    """Calculate between-group comparisons, rankings, variance contributions, and statistical tests."""
    empty_res = {"groups_table": pd.DataFrame(), "anova_p_value": None, "cohens_d": None}
    if df is None or len(df) == 0:
        return empty_res
    if not group_col or not metric_col:
        return empty_res
    if group_col not in df.columns or metric_col not in df.columns:
        return empty_res
    if str(group_col).strip() == str(metric_col).strip():
        return empty_res

    try:
        temp_df = pd.DataFrame({
            "__grp__": df[group_col].astype(str),
            "__y__": pd.to_numeric(df[metric_col], errors="coerce")
        }).dropna(subset=["__grp__", "__y__"])

        if len(temp_df) == 0:
            return empty_res

        # Group summaries
        grouped = temp_df.groupby("__grp__", as_index=False)["__y__"].agg(
            count="count",
            sum="sum",
            mean="mean",
            std="std",
            median="median",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75)
        )
        grouped.rename(columns={"__grp__": group_col, "__y__": metric_col}, inplace=True)

        overall_mean = temp_df["__y__"].mean()
        total_sum = temp_df["__y__"].sum()

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
        unique_groups = temp_df["__grp__"].unique()
        group_arrays = [temp_df[temp_df["__grp__"] == g]["__y__"].values for g in unique_groups if len(temp_df[temp_df["__grp__"] == g]) >= 3]

        p_value = None
        f_stat = None
        if len(group_arrays) >= 2:
            try:
                f_stat, p_value = stats.f_oneway(*group_arrays)
                p_value = float(p_value) if not np.isnan(p_value) else None
                f_stat = float(f_stat) if not np.isnan(f_stat) else None
            except Exception:
                p_value = None
                f_stat = None
            pass

        # Cohen's d between Top Group and Bottom Group
        cohens_d = None
        if len(unique_groups) >= 2:
            top_grp = grouped.iloc[0][group_col]
            bot_grp = grouped.iloc[-1][group_col]
            s1 = temp_df[temp_df["__grp__"] == top_grp]["__y__"].values
            s2 = temp_df[temp_df["__grp__"] == bot_grp]["__y__"].values
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
    except Exception:
        return empty_res


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
