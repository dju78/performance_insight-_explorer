"""Deterministic Evidence-Based Insight Engine for Performance Insight Explorer.
Generates rigorous, data-backed insights directly from verified KPI results and statistical tests.
No external LLM dependency required for complete deterministic generation.
"""
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from core.models import EvidenceInsight


def generate_deterministic_insights(
    kpi_results: Dict[str, Any],
    comparisons: Optional[Dict[str, Any]] = None,
    trends: Optional[pd.DataFrame] = None,
    qa_report: Optional[Dict[str, Any]] = None
) -> List[EvidenceInsight]:
    """Derive structured evidence insights from verified session computations."""
    insights: List[EvidenceInsight] = []
    insight_idx = 1

    # 1. Target Shortfall Insights
    for kpi_id, res in kpi_results.items():
        var_pct = res.get("variance_pct")
        var_num = res.get("variance")
        actual = res.get("actual")
        target = res.get("target")
        status = res.get("status", "")
        unit = res.get("unit", "")
        name = res.get("name", kpi_id)

        if "Red" in status and var_pct is not None and target is not None:
            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Critical Shortfall in '{name}' Against Target Standard",
                quantitative_evidence=f"Observed performance of {actual:,.1f} {unit} trails target standard of {target:,.1f} {unit} by {abs(var_pct):.1f}% (Deficit: {var_num:+,.1f} {unit}).",
                kpi_affected=name,
                variance_or_gap_size=round(float(var_pct), 2),
                time_period="Overall Reporting Period",
                affected_segment="Enterprise-Wide",
                confidence_level="High (Verified Calculation)",
                business_significance="Critical Operational Risk",
                data_quality_caveat="Ensure target standard has been calibrated for current operating conditions.",
                statistical_limitation="Aggregate variance does not isolate subgroup heterogeneity.",
                suggested_follow_up="Drill down into cohort comparisons and driver correlation tree.",
                status="Active"
            ))
            insight_idx += 1

        elif "Green" in status and var_pct is not None and target is not None:
            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Target Standard Exceeded in '{name}'",
                quantitative_evidence=f"Delivered {actual:,.1f} {unit} exceeding target benchmark of {target:,.1f} {unit} by {var_pct:+.1f}%.",
                kpi_affected=name,
                variance_or_gap_size=round(float(var_pct), 2),
                time_period="Overall Reporting Period",
                affected_segment="Enterprise-Wide",
                confidence_level="High (Verified Calculation)",
                business_significance="Positive Benchmark Achievement",
                data_quality_caveat="Verify whether target represents an ambitious stretch or conservative baseline.",
                statistical_limitation="Sustained attainment requires longitudinal process stability check.",
                suggested_follow_up="Benchmark high-performing practices for cross-team dissemination.",
                status="Active"
            ))
            insight_idx += 1

    # 2. Group Variance & Disparity Insights
    if comparisons and "groups_table" in comparisons:
        gt = comparisons["groups_table"]
        p_val = comparisons.get("anova_p_value")
        cohen = comparisons.get("cohens_d")
        if isinstance(gt, pd.DataFrame) and len(gt) >= 2:
            top_row = gt.iloc[0]
            bot_row = gt.iloc[-1]
            gap_pct = ((top_row["mean"] - bot_row["mean"]) / max(bot_row["mean"], 0.001)) * 100.0

            sig_text = f"(Statistically significant, p={p_val:.4f}, Cohen's d={cohen})" if p_val and p_val < 0.05 else "(Observational difference)"

            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Significant Performance Disparity Across Operational Cohorts",
                quantitative_evidence=f"Top group '{top_row.iloc[0]}' ({top_row['mean']:.1f}) outperforms lowest group '{bot_row.iloc[0]}' ({bot_row['mean']:.1f}) by {gap_pct:.1f}% {sig_text}.",
                kpi_affected="Comparative Throughput / Output",
                variance_or_gap_size=round(float(gap_pct), 2),
                time_period="Reporting Period",
                affected_segment=f"Lowest Cohort: {bot_row.iloc[0]}",
                confidence_level="High (Empirical Comparison)" if p_val and p_val < 0.05 else "Medium (Indicative)",
                business_significance="Material Efficiency Opportunity",
                data_quality_caveat="Confirm case mix complexity is equivalent between compared cohorts.",
                statistical_limitation="Bivariate comparison does not control for confounding staff experience.",
                suggested_follow_up="Conduct 5-Whys and operational interview on lowest-performing cohort.",
                status="Active"
            ))
            insight_idx += 1

    # 3. Time-Series Volatility / Special Cause
    if trends is not None and isinstance(trends, pd.DataFrame) and "is_special_cause" in trends.columns:
        special_causes = trends[trends["is_special_cause"] == True]
        if len(special_causes) > 0:
            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Special-Cause Variation Detected in Time Series",
                quantitative_evidence=f"Identified {len(special_causes)} period(s) breaching 3-sigma statistical process control limits.",
                kpi_affected="Process Stability",
                variance_or_gap_size=round(float(len(special_causes)), 1),
                time_period="Observed Time Series",
                affected_segment="Temporal Outlier Periods",
                confidence_level="High (Statistical Process Control)",
                business_significance="Operational Stability Anomaly",
                data_quality_caveat="Confirm whether outlier points coincided with system outages or policy changes.",
                statistical_limitation="Control charts assume approximate normality of subgroup means.",
                suggested_follow_up="Investigate operational events on special-cause dates.",
                status="Active"
            ))
            insight_idx += 1

    return insights


