"""Action Tracking and Benefits Realization Engine for Performance Insight Explorer.
Manages enterprise action registries, status lifecycles, and before-versus-after benefits realization.
Enforces explicit causality warnings on observed metric changes.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from core.constants import ActionStatus, PriorityLevel
from core.models import ActionItem, RecommendationItem


def convert_recommendation_to_action(
    rec: RecommendationItem,
    action_title: str,
    action_desc: str,
    owner: str,
    dept: str,
    due_date: str,
    baseline_val: Optional[float] = None,
    expected_val: Optional[float] = None
) -> ActionItem:
    """Instantiate a new tracked action item linked to an approved recommendation."""
    action_id = f"ACT-{pd.Timestamp.now().strftime('%m%d%H%M%S')}"
    return ActionItem(
        id=action_id,
        recommendation_id=rec.id,
        action_title=action_title or f"Implement {rec.category.value}: {rec.id}",
        action_description=action_desc or rec.proposed_action,
        owner=owner or rec.responsible_owner,
        department=dept or "Operations",
        priority=rec.priority,
        status=ActionStatus.NOT_STARTED,
        due_date=due_date or rec.review_date,
        kpi_affected=rec.success_measure,
        baseline_value=baseline_val,
        expected_result=expected_val,
        actual_result=None,
        progress_notes="Action logged from approved recommendation.",
        review_date=rec.review_date
    )


def evaluate_benefits_realization(actions: List[ActionItem]) -> Dict[str, Any]:
    """Compute realization progress and variance across all tracked action items."""
    if not actions:
        return {
            "summary_table": pd.DataFrame(),
            "total_actions": 0,
            "completed_count": 0,
            "in_progress_count": 0,
            "blocked_count": 0,
            "realization_rate_pct": 0.0,
            "causality_caveat": "CAUSALITY DISCLAIMER: Post-implementation changes reflect observed associations and cannot be interpreted as definitive causal proof without controlled experimentation."
        }

    rows = []
    completed_cnt = 0
    in_prog_cnt = 0
    blocked_cnt = 0

    for a in actions:
        st_val = a.status.value if hasattr(a.status, "value") else str(a.status)
        if st_val == ActionStatus.COMPLETED.value:
            completed_cnt += 1
        elif st_val == ActionStatus.IN_PROGRESS.value:
            in_prog_cnt += 1
        elif st_val == ActionStatus.BLOCKED.value:
            blocked_cnt += 1

        baseline = a.baseline_value
        expected = a.expected_result
        actual = a.actual_result

        benefit_achieved_pct = None
        if baseline is not None and expected is not None and actual is not None:
            expected_change = expected - baseline
            actual_change = actual - baseline
            if expected_change != 0:
                benefit_achieved_pct = round((actual_change / expected_change) * 100.0, 1)

        rows.append({
            "Action ID": a.id,
            "Action Title": a.action_title,
            "Owner": a.owner,
            "Department": a.department,
            "Priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
            "Status": st_val,
            "Due Date": a.due_date,
            "Target KPI": a.kpi_affected,
            "Baseline Value": baseline,
            "Expected Target": expected,
            "Actual Result": actual,
            "Realization %": f"{benefit_achieved_pct}%" if benefit_achieved_pct is not None else "Pending Actuals"
        })

    realization_rate = (completed_cnt / len(actions) * 100.0) if actions else 0.0

    return {
        "summary_table": pd.DataFrame(rows),
        "total_actions": len(actions),
        "completed_count": completed_cnt,
        "in_progress_count": in_prog_cnt,
        "blocked_count": blocked_cnt,
        "realization_rate_pct": round(realization_rate, 1),
        "causality_caveat": "CAUSALITY DISCLAIMER: Post-implementation performance changes reflect observed tracking associations. External confounding factors (seasonality, staffing turnover, policy shifts) must be considered."
    }
