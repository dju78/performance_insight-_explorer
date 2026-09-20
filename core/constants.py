"""Core constants and enumerations for Performance Insight Explorer.
Enterprise Performance Analysis, Diagnostic and Decision-Support Platform.
"""
from enum import Enum


class AppMode(str, Enum):
    ORGANIZATION = "Organization Mode"
    PUBLIC_PRESENTATION = "Public Presentation Mode"
    ASSESSMENT = "Public Presentation Mode"  # Backward compatibility alias


class UserRole(str, Enum):
    ADMIN = "Administrator"
    ANALYST = "Lead Analyst"
    VIEWER = "Executive Viewer"


class QualityDimension(str, Enum):
    COMPLETENESS = "Completeness"
    VALIDITY = "Validity"
    ACCURACY = "Accuracy"
    CONSISTENCY = "Consistency"
    UNIQUENESS = "Uniqueness"
    TIMELINESS = "Timeliness"
    INTEGRITY = "Integrity"
    CONFORMITY = "Conformity"
    COVERAGE = "Coverage"
    PLAUSIBILITY = "Plausibility"


class QualitySeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RemediationAction(str, Enum):
    ACCEPT = "Accept as Known Risk"
    EXCLUDE = "Exclude Affected Records"
    FLAG = "Flag as Limitation"
    JUSTIFY = "Add Business Justification"
    CLEAN = "Apply Cleaning Rule"


class TargetDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    TARGET_RANGE = "target_range"
    EXACT_TARGET = "exact_target"
    INFORMATIONAL = "informational"


class RecommendationCategory(str, Enum):
    QUICK_WIN = "Quick Win"
    STRATEGIC_INITIATIVE = "Strategic Initiative"
    FURTHER_INVESTIGATION = "Further Investigation"
    DATA_QUALITY = "Data-Quality Improvement"
    MONITORING = "Monitoring Action"


class ActionStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    UNDER_REVIEW = "Under Review"


class PriorityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class WorkflowStage(str, Enum):
    STAGE_01_QUESTION = "Define Business Question"
    STAGE_02_INGEST = "Upload & Profile Data"
    STAGE_03_GRANULARITY = "Confirm Data Granularity"
    STAGE_04_QUALITY = "Assess Data Quality"
    STAGE_05_MAPPING = "Configure Variables & Roles"
    STAGE_06_KPIS = "Define Targets & Benchmarks"
    STAGE_07_METHODS = "Select Analytical Methods"
    STAGE_08_OVERVIEW = "Analyse Performance"
    STAGE_09_TRENDS = "Identify Trends & Exceptions"
    STAGE_10_ROOT_CAUSE = "Investigate Drivers (RCA)"
    STAGE_11_UNCERTAINTY = "Assess Uncertainty & Limits"
    STAGE_12_INSIGHTS = "Evidence-Based Insights"
    STAGE_13_RECOMMENDATIONS = "Prioritized Recommendations"
    STAGE_14_ACTIONS = "Assign Actions & Tracking"
    STAGE_15_EXPORT = "Export & Governance"


WORKFLOW_STAGES_ORDER = [
    WorkflowStage.STAGE_01_QUESTION,
    WorkflowStage.STAGE_02_INGEST,
    WorkflowStage.STAGE_03_GRANULARITY,
    WorkflowStage.STAGE_04_QUALITY,
    WorkflowStage.STAGE_05_MAPPING,
    WorkflowStage.STAGE_06_KPIS,
    WorkflowStage.STAGE_07_METHODS,
    WorkflowStage.STAGE_08_OVERVIEW,
    WorkflowStage.STAGE_09_TRENDS,
    WorkflowStage.STAGE_10_ROOT_CAUSE,
    WorkflowStage.STAGE_11_UNCERTAINTY,
    WorkflowStage.STAGE_12_INSIGHTS,
    WorkflowStage.STAGE_13_RECOMMENDATIONS,
    WorkflowStage.STAGE_14_ACTIONS,
    WorkflowStage.STAGE_15_EXPORT,
]
