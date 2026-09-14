"""Session State Management for Streamlit.
Maintains pristine raw data, active confirmed mappings, assessment context,
row granularity confirmation, insight review status, and safe reset controls.
"""
import streamlit as st
import pandas as pd
from typing import Any, Optional, Dict
from src.audit import AuditLogger
from src.recommendations import AssumptionsRegister, LimitationsRegister


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
        
    if "metadata" not in st.session_state:
        st.session_state.metadata = None
        
    if "profile_info" not in st.session_state:
        st.session_state.profile_info = None
        
    if "row_granularity" not in st.session_state:
        st.session_state.row_granularity = "Not Confirmed"
        
    if "row_granularity_confirmed" not in st.session_state:
        st.session_state.row_granularity_confirmed = False
        
    if "assessment_context" not in st.session_state:
        st.session_state.assessment_context = {
            "question": "",
            "audience": "",
            "output_format": "",
            "time_available": "",
            "analyst_notes": ""
        }
        
    if "target_direction" not in st.session_state:
        st.session_state.target_direction = "higher_is_better"
        
    if "mappings" not in st.session_state:
        st.session_state.mappings = {}
        
    if "confirmed_mappings" not in st.session_state:
        st.session_state.confirmed_mappings = {}
        
    if "qa_report" not in st.session_state:
        st.session_state.qa_report = None
        
    if "kpi_results" not in st.session_state:
        st.session_state.kpi_results = None
        
    if "active_filters" not in st.session_state:
        st.session_state.active_filters = {}
        
    if "reviewed_insights" not in st.session_state:
        st.session_state.reviewed_insights = []
        
    if "reviewed_recommendations" not in st.session_state:
        st.session_state.reviewed_recommendations = {}


def reset_analysis_state():
    """Safe reset that clears mappings, filters, KPIs, and insights WITHOUT deleting raw uploaded data."""
    st.session_state.mappings = {}
    st.session_state.confirmed_mappings = {}
    st.session_state.kpi_results = None
    st.session_state.active_filters = {}
    st.session_state.reviewed_insights = []
    st.session_state.reviewed_recommendations = {}
    if st.session_state.raw_df is not None:
        st.session_state.audit_logger.log(
            "RESET_ANALYSIS",
            "Cleared mappings, filters, metrics, and insights while preserving raw source dataset.",
            filename=st.session_state.metadata.get("filename", "") if st.session_state.metadata else ""
        )


def reset_entire_session():
    """Complete reset that clears all uploaded data and session state."""
    st.session_state.raw_df = None
    st.session_state.metadata = None
    st.session_state.profile_info = None
    st.session_state.row_granularity = "Not Confirmed"
    st.session_state.row_granularity_confirmed = False
    st.session_state.assessment_context = {
        "question": "",
        "audience": "",
        "output_format": "",
        "time_available": "",
        "analyst_notes": ""
    }
    st.session_state.target_direction = "higher_is_better"
    st.session_state.mappings = {}
    st.session_state.confirmed_mappings = {}
    st.session_state.qa_report = None
    st.session_state.kpi_results = None
    st.session_state.active_filters = {}
    st.session_state.reviewed_insights = []
    st.session_state.reviewed_recommendations = {}
    st.session_state.audit_logger.clear()


def get_working_df() -> Optional[pd.DataFrame]:
    """Return a filtered working dataframe or raw dataframe."""
    if st.session_state.get("raw_df") is None:
        return None
        
    df = st.session_state.raw_df.copy(deep=True)
    filters = st.session_state.get("active_filters", {})
    
    for col, selected_vals in filters.items():
        if col in df.columns and selected_vals:
            df = df[df[col].isin(selected_vals)]
            
    return df


def get_state(key: str, default: Any = None) -> Any:
    """Get value from st.session_state safely."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Set value in st.session_state."""
    st.session_state[key] = value


def reset_analysis_only() -> None:
    """Alias for reset_analysis_state that clears derived analysis while preserving raw data."""
    st.session_state["mappings"] = {}
    st.session_state["confirmed_mappings"] = {}
    st.session_state["suggested_mappings"] = {}
    st.session_state["kpi_results"] = {}
    st.session_state["active_filters"] = {}
    st.session_state["reviewed_insights"] = []
    st.session_state["insights_list"] = []
    st.session_state["reviewed_recommendations"] = {}
    st.session_state["recommendations_list"] = []
    try:
        if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
            st.session_state.audit_logger.log(
                "RESET_ANALYSIS_ONLY",
                "Cleared mappings, filters, metrics, insights, and recommendations while preserving raw dataset."
            )
    except Exception:
        pass


def reset_full_state() -> None:
    """Alias for reset_entire_session."""
    reset_entire_session()
    st.session_state["insights_list"] = []
    st.session_state["recommendations_list"] = []
