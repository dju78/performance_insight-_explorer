"""Centralized Session State and Project Persistence Engine for Performance Insight Explorer.
Manages:
- Dual-Mode state (Organization Mode vs Assessment Mode)
- 15-Stage Guided Analysis Workflow progress and gating
- Pristine raw data, clean data, and multi-dataset registry
- Dynamic KPI registry and calculation cache
- Quality issue remediation log and transformation audit trail
- Evidence insights, prioritized recommendations, and action tracking
- Project Save/Resume (portable JSON bundle)
"""
import copy
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import streamlit as st

from core.constants import AppMode, UserRole, WorkflowStage, WORKFLOW_STAGES_ORDER
from core.models import (
    KPIDefinition, QualityIssue, EvidenceInsight, RecommendationItem, ActionItem, ProjectState
)
from core.security import compute_audit_hash


def compute_dataset_fingerprint(df: Optional[pd.DataFrame], filename: str = "", sheet_name: str = "") -> str:
    """Compute a deterministic SHA-256 fingerprint for a dataset context."""
    if df is None or len(df) == 0:
        return "EMPTY_DATASET"
    cols_str = "_".join(sorted([str(c) for c in df.columns]))
    raw_sig = f"{filename}::{sheet_name}::{len(df)}::{cols_str}"
    return hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]


def init_session_state() -> None:
    """Initialize all platform session state keys if not already present."""
    # App Mode & User Role
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = AppMode.ORGANIZATION.value
    if "user_role" not in st.session_state:
        st.session_state.user_role = UserRole.ANALYST.value
    if "model_version" not in st.session_state:
        st.session_state.model_version = 1

    # Project Context
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState(
            project_id="PROJ-" + datetime.now().strftime("%Y%m%d-%H%M"),
            project_name="Executive Operational Review",
            organization_name="Enterprise Operations",
            created_by="Daramola Omoyele",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            business_question="What are the operational performance bottlenecks and efficiency opportunities?",
            target_audience="Executive Leadership & Operations Committee",
            time_horizon="Last 12 Months",
            completed_stages=[WorkflowStage.STAGE_01_QUESTION.value],
            current_stage=WorkflowStage.STAGE_01_QUESTION.value,
            notes=""
        ).to_dict()

    # Workflow Progress Tracker
    if "workflow_stage" not in st.session_state:
        st.session_state.workflow_stage = WorkflowStage.STAGE_01_QUESTION.value
    if "completed_stages" not in st.session_state:
        st.session_state.completed_stages = [WorkflowStage.STAGE_01_QUESTION.value]
    if "stage_blocking_issues" not in st.session_state:
        st.session_state.stage_blocking_issues = {}

    # Datasets & Multi-file Registry
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None
    if "clean_df" not in st.session_state:
        st.session_state.clean_df = None
    if "dataset_name" not in st.session_state:
        st.session_state.dataset_name = ""
    if "dataset_fingerprint" not in st.session_state:
        st.session_state.dataset_fingerprint = ""
    if "metadata" not in st.session_state:
        st.session_state.metadata = None
    if "data_profile" not in st.session_state:
        st.session_state.data_profile = None
    if "row_granularity" not in st.session_state:
        st.session_state.row_granularity = "Not Confirmed"
    if "row_granularity_confirmed" not in st.session_state:
        st.session_state.row_granularity_confirmed = False
    if "datasets" not in st.session_state:
        st.session_state.datasets = {}
    if "primary_dataset_id" not in st.session_state:
        st.session_state.primary_dataset_id = ""
    if "relationships" not in st.session_state:
        st.session_state.relationships = []
    if "transformation_log" not in st.session_state:
        st.session_state.transformation_log = []

    # Quality Assurance & Remediation
    if "qa_report" not in st.session_state:
        st.session_state.qa_report = None
    if "qa_dimension_scores" not in st.session_state:
        st.session_state.qa_dimension_scores = {}
    if "remediated_issues" not in st.session_state:
        st.session_state.remediated_issues = {}
    if "data_quality_approved" not in st.session_state:
        st.session_state.data_quality_approved = False

    # Mapping & Semantic Taxonomies
    if "suggested_mappings" not in st.session_state:
        st.session_state.suggested_mappings = {}
    if "confirmed_mappings" not in st.session_state:
        st.session_state.confirmed_mappings = {}
    if "target_directions" not in st.session_state:
        st.session_state.target_directions = {}
    if "custom_taxonomies" not in st.session_state:
        st.session_state.custom_taxonomies = {}

    # Dynamic KPI Registry
    if "custom_kpi_registry" not in st.session_state:
        st.session_state.custom_kpi_registry = {}
    if "kpi_results" not in st.session_state:
        st.session_state.kpi_results = {}

    # Analytical Summaries & Filters
    if "active_filters" not in st.session_state:
        st.session_state.active_filters = {}
    if "selected_methods" not in st.session_state:
        st.session_state.selected_methods = []
    if "trend_summary" not in st.session_state:
        st.session_state.trend_summary = None
    if "comparison_summary" not in st.session_state:
        st.session_state.comparison_summary = None
    if "root_cause_summary" not in st.session_state:
        st.session_state.root_cause_summary = None
    if "five_whys_notes" not in st.session_state:
        st.session_state.five_whys_notes = ["", "", "", "", ""]
    if "fishbone_categories" not in st.session_state:
        st.session_state.fishbone_categories = {
            "People / Workforce": [],
            "Process / Methods": [],
            "Systems / Technology": [],
            "Capacity / Demand": [],
            "Measurement / Policy": [],
            "Environment / Vendor": []
        }

    # Decision Support & Action Tracking
    if "insights_list" not in st.session_state:
        st.session_state.insights_list = []
    if "reviewed_insights" not in st.session_state:
        st.session_state.reviewed_insights = []
    if "recommendations_list" not in st.session_state:
        st.session_state.recommendations_list = []
    if "action_registry" not in st.session_state:
        st.session_state.action_registry = []
    if "scenario_assumptions" not in st.session_state:
        st.session_state.scenario_assumptions = {
            "demand_multiplier": 1.0,
            "fte_multiplier": 1.0,
            "productivity_gain_pct": 0.0,
            "target_sla_days": 10.0
        }

    # Public Presentation & Stakeholder Briefing State
    if "briefing_data" not in st.session_state:
        st.session_state.briefing_data = {
            "filename": "", "raw_text": "", "questions": [], "question_count": 0, "is_loaded": False
        }
    if "assessment_brief_data" not in st.session_state:
        st.session_state.assessment_brief_data = st.session_state.briefing_data
    if "briefing_question" not in st.session_state:
        st.session_state.briefing_question = ""
    if "assessment_question" not in st.session_state:
        st.session_state.assessment_question = ""
    if "questions_must_answer" not in st.session_state:
        st.session_state.questions_must_answer = ""
    if "target_audience" not in st.session_state:
        st.session_state.target_audience = "Senior Leadership & Public Stakeholders"
    if "output_format" not in st.session_state:
        st.session_state.output_format = "PowerPoint"
    if "presentation_notes" not in st.session_state:
        st.session_state.presentation_notes = ""
    if "analyst_notes" not in st.session_state:
        st.session_state.analyst_notes = ""
    if "assessment_rules_confirmed" not in st.session_state:
        st.session_state.assessment_rules_confirmed = True

    # Audit Trail
    if "audit_log_entries" not in st.session_state:
        st.session_state.audit_log_entries = []
    if "last_audit_hash" not in st.session_state:
        st.session_state.last_audit_hash = "GENESIS_HASH_0000000000000000"