def normalize_finding(item: Any) -> Optional[Dict[str, Any]]:
    """Safely normalise finding from dataclass, dict, or string into a standardized dict."""
    if item is None:
        return None

    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None
        return {
            "title": text[:60] + ("..." if len(text) > 60 else ""),
            "evidence_level": "Not assessed",
            "description": text,
            "metric": "Operational Performance",
            "where": "Enterprise-Wide",
            "when": "Overall Period",
            "impact": "General performance insight",
            "limitation": "Derived from summary text record"
        }

    def _extract(key_list: List[str], default: str = "") -> str:
        for k in key_list:
            if isinstance(item, dict) and k in item and item[k] is not None:
                return str(item[k]).strip()
            elif hasattr(item, k) and getattr(item, k) is not None:
                return str(getattr(item, k)).strip()
        return default

    title = _extract(["finding_title", "title", "name", "headline", "summary"], default="Performance Finding")
    evidence_level = _extract(["confidence_level", "evidence_level", "confidence", "evidence_tier", "strength"], default="Not assessed")
    description = _extract(["quantitative_evidence", "observation", "description", "details", "text", "body", "finding"], default="")
    metric = _extract(["kpi_affected", "metric", "kpi", "measure", "metric_name"], default="Operational Performance")
    where = _extract(["affected_segment", "where", "segment", "group", "cohort", "dimension"], default="Enterprise-Wide")
    when = _extract(["time_period", "when", "period", "date_range", "timeline"], default="Overall Period")
    impact = _extract(["business_significance", "business_impact", "impact", "severity", "significance"], default="Material Operational Observation")
    limitation = _extract(["statistical_limitation", "limitations_disclosure", "data_quality_caveat", "limitation", "caveat"], default="Observational findings subject to data completeness")

    return {
        "title": title or "Performance Finding",
        "evidence_level": evidence_level or "Not assessed",
        "description": description,
        "metric": metric,
        "where": where,
        "when": when,
        "impact": impact,
        "limitation": limitation
    }


def normalize_recommendation(item: Any) -> Optional[Dict[str, Any]]:
    """Safely normalise recommendation from dataclass, dict, or string into a standardized dict."""
    if item is None:
        return None

    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None
        return {
            "id": "REC-001",
            "title": text[:60] + ("..." if len(text) > 60 else ""),
            "problem": text,
            "proposed_action": text,
            "expected_benefit": "Operational improvement",
            "impact": "Medium",
            "effort": "Medium",
            "owner": "Operations Lead",
            "timescale": "30-60 days",
            "priority": "High"
        }

    def _extract(key_list: List[str], default: str = "") -> str:
        for k in key_list:
            if isinstance(item, dict) and k in item and item[k] is not None:
                return str(item[k]).strip()
            elif hasattr(item, k) and getattr(item, k) is not None:
                val = getattr(item, k)
                if hasattr(val, "value"):
                    return str(val.value).strip()
                return str(val).strip()
        return default

    rec_id = _extract(["id", "rec_id", "code"], default="REC-001")
    title = _extract(["title", "name", "action_title", "headline"], default="Recommended Operational Action")
    problem = _extract(["problem_addressed", "problem", "issue", "rationale", "title"], default="Operational performance variance")
    proposed_action = _extract(["proposed_action", "action", "recommendation", "treatment", "proposed_intervention"], default="")
    expected_benefit = _extract(["expected_benefit", "benefit", "outcome", "target_outcome"], default="Targeted efficiency gain")
    impact = _extract(["impact", "impact_level"], default="High")
    effort = _extract(["effort", "effort_level"], default="Medium")
    owner = _extract(["responsible_owner", "owner", "owner_role", "assignee"], default="Operations Lead")
    timescale = _extract(["timescale", "timeframe", "target_milestone", "due_date"], default="30-60 days")
    priority = _extract(["priority", "priority_level"], default="High")

    return {
        "id": rec_id,
        "title": title or "Recommended Action",
        "problem": problem,
        "proposed_action": proposed_action or problem,
        "expected_benefit": expected_benefit,
        "impact": impact,
        "effort": effort,
        "owner": owner,
        "timescale": timescale,
        "priority": priority
    }
