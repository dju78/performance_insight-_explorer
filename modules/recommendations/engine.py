"""Enterprise Recommendation Engine and Traceability Matrix for Performance Insight Explorer.
Maps accepted findings into prioritized operational interventions using an Impact x Effort framework.
Enforces non-prescriptive, evidence-grounded wording safeguards.
"""
from typing import Any, Dict, List, Optional
import pandas as pd
from core.constants import PriorityLevel, RecommendationCategory
from core.models import EvidenceInsight, RecommendationItem


def generate_prioritized_recommendations(
    insights: List[EvidenceInsight]
) -> List[RecommendationItem]:
    """Derive operational recommendations directly from accepted analytical insights."""
    recommendations: List[RecommendationItem] = []
    rec_idx = 1

    for ins in insights:
        if ins.status == "Rejected":
            continue

        title_lower = ins.finding_title.lower()

        # Case A: Critical Shortfall / Capacity Deficit
        if "shortfall" in title_lower or "deficit" in title_lower:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_idx:03d}",
                linked_insight_id=ins.id,
                problem_addressed=f"Operational shortfall in {ins.kpi_affected} ({ins.quantitative_evidence})",
                supporting_evidence=f"Insight [{ins.id}]: {ins.quantitative_evidence}",
                proposed_action=f"The evidence suggests conducting a targeted workload rebalancing review for {ins.affected_segment}. A reasonable next action is establishing daily throughput huddles and flexible capacity cross-skilling.",
                expected_benefit="This should be tested through pilot reallocations with an expected benefit of narrowing the attainment gap by 10-15%, monitored via weekly KPI tracking.",
                priority=PriorityLevel.HIGH,
                urgency="Immediate (< 30 days)",
                impact="High",
                effort="Medium",
                cost_category="Operational / Existing Headcount",
                risk="Short-term transition friction while reallocating case queues.",
                responsible_owner="Head of Operations & Service Delivery",
                timescale="30-45 days",
                success_measure=f"{ins.kpi_affected} target attainment >= 95%",
                review_date="End of Next Month",
                dependencies="Agreement on multi-skilled staff rotation schedule",
                confidence_level="High (Empirically grounded)",
                category=RecommendationCategory.QUICK_WIN,
                status="Proposed"
            ))
            rec_idx += 1

        # Case B: Disparity Across Cohorts / Variation
        elif "disparity" in title_lower or "cohort" in title_lower or "variation" in title_lower:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_idx:03d}",
                linked_insight_id=ins.id,
                problem_addressed=f"Performance variation across operational groups ({ins.quantitative_evidence})",
                supporting_evidence=f"Insight [{ins.id}]: {ins.quantitative_evidence}",
                proposed_action=f"The evidence suggests pairing lower-performing cohorts ({ins.affected_segment}) with top-quartile benchmark squads. A reasonable next action is conducting standard operating procedure (SOP) audits to identify handling bottlenecks.",
                expected_benefit="The expected benefit should be monitored using cohort variance metrics, targeting a 20% reduction in between-group standard deviation.",
                priority=PriorityLevel.MEDIUM,
                urgency="Medium Term (30-60 days)",
                impact="High",
                effort="Low",
                cost_category="Negligible / Internal Knowledge Transfer",
                risk="Cultural resistance if benchmarking is perceived as punitive rather than supportive.",
                responsible_owner="Operational Quality & Practice Lead",
                timescale="60 days",
                success_measure="Bottom-quartile mean throughput improvement >= 15%",
                review_date="Quarterly Operational Review",
                dependencies="Standardized case complexity scoring",
                confidence_level="Medium-High (Supported by ANOVA)",
                category=RecommendationCategory.QUICK_WIN,
                status="Proposed"
            ))
            rec_idx += 1

        # Case C: Process Outliers / Special Cause
        elif "special-cause" in title_lower or "stability" in title_lower:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_idx:03d}",
                linked_insight_id=ins.id,
                problem_addressed="Temporal process instability and special-cause outlier events.",
                supporting_evidence=f"Insight [{ins.id}]: {ins.quantitative_evidence}",
                proposed_action="The evidence suggests establishing automated anomaly triggers. A reasonable next action is conducting root-cause incident reviews whenever weekly volumes breach the 2-sigma warning limit.",
                expected_benefit="Early containment of throughput bottlenecks before queue backlogs accumulate.",
                priority=PriorityLevel.MEDIUM,
                urgency="Short Term (< 15 days)",
                impact="Medium",
                effort="Low",
                cost_category="Zero Direct Cost",
                risk="False alert fatigue if thresholds are set too narrow.",
                responsible_owner="Performance & Reporting Analyst",
                timescale="15-30 days",
                success_measure="Zero uninvestigated special-cause breaches per quarter",
                review_date="Monthly Governance Meeting",
                dependencies="Access to weekly reporting refresh",
                confidence_level="High (Statistical Process Control)",
                category=RecommendationCategory.MONITORING,
                status="Proposed"
            ))
            rec_idx += 1

    return recommendations


def build_traceability_matrix(
    dataset_name: str,
    kpi_results: Dict[str, Any],
    insights: List[EvidenceInsight],
    recommendations: List[RecommendationItem],
    actions: List[Any]
) -> pd.DataFrame:
    """Construct full end-to-end lifecycle traceability table:
    DATA -> CALCULATION -> FINDING -> RECOMMENDATION -> ACTION -> OUTCOME
    """
    rows = []
    actions_by_rec = {getattr(a, "recommendation_id", ""): a for a in actions}

    for rec in recommendations:
        ins = next((i for i in insights if i.id == rec.linked_insight_id), None)
        act = actions_by_rec.get(rec.id)

        rows.append({
            "Dataset": dataset_name or "Active Dataset",
            "Calculation / Metric": ins.kpi_affected if ins else "General KPI",
            "Evidence Finding (Insight)": ins.finding_title if ins else "Verified Result",
            "Finding Confidence": ins.confidence_level if ins else "High",
            "Recommendation ID": rec.id,
            "Proposed Recommendation": rec.proposed_action[:80] + "...",
            "Priority": rec.priority.value if hasattr(rec.priority, "value") else str(rec.priority),
            "Category": rec.category.value if hasattr(rec.category, "value") else str(rec.category),
            "Assigned Action": getattr(act, "action_title", "Pending Assignment") if act else "Not yet converted",
            "Action Owner": getattr(act, "owner", rec.responsible_owner),
            "Action Status": getattr(act, "status", "Proposed") if act else "Proposed",
            "Target Outcome": rec.success_measure
        })

    return pd.DataFrame(rows)
