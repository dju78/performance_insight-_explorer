"""Data models and schemas for Performance Insight Explorer.
Structured validation models for KPIs, Data Quality, Insights, Recommendations, and Actions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from core.constants import (
    QualityDimension, QualitySeverity, RemediationAction,
    TargetDirection, RecommendationCategory, ActionStatus, PriorityLevel, WorkflowStage
)


@dataclass
class QualityIssue:
    issue_id: str
    dimension: QualityDimension
    severity: QualitySeverity
    title: str
    description: str
    field_name: str
    affected_count: int
    affected_pct: float
    sample_indices: List[Any] = field(default_factory=list)
    sample_values: List[Any] = field(default_factory=list)
    business_impact: str = ""
    recommended_treatment: str = ""
    status: str = "Unresolved"  # Unresolved, Accepted, Remediated, Flagged
    analyst_justification: str = ""
    remediation_action: Optional[RemediationAction] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "dimension": self.dimension.value if isinstance(self.dimension, QualityDimension) else str(self.dimension),
            "severity": self.severity.value if isinstance(self.severity, QualitySeverity) else str(self.severity),
            "title": self.title,
            "description": self.description,
            "field": self.field_name,
            "affected_count": self.affected_count,
            "affected_pct": self.affected_pct,
            "sample_indices": self.sample_indices[:10],
            "sample_values": self.sample_values[:5],
            "business_impact": self.business_impact,
            "recommended_treatment": self.recommended_treatment,
            "status": self.status,
            "analyst_justification": self.analyst_justification,
            "remediation_action": self.remediation_action.value if self.remediation_action else None
        }


@dataclass
class KPIDefinition:
    id: str
    name: str
    business_definition: str
    formula: str  # e.g., "numerator / denominator * 100" or custom expression
    numerator_field: Optional[str] = None
    denominator_field: Optional[str] = None
    source_field: Optional[str] = None
    unit: str = ""
    aggregation_method: str = "sum"  # sum, mean, median, count, rate, ratio, index, composite
    reporting_frequency: str = "Monthly"  # Daily, Weekly, Monthly, Quarterly, Annual
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    benchmark_value: Optional[float] = None
    benchmark_source: str = "Internal Target"
    directionality: TargetDirection = TargetDirection.HIGHER_IS_BETTER
    target_min: Optional[float] = None  # Used when directionality == TARGET_RANGE
    target_max: Optional[float] = None  # Used when directionality == TARGET_RANGE
    weight: float = 1.0
    owner: str = "Operations Lead"
    relevant_dimensions: List[str] = field(default_factory=list)
    missing_data_rule: str = "exclude"  # exclude, zero, carry_forward
    min_sample_size: int = 1
    is_composite: bool = False
    component_kpi_weights: Dict[str, float] = field(default_factory=dict)
    is_estimated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "business_definition": self.business_definition,
            "formula": self.formula,
            "numerator_field": self.numerator_field,
            "denominator_field": self.denominator_field,
            "source_field": self.source_field,
            "unit": self.unit,
            "aggregation_method": self.aggregation_method,
            "reporting_frequency": self.reporting_frequency,
            "target_value": self.target_value,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "benchmark_value": self.benchmark_value,
            "benchmark_source": self.benchmark_source,
            "directionality": self.directionality.value if isinstance(self.directionality, TargetDirection) else str(self.directionality),
            "target_min": self.target_min,
            "target_max": self.target_max,
            "weight": self.weight,
            "owner": self.owner,
            "relevant_dimensions": self.relevant_dimensions,
            "missing_data_rule": self.missing_data_rule,
            "min_sample_size": self.min_sample_size,
            "is_composite": self.is_composite,
            "component_kpi_weights": self.component_kpi_weights,
            "is_estimated": self.is_estimated
        }


@dataclass
class EvidenceInsight:
    id: str
    finding_title: str
    quantitative_evidence: str
    kpi_affected: str
    variance_or_gap_size: float
    time_period: str
    affected_segment: str
    confidence_level: str  # High (Verified), Medium (Indicative), Low (Hypothesis)
    business_significance: str  # Critical, Material, Operational, Informational
    data_quality_caveat: str
    statistical_limitation: str
    suggested_follow_up: str
    status: str = "Active"  # Active, Accepted, Edited, Rejected, Merged, Pinned
    analyst_context_notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "finding_title": self.finding_title,
            "quantitative_evidence": self.quantitative_evidence,
            "kpi_affected": self.kpi_affected,
            "variance_or_gap_size": self.variance_or_gap_size,
            "time_period": self.time_period,
            "affected_segment": self.affected_segment,
            "confidence_level": self.confidence_level,
            "business_significance": self.business_significance,
            "data_quality_caveat": self.data_quality_caveat,
            "statistical_limitation": self.statistical_limitation,
            "suggested_follow_up": self.suggested_follow_up,
            "status": self.status,
            "analyst_context_notes": self.analyst_context_notes,
            "created_at": self.created_at
        }


@dataclass
class RecommendationItem:
    id: str
    linked_insight_id: str
    problem_addressed: str
    supporting_evidence: str
    proposed_action: str
    expected_benefit: str
    priority: PriorityLevel = PriorityLevel.HIGH
    urgency: str = "Immediate (< 30 days)"
    impact: str = "High"  # High, Medium, Low
    effort: str = "Medium"  # Low, Medium, High
    cost_category: str = "Operational / Existing Budget"  # Low, Medium, Capital
    risk: str = "Low implementation risk"
    responsible_owner: str = "Operations Lead"
    timescale: str = "30-60 days"
    success_measure: str = "KPI target attainment"
    review_date: str = ""
    dependencies: str = "Standard management approval"
    confidence_level: str = "High (Empirically grounded)"
    category: RecommendationCategory = RecommendationCategory.QUICK_WIN
    status: str = "Proposed"  # Proposed, Approved, Deferred, Rejected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "linked_insight_id": self.linked_insight_id,
            "problem_addressed": self.problem_addressed,
            "supporting_evidence": self.supporting_evidence,
            "proposed_action": self.proposed_action,
            "expected_benefit": self.expected_benefit,
            "priority": self.priority.value if isinstance(self.priority, PriorityLevel) else str(self.priority),
            "urgency": self.urgency,
            "impact": self.impact,
            "effort": self.effort,
            "cost_category": self.cost_category,
            "risk": self.risk,
            "responsible_owner": self.responsible_owner,
            "timescale": self.timescale,
            "success_measure": self.success_measure,
            "review_date": self.review_date,
            "dependencies": self.dependencies,
            "confidence_level": self.confidence_level,
            "category": self.category.value if isinstance(self.category, RecommendationCategory) else str(self.category),
            "status": self.status
        }


@dataclass
class ActionItem:
    id: str
    recommendation_id: str
    action_title: str
    action_description: str
    owner: str
    department: str
    priority: PriorityLevel
    status: ActionStatus = ActionStatus.NOT_STARTED
    due_date: str = ""
    kpi_affected: str = ""
    baseline_value: Optional[float] = None
    expected_result: Optional[float] = None
    actual_result: Optional[float] = None
    progress_notes: str = ""
    evidence_attachment_ref: str = ""
    review_date: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "action_title": self.action_title,
            "action_description": self.action_description,
            "owner": self.owner,
            "department": self.department,
            "priority": self.priority.value if isinstance(self.priority, PriorityLevel) else str(self.priority),
            "status": self.status.value if isinstance(self.status, ActionStatus) else str(self.status),
            "due_date": self.due_date,
            "kpi_affected": self.kpi_affected,
            "baseline_value": self.baseline_value,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "progress_notes": self.progress_notes,
            "evidence_attachment_ref": self.evidence_attachment_ref,
            "review_date": self.review_date,
            "updated_at": self.updated_at
        }


@dataclass
class ProjectState:
    project_id: str
    project_name: str
    organization_name: str
    created_by: str
    created_at: str
    business_question: str
    target_audience: str
    time_horizon: str
    completed_stages: List[str] = field(default_factory=list)
    current_stage: str = WorkflowStage.STAGE_01_QUESTION.value
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "organization_name": self.organization_name,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "business_question": self.business_question,
            "target_audience": self.target_audience,
            "time_horizon": self.time_horizon,
            "completed_stages": self.completed_stages,
            "current_stage": self.current_stage,
            "notes": self.notes
        }
