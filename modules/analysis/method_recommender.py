"""Method Selection & Analytical Recommendation Engine.
Recommends appropriate statistical, diagnostic, and operational methods based on data shape,
distributions, sample sizes, and user questions.
"""
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def recommend_analytical_methods(
    df: pd.DataFrame,
    confirmed_mappings: Dict[str, str],
    business_question: str = ""
) -> List[Dict[str, Any]]:
    """Analyze active dataset characteristics and produce prioritized analytical method recommendations."""
    if df is None or len(df) == 0:
        return []

    recommendations: List[Dict[str, Any]] = []
    row_count = len(df)
    cols = df.columns.tolist()

    has_date = any(role in ["date", "reporting_period"] for role in confirmed_mappings.values())
    has_groups = any(role in ["team", "department", "region", "product_service", "customer_segment"] for role in confirmed_mappings.values())
    has_measures = any(role in ["actual", "volume_inflow", "cost", "revenue", "quality_measure", "duration_wait_time"] for role in confirmed_mappings.values())
    has_target = any(role in ["target", "benchmark"] for role in confirmed_mappings.values())
    has_capacity = any(role in ["capacity_fte"] for role in confirmed_mappings.values())

    # 1. Target & Benchmark Variance Analysis
    if has_target and has_measures:
        recommendations.append({
            "method_name": "Target & Benchmark Variance Analysis",
            "category": "Performance Measurement",
            "suitability": "Highly Recommended",
            "confidence": 0.95,
            "rationale": "Dataset contains mapped targets/benchmarks and actual measures. Enables RAG tracking and attainment gap quantification.",
            "assumptions": ["Targets represent comparable operational standards across units."],
            "deliverables": ["Actual vs Target Variance Table", "Attainment Rate %", "RAG Scorecard"]
        })

    # 2. Time-Series & Run Control Charts
    if has_date and has_measures:
        recommendations.append({
            "method_name": "Statistical Process Control & Trend Analysis",
            "category": "Time-Series Diagnostics",
            "suitability": "Highly Recommended",
            "confidence": 0.90,
            "rationale": "Chronological dates and measures detected. Suitable for detecting common-cause vs special-cause variation and structural breaks.",
            "assumptions": ["Equally spaced reporting intervals without major unrecorded missing periods."],
            "deliverables": ["Shewhart Run Chart", "Period-over-Period Growth", "Trend Decomposition"]
        })

    # 3. Cohort Comparison & Variance Decomposition
    if has_groups and has_measures:
        recommendations.append({
            "method_name": "Group Comparison & Variance Decomposition",
            "category": "Comparative Analysis",
            "suitability": "Highly Recommended",
            "confidence": 0.88,
            "rationale": "Categorical organizational dimensions detected. Enables ranking, quartile segmentation, and ANOVA / Cohen's d effect size tests.",
            "assumptions": ["Sufficient sample size per group (n >= 5) to ensure statistical reliability."],
            "deliverables": ["Quartile Performance Ranking", "Between-Group Variance %", "Statistical Significance p-values"]
        })

    # 4. Operational Productivity & Capacity Utilization
    if has_capacity and has_measures:
        recommendations.append({
            "method_name": "Capacity Utilization & Unit Productivity",
            "category": "Operational Efficiency",
            "suitability": "Recommended",
            "confidence": 0.85,
            "rationale": "Workforce / FTE capacity fields detected. Allows calculation of throughput per FTE and workload pressure ratios.",
            "assumptions": ["FTE figures reflect net available hours rather than nominal contracted headcount."],
            "deliverables": ["Output per FTE", "Capacity Utilization %", "Staffing Deficit Estimates"]
        })

    # 5. Diagnostic Regression & Driver Tree Analysis
    if len(cols) >= 4 and has_measures:
        recommendations.append({
            "method_name": "Multivariate Driver Regression & Root Cause",
            "category": "Diagnostic Analysis",
            "suitability": "Recommended",
            "confidence": 0.80,
            "rationale": "Multi-attribute dataset allows regression modeling to identify primary variance drivers.",
            "assumptions": ["Linearity, independence of residuals, and absence of extreme multicollinearity."],
            "deliverables": ["Feature Importance Ranking", "R-squared Variance Explained", "Driver Impact Trees"]
        })

    # 6. Pareto 80/20 Concentration Analysis
    if has_measures and has_groups:
        recommendations.append({
            "method_name": "Pareto 80/20 Concentration Analysis",
            "category": "Operational Analysis",
            "suitability": "Useful",
            "confidence": 0.75,
            "rationale": "Identifies the critical 20% of teams, cases, or failure categories driving 80% of volume or backlog.",
            "assumptions": ["Discrete non-negative volume or cost distributions."],
            "deliverables": ["Cumulative Pareto Curve", "Top Contributor List"]
        })

    return recommendations
