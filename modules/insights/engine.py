"""Deterministic Insight and Evidence Synthesis Engine for Performance Insight Explorer.
Generates structured, traceable EvidenceInsight objects with explicit statistical caveats
and deterministic rule-based analysis.
"""
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from core.models import EvidenceInsight, KPIDefinition


def generate_deterministic_insights(
    kpi_results: Dict[str, Any],
    comparisons: Optional[Dict[str, Any]] = None,
    trends: Optional[pd.DataFrame] = None,
    qa_report: Optional[Dict[str, Any]] = None
) -> List[EvidenceInsight]:
    """Synthesize deterministic, evidence-grounded insights from analytical outputs."""
    insights: List[EvidenceInsight] = []
    insight_idx = 1
    comp_dict = comparisons or {}
    trends_df = trends if trends is not None else pd.DataFrame()

    # 1. KPI Target Variance Insights
    for kpi_id, kpi_data in kpi_results.items():
        status = kpi_data.get("status", "")
        variance_pct = kpi_data.get("variance_pct")
        variance_num = kpi_data.get("variance")
        actual = kpi_data.get("actual")
        target = kpi_data.get("target")

        if "Red" in status and variance_pct is not None:
            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Critical Target Shortfall in {kpi_data.get('name', kpi_id)}",
                quantitative_evidence=f"Observed value of {actual:,.2f} {kpi_data.get('unit', '')} breaches target of {target:,.2f} by {variance_pct:+.1f}% ({variance_num:+,.2f}).",
                kpi_affected=kpi_data.get("name", kpi_id),
                variance_or_gap_size=round(float(variance_pct), 1),
                time_period="Active Reporting Horizon",
                affected_segment="Overall Organization",
                confidence_level="High (Empirically Grounded)",
                business_significance="Critical Strategic Shortfall",
                data_quality_caveat="Ensure no missing periods or incomplete aggregations contributed to variance.",
                statistical_limitation="Point-in-time KPI variance does not evaluate autocorrelation or seasonal cycles.",
                suggested_follow_up=f"Perform root-cause driver decomposition on {kpi_id}.",
                status="Active"
            ))
            insight_idx += 1

        elif "Amber" in status and variance_pct is not None:
            insights.append(EvidenceInsight(
                id=f"INS-{insight_idx:03d}",
                finding_title=f"Warning / Approaching Threshold for {kpi_data.get('name', kpi_id)}",
                quantitative_evidence=f"Observed value of {actual:,.2f} is within warning tolerance band ({variance_pct:+.1f}% variance from target).",
                kpi_affected=kpi_data.get("name", kpi_id),
                variance_or_gap_size=round(float(variance_pct), 1),
                time_period="Active Reporting Horizon",
                affected_segment="Overall Organization",
                confidence_level="High (Empirically Grounded)",
                business_significance="Material Operational Risk",
                data_quality_caveat="Review underlying records for transient reporting lags.",
                statistical_limitation="Slight variance may be within normal process noise.",
                suggested_follow_up="Monitor next reporting cycle before initiating capital intervention.",
                status="Active"
            ))
            insight_idx += 1

    # 2. Cohort Comparison Disparity Insights
    groups_df = comp_dict.get("groups_table", pd.DataFrame())
    if not groups_df.empty and len(groups_df) >= 2 and "mean" in groups_df.columns:
        top_cohort = groups_df.iloc[0]
        bottom_cohort = groups_df.iloc[-1]
        spread = top_cohort["mean"] - bottom_cohort["mean"]
        spread_pct = (spread / max(bottom_cohort["mean"], 0.001)) * 100.0 if bottom_cohort["mean"] != 0 else 0.0

        p_val = comp_dict.get("anova_p_value")
        p_val_str = f" (ANOVA p={p_val:.4f})" if p_val is not None else ""

        insights.append(EvidenceInsight(
            id=f"INS-{insight_idx:03d}",
            finding_title=f"Significant Cohort Performance Disparity",
            quantitative_evidence=f"Top cohort '{top_cohort.iloc[0]}' ({top_cohort['mean']:,.2f}) outperforms lowest cohort '{bottom_cohort.iloc[0]}' ({bottom_cohort['mean']:,.2f}) by {spread_pct:.1f}% ({spread:,.2f} units){p_val_str}.",
            kpi_affected="Cohort Performance",
            variance_or_gap_size=round(float(spread), 2),
            time_period="Aggregated Evaluation Period",
            affected_segment=f"{bottom_cohort.iloc[0]} vs {top_cohort.iloc[0]}",
            confidence_level="High (Statistical ANOVA)" if (p_val is not None and p_val < 0.05) else "Medium (Descriptive Spread)",
            business_significance="Operational Disparity / Best-Practice Gap",
            data_quality_caveat="Verify case mix and complexity differences between cohorts.",
            statistical_limitation="Comparison assumes comparable operational environments and uniform data capture.",
            suggested_follow_up="Conduct 5-Whys and operational review on lowest-performing cohort.",
            status="Active"
        ))
        insight_idx += 1

    # 3. SPC Special-Cause Variation Insights
    if not trends_df.empty and "is_special_cause" in trends_df.columns:
        special_causes = trends_df[trends_df["is_special_cause"] == True]
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
            "limitation": "Derived from summary text record",
            "status": "Active"
        }

    def _extract(key_list: List[str], default: str = "") -> str:
        for k in key_list:
            if isinstance(item, dict) and k in item and item[k] is not None:
                return str(item[k]).strip()
            elif hasattr(item, k) and getattr(item, k) is not None:
                return str(getattr(item, k)).strip()
        return default

    title = _extract(["finding_title", "title", "finding", "name", "headline", "summary"], default="Performance Finding")
    evidence_level = _extract(["confidence_level", "evidence_level", "confidence", "evidence_tier", "strength"], default="Not assessed")
    description = _extract(["quantitative_evidence", "observation", "description", "details", "text", "body", "finding", "problem"], default="")
    metric = _extract(["kpi_affected", "metric", "kpi", "measure", "metric_name"], default="Operational Performance")
    where = _extract(["affected_segment", "where", "segment", "group", "cohort", "dimension"], default="Enterprise-Wide")
    when = _extract(["time_period", "when", "period", "date_range", "timeline"], default="Overall Period")
    impact = _extract(["business_significance", "business_impact", "impact", "severity", "significance"], default="Material Operational Observation")
    limitation = _extract(["statistical_limitation", "limitations_disclosure", "data_quality_caveat", "limitation", "caveat"], default="Observational findings subject to data completeness")
    status = _extract(["status", "review_status"], default="Active")

    return {
        "title": title or "Performance Finding",
        "evidence_level": evidence_level or "Not assessed",
        "description": description or title,
        "metric": metric,
        "where": where,
        "when": when,
        "impact": impact,
        "limitation": limitation,
        "status": status
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
            "priority": "High",
            "status": "Proposed"
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
    title = _extract(["title", "action_title", "headline", "name", "problem_addressed", "problem", "proposed_action", "action", "recommendation"], default="Recommended Operational Action")
    problem = _extract(["problem_addressed", "problem", "issue", "rationale", "title"], default="Operational performance variance")
    proposed_action = _extract(["proposed_action", "action", "recommendation", "treatment", "proposed_intervention"], default="")
    expected_benefit = _extract(["expected_benefit", "benefit", "outcome", "target_outcome"], default="Targeted efficiency gain")
    impact = _extract(["impact", "impact_level"], default="High")
    effort = _extract(["effort", "effort_level"], default="Medium")
    owner = _extract(["responsible_owner", "owner", "owner_role", "assignee"], default="Operations Lead")
    timescale = _extract(["timescale", "timeframe", "target_milestone", "due_date"], default="30-60 days")
    priority = _extract(["priority", "priority_level"], default="High")
    status = _extract(["status", "approval_status"], default="Proposed")

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
        "priority": priority,
        "status": status
    }
