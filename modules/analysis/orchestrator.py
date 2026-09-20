"""Automated Performance Analysis Orchestrator.
Coordinates the end-to-end analytical pipeline:
1. Quality scoring
2. Descriptive statistics
3. Time-series & Shewhart SPC trends
4. Cohort comparisons & ANOVA significance
5. Actual vs Target achievement
6. Driver diagnostics & regression
7. Pareto concentration
8. Deterministic findings tied to user objective
9. Practical prioritized recommendations
10. Executive summary synthesis
"""
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from core.security import is_index_like_column
from modules.quality.engine import evaluate_data_quality_10d
from modules.analysis.stats_engine import (
    calculate_descriptive_stats,
    calculate_control_chart_limits,
    calculate_group_comparison_statistics,
    calculate_pareto_curve
)
from modules.diagnostics.root_cause_engine import (
    evaluate_driver_correlations,
    calculate_driver_importance_regression
)
from modules.insights.engine import generate_deterministic_insights
from modules.recommendations.engine import generate_prioritized_recommendations


def run_full_performance_analysis(
    df: pd.DataFrame,
    objective_text: str = "",
    specific_questions: str = "",
    date_col: Optional[str] = None,
    metric_col: Optional[str] = None,
    group_col: Optional[str] = None,
    target_val: Optional[float] = None,
    target_col: Optional[str] = None
) -> Dict[str, Any]:
    """Execute complete performance analysis pipeline and synthesize evidence results."""
    if df is None or len(df) == 0:
        return {"error": "No active dataset loaded."}

    results: Dict[str, Any] = {
        "objective": objective_text.strip() if objective_text else "General Performance Evaluation",
        "specific_questions": [q.strip() for q in specific_questions.split("\n") if q.strip()],
        "date_col": date_col,
        "metric_col": metric_col,
        "group_col": group_col,
        "target_val": target_val,
        "target_col": target_col
    }

    # 1. Data Quality Evaluation
    qa_report = evaluate_data_quality_10d(df)
    results["qa_report"] = qa_report
    results["health_score"] = qa_report.get("health_score", 100.0)

    # 2. Metric Verification & Descriptive Statistics
    if metric_col and metric_col in df.columns:
        desc_stats = calculate_descriptive_stats(df, metric_col)
        results["descriptive_stats"] = desc_stats
        metric_mean = desc_stats.get("mean", 0.0)
        metric_median = desc_stats.get("median", 0.0)
        metric_std = desc_stats.get("std", 0.0)
    else:
        results["descriptive_stats"] = {}
        metric_mean, metric_median, metric_std = 0.0, 0.0, 0.0

    # 3. Time-Series & Statistical Process Control (SPC)
    spc_df = pd.DataFrame()
    if date_col and metric_col and date_col in df.columns and metric_col in df.columns and date_col != metric_col:
        spc_df = calculate_control_chart_limits(df, date_col, metric_col, aggregation="mean")
    results["spc_df"] = spc_df

    # 4. Cohort / Group Comparisons
    comp_results: Dict[str, Any] = {"groups_table": pd.DataFrame(), "anova_p_value": None, "cohens_d": None}
    if group_col and metric_col and group_col in df.columns and metric_col in df.columns and group_col != metric_col:
        comp_results = calculate_group_comparison_statistics(df, group_col, metric_col)
    results["comparison_results"] = comp_results

    # 5. Actual vs Target Analysis
    target_achievement_pct = None
    target_gap = None
    target_status = "No Target Configured"
    if target_val is not None and target_val > 0 and metric_mean > 0:
        target_achievement_pct = round((metric_mean / target_val) * 100.0, 1)
        target_gap = round(metric_mean - target_val, 2)
        if target_gap <= 0:
            target_status = f"On Target ({target_achievement_pct}% of benchmark)"
        else:
            target_status = f"Variance: {target_gap:+.2f} ({target_achievement_pct}% of benchmark)"
    elif target_col and target_col in df.columns and metric_col:
        t_clean = pd.to_numeric(df[target_col], errors="coerce").dropna()
        if len(t_clean) > 0:
            avg_t = t_clean.mean()
            if avg_t > 0:
                target_achievement_pct = round((metric_mean / avg_t) * 100.0, 1)
                target_gap = round(metric_mean - avg_t, 2)
                target_status = f"Avg Target: {avg_t:.1f} (Achievement: {target_achievement_pct}%)"

    results["target_achievement_pct"] = target_achievement_pct
    results["target_gap"] = target_gap
    results["target_status"] = target_status

    # 6. Driver Diagnostics & Correlations
    candidate_drivers = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c != metric_col and not is_index_like_column(c, df[c]) and not pd.api.types.is_bool_dtype(df[c])
    ]
    driver_results = []
    regression_summary = {}
    if metric_col and candidate_drivers:
        driver_results = evaluate_driver_correlations(df, metric_col, candidate_drivers[:6])
        regression_summary = calculate_driver_importance_regression(df, metric_col, candidate_drivers[:6])
    results["driver_results"] = driver_results
    results["regression_summary"] = regression_summary

    # 7. Pareto Concentration
    pareto_df = pd.DataFrame()
    if group_col and metric_col and group_col in df.columns and metric_col in df.columns:
        pareto_df = calculate_pareto_curve(df, group_col, metric_col)
    results["pareto_df"] = pareto_df

    # 8. Deterministic Findings & Insights
    findings = []
    if metric_col:
        kpi_dict = {
            metric_col: {
                "name": metric_col,
                "actual": metric_mean,
                "target": target_val,
                "variance": target_gap,
                "variance_pct": round(((metric_mean - target_val) / target_val * 100.0), 1) if target_val and target_val > 0 else None,
                "status": "Red (Underperforming)" if target_val and metric_mean > target_val else ("Green (On Target)" if target_val else "Evaluated"),
                "unit": "Units"
            }
        }
        findings = generate_deterministic_insights(
            kpi_results=kpi_dict,
            comparisons=comp_results,
            trends=spc_df,
            qa_report=qa_report
        )
    results["findings"] = findings

    # 9. Prioritized Recommendations
    recommendations = []
    if findings:
        recommendations = generate_prioritized_recommendations(findings)
    results["recommendations"] = recommendations

    # 10. Synthesize Executive Performance Summary
    # Main result
    main_result = f"Analyzed {len(df):,} records for '{metric_col or 'Operational Performance'}'. Mean: {metric_mean:,.2f} (Median: {metric_median:,.2f}, Std: {metric_std:,.2f})."
    
    # Strongest and Weakest areas
    groups_tbl = comp_results.get("groups_table", pd.DataFrame())
    if not groups_tbl.empty and len(groups_tbl) >= 2:
        top_cohort = groups_tbl.iloc[0]
        bot_cohort = groups_tbl.iloc[-1]
        strongest_area = f"{top_cohort[group_col]} (Mean: {top_cohort['mean']:,.2f})"
        weakest_area = f"{bot_cohort[group_col]} (Mean: {bot_cohort['mean']:,.2f})"
    else:
        strongest_area = "Insufficient cohort groupings"
        weakest_area = "Insufficient cohort groupings"

    # Largest improvement & deterioration
    if not spc_df.empty and len(spc_df) >= 2 and "mom_change_pct" in spc_df.columns:
        valid_changes = spc_df.dropna(subset=["mom_change_pct"])
        if not valid_changes.empty:
            max_up = valid_changes.loc[valid_changes["mom_change_pct"].idxmax()]
            max_down = valid_changes.loc[valid_changes["mom_change_pct"].idxmin()]
            largest_deterioration = f"{max_up[date_col]} ({max_up['mom_change_pct']:+.1f}% jump)"
            largest_improvement = f"{max_down[date_col]} ({max_down['mom_change_pct']:+.1f}% drop)"
        else:
            largest_improvement = "Stable across periods"
            largest_deterioration = "Stable across periods"
    else:
        largest_improvement = "No time-series sequence"
        largest_deterioration = "No time-series sequence"

    # Important data quality warning
    issues = qa_report.get("issues", [])
    if issues:
        top_issue = issues[0]
        quality_warning = f"Quality Index: {qa_report.get('health_score', 100):.0f}/100 — {top_issue.get('rule_name', 'Warning')}: {top_issue.get('details', '')}"
    else:
        quality_warning = "Quality Index: 100/100 — High data hygiene, zero blocking anomalies detected."

    results["summary"] = {
        "main_result": main_result,
        "strongest_area": strongest_area,
        "weakest_area": weakest_area,
        "largest_improvement": largest_improvement,
        "largest_deterioration": largest_deterioration,
        "target_achievement": target_status,
        "quality_warning": quality_warning
    }

    return results