def log_audit_event(event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Record a cryptographically-chained event in the platform audit log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    det = details or {}
    prev = st.session_state.get("last_audit_hash", "GENESIS_HASH_0000000000000000")
    new_hash = compute_audit_hash(prev, ts, event_type, json.dumps(det, default=str))
    
    entry = {
        "timestamp": ts,
        "event_type": event_type,
        "message": message,
        "user": st.session_state.get("user_role", UserRole.ANALYST.value),
        "details": det,
        "hash": new_hash
    }
    
    st.session_state.audit_log_entries.append(entry)
    st.session_state.last_audit_hash = new_hash


def advance_workflow_stage(stage: WorkflowStage) -> None:
    """Mark a workflow stage as completed and advance current stage pointer."""
    st.session_state.workflow_stage = stage.value
    if stage.value not in st.session_state.completed_stages:
        st.session_state.completed_stages.append(stage.value)
    log_audit_event("WORKFLOW_STAGE_COMPLETED", f"Completed workflow stage: {stage.value}")


def clear_dataset_state() -> None:
    """Thoroughly purge all active dataset data, mappings, KPIs, QA reports, and derived analysis results."""
    st.session_state.raw_df = None
    st.session_state.clean_df = None
    st.session_state.dataset_name = ""
    st.session_state.uploaded_file_name = ""
    st.session_state.dataset_fingerprint = ""
    st.session_state.metadata = None
    st.session_state.data_profile = None
    st.session_state.available_sheets = []
    st.session_state.active_sheet = "Default"
    st.session_state.row_granularity = "Not Confirmed"
    st.session_state.row_granularity_confirmed = False

    st.session_state.suggested_mappings = {}
    st.session_state.confirmed_mappings = {}
    st.session_state.target_directions = {}
    st.session_state.custom_taxonomies = {}

    st.session_state.custom_kpi_registry = {}
    st.session_state.kpi_results = {}
    st.session_state.active_filters = {}
    st.session_state.selected_methods = []

    st.session_state.qa_report = None
    st.session_state.qa_dimension_scores = {}
    st.session_state.remediated_issues = {}
    st.session_state.data_quality_approved = False

    st.session_state.trend_summary = None
    st.session_state.comparison_summary = None
    st.session_state.root_cause_summary = None
    st.session_state.five_whys_notes = ["", "", "", "", ""]
    st.session_state.fishbone_categories = {
        "People / Workforce": [],
        "Process / Methods": [],
        "Systems / Technology": [],
        "Capacity / Demand": [],
        "Measurement / Policy": [],
        "Environment / Vendor": []
    }

    st.session_state.insights_list = []
    st.session_state.reviewed_insights = []
    st.session_state.recommendations_list = []
    st.session_state.action_registry = []

    # Quick Analysis State
    st.session_state.analysis_results = None
    st.session_state.selected_metric_col = None
    st.session_state.selected_date_col = None
    st.session_state.selected_group_col = None
    st.session_state.selected_target_val = None

    log_audit_event("DATASET_CLEARED", "Purged active dataset, mappings, and analytical cache.")


def invalidate_derived_state(df: Optional[pd.DataFrame] = None, new_fingerprint: str = "") -> None:
    """Invalidate all downstream analytical calculations when data or mappings change."""
    st.session_state.model_version = st.session_state.get("model_version", 1) + 1
    st.session_state.kpi_results = {}
    st.session_state.trend_summary = None
    st.session_state.comparison_summary = None
    st.session_state.root_cause_summary = None
    st.session_state.insights_list = []
    st.session_state.reviewed_insights = []
    st.session_state.recommendations_list = []
    st.session_state.analysis_results = None
    if new_fingerprint:
        st.session_state.dataset_fingerprint = new_fingerprint
    log_audit_event("DERIVED_STATE_INVALIDATED", "Cleared downstream analytical cache.")


def get_working_df() -> Optional[pd.DataFrame]:
    """Retrieve the filtered working dataframe based on active user filters."""
    df = st.session_state.get("clean_df")
    if df is None:
        df = st.session_state.get("raw_df")
    if df is None:
        return None
    
    res_df = df.copy(deep=True)
    filters = st.session_state.get("active_filters", {})
    for col, vals in filters.items():
        if col in res_df.columns and vals:
            res_df = res_df[res_df[col].isin(vals)]
    return res_df


def save_project_bundle() -> str:
    """Serialize entire analytical project into a portable JSON state bundle."""
    bundle = {
        "version": "2.0.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_state": st.session_state.get("project_state", {}),
        "workflow_stage": st.session_state.get("workflow_stage", ""),
        "completed_stages": st.session_state.get("completed_stages", []),
        "dataset_name": st.session_state.get("dataset_name", ""),
        "row_granularity": st.session_state.get("row_granularity", ""),
        "row_granularity_confirmed": st.session_state.get("row_granularity_confirmed", False),
        "confirmed_mappings": st.session_state.get("confirmed_mappings", {}),
        "target_directions": st.session_state.get("target_directions", {}),
        "custom_kpi_registry": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in st.session_state.get("custom_kpi_registry", {}).items()},
        "insights_list": [i.to_dict() if hasattr(i, "to_dict") else i for i in st.session_state.get("insights_list", [])],
        "reviewed_insights": [i.to_dict() if hasattr(i, "to_dict") else i for i in st.session_state.get("reviewed_insights", [])],
        "recommendations_list": [r.to_dict() if hasattr(r, "to_dict") else r for r in st.session_state.get("recommendations_list", [])],
        "action_registry": [a.to_dict() if hasattr(a, "to_dict") else a for a in st.session_state.get("action_registry", [])],
        "scenario_assumptions": st.session_state.get("scenario_assumptions", {}),
        "remediated_issues": st.session_state.get("remediated_issues", {}),
        "audit_log": st.session_state.get("audit_log_entries", [])
    }
    return json.dumps(bundle, indent=2, default=str)


