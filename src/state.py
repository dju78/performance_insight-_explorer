"""Session State Management for Streamlit.
Maintains pristine raw data, active confirmed mappings, assessment context,
row granularity confirmation, insight review status, dataset fingerprints, and safe reset controls.
"""
import hashlib
from typing import Any, Optional, Dict, List
import pandas as pd
import streamlit as st
from src.audit import AuditLogger
from src.recommendations import AssumptionsRegister, LimitationsRegister


def compute_dataset_fingerprint(df: Optional[pd.DataFrame], filename: str = "", sheet_name: str = "") -> str:
    """Compute a unique deterministic hash for a dataset context."""
    if df is None or len(df) == 0:
        return "EMPTY_DATASET"
    cols_str = "_".join(sorted([str(c) for c in df.columns]))
    raw_sig = f"{filename}::{sheet_name}::{len(df)}::{cols_str}"
    return hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]


def init_session_state():
    """Initialize default session state keys if not already present."""
    if "audit_logger" not in st.session_state:
        st.session_state.audit_logger = AuditLogger()
        
    if "assumptions_register" not in st.session_state:
        st.session_state.assumptions_register = AssumptionsRegister()
        
    if "limitations_register" not in st.session_state:
        st.session_state.limitations_register = LimitationsRegister()
        
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
        
    if "assessment_question" not in st.session_state:
        st.session_state.assessment_question = ""
        
    if "target_audience" not in st.session_state:
        st.session_state.target_audience = "Senior Leadership"
        
    if "output_format" not in st.session_state:
        st.session_state.output_format = "Presentation Deck (PPTX)"
        
    if "time_available" not in st.session_state:
        st.session_state.time_available = "15 minutes"
        
    if "analyst_notes" not in st.session_state:
        st.session_state.analyst_notes = ""
        
    if "target_directions" not in st.session_state:
        st.session_state.target_directions = {}
        
    if "suggested_mappings" not in st.session_state:
        st.session_state.suggested_mappings = {}
        
    if "confirmed_mappings" not in st.session_state:
        st.session_state.confirmed_mappings = {}
        
    if "qa_report" not in st.session_state:
        st.session_state.qa_report = None
        
    if "structural_qa_report" not in st.session_state:
        st.session_state.structural_qa_report = None
        
    if "semantic_qa_report" not in st.session_state:
        st.session_state.semantic_qa_report = None
        
    if "kpi_results" not in st.session_state:
        st.session_state.kpi_results = {}
        
    if "active_filters" not in st.session_state:
        st.session_state.active_filters = {}
        
    if "insights_list" not in st.session_state:
        st.session_state.insights_list = []
        
    if "reviewed_insights" not in st.session_state:
        st.session_state.reviewed_insights = []
        
    if "recommendations_list" not in st.session_state:
        st.session_state.recommendations_list = []
        
    if "reviewed_recommendations" not in st.session_state:
        st.session_state.reviewed_recommendations = {}


def reset_derived_state_for_new_dataset(new_fingerprint: str = "") -> None:
    """Clear all derived analytical state while preserving raw dataset and assessment context."""
    st.session_state["suggested_mappings"] = {}
    st.session_state["confirmed_mappings"] = {}
    st.session_state["target_directions"] = {}
    st.session_state["qa_report"] = None
    st.session_state["structural_qa_report"] = None
    st.session_state["semantic_qa_report"] = None
    st.session_state["kpi_results"] = {}
    st.session_state["active_filters"] = {}
    st.session_state["insights_list"] = []
    st.session_state["reviewed_insights"] = []
    st.session_state["recommendations_list"] = []
    st.session_state["reviewed_recommendations"] = {}
    st.session_state["row_granularity_confirmed"] = False
    st.session_state["row_granularity"] = "Not Confirmed"
    st.session_state["dataset_fingerprint"] = new_fingerprint
    
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "DATASET_CONTEXT_CHANGED",
            "Dataset changed; cleared mappings, QA reports, KPIs, insights, and recommendations.",
            details={"new_fingerprint": new_fingerprint}
        )


def reset_analysis_only() -> None:
    """Clear derived analysis while preserving raw data and assessment context."""
    st.session_state["confirmed_mappings"] = {}
    st.session_state["target_directions"] = {}
    st.session_state["semantic_qa_report"] = None
    st.session_state["kpi_results"] = {}
    st.session_state["active_filters"] = {}
    st.session_state["insights_list"] = []
    st.session_state["reviewed_insights"] = []
    st.session_state["recommendations_list"] = []
    st.session_state["reviewed_recommendations"] = {}
    
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "RESET_ANALYSIS_ONLY",
            "Cleared confirmed mappings, metrics, insights, and recommendations."
        )


def reset_full_state() -> None:
    """Complete reset that clears everything."""
    st.session_state["raw_df"] = None
    st.session_state["clean_df"] = None
    st.session_state["dataset_name"] = ""
    st.session_state["dataset_fingerprint"] = ""
    st.session_state["metadata"] = None
    st.session_state["data_profile"] = None
    st.session_state["row_granularity"] = "Not Confirmed"
    st.session_state["row_granularity_confirmed"] = False
    st.session_state["suggested_mappings"] = {}
    st.session_state["confirmed_mappings"] = {}
    st.session_state["target_directions"] = {}
    st.session_state["qa_report"] = None
    st.session_state["structural_qa_report"] = None
    st.session_state["semantic_qa_report"] = None
    st.session_state["kpi_results"] = {}
    st.session_state["active_filters"] = {}
    st.session_state["insights_list"] = []
    st.session_state["reviewed_insights"] = []
    st.session_state["recommendations_list"] = []
    st.session_state["reviewed_recommendations"] = {}
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "clear"):
        st.session_state.audit_logger.clear()


def get_working_df() -> Optional[pd.DataFrame]:
    """Return filtered clean dataframe."""
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


def get_state(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    st.session_state[key] = value