def load_project_bundle(bundle_json_str: str) -> Tuple[bool, str]:
    """Restore an analytical project from a JSON state bundle."""
    try:
        data = json.loads(bundle_json_str)
        st.session_state.project_state = data.get("project_state", {})
        st.session_state.workflow_stage = data.get("workflow_stage", WorkflowStage.STAGE_01_QUESTION.value)
        st.session_state.completed_stages = data.get("completed_stages", [])
        st.session_state.dataset_name = data.get("dataset_name", "")
        st.session_state.row_granularity = data.get("row_granularity", "Not Confirmed")
        st.session_state.row_granularity_confirmed = data.get("row_granularity_confirmed", False)
        st.session_state.confirmed_mappings = data.get("confirmed_mappings", {})
        st.session_state.target_directions = data.get("target_directions", {})
        st.session_state.custom_kpi_registry = data.get("custom_kpi_registry", {})
        st.session_state.insights_list = data.get("insights_list", [])
        st.session_state.reviewed_insights = data.get("reviewed_insights", [])
        st.session_state.recommendations_list = data.get("recommendations_list", [])
        st.session_state.action_registry = data.get("action_registry", [])
        st.session_state.scenario_assumptions = data.get("scenario_assumptions", {})
        st.session_state.remediated_issues = data.get("remediated_issues", {})
        
        log_audit_event("PROJECT_RESTORED_FROM_BUNDLE", f"Project state restored: {data.get('project_state', {}).get('project_name', 'Unnamed')}")
        return True, "Project successfully loaded."
    except Exception as e:
        return False, f"Failed to restore project bundle: {str(e)}"
