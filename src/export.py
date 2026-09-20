"""Unified Export Module for Performance Insight Explorer.
Builds standardized export payloads from active session state and dispatches
to PowerPoint, PDF Briefings, Multi-tab Excel Packs, and Plaintext Audit Trails.
Strictly adheres to analytical governance: Approved-Findings only, No Hallucinated Metrics.
"""
import os
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st

from src.quality import run_quality_audit

def load_app_config() -> Dict[str, Any]:
    """Return application configuration and metadata."""
    return {
        "app_title": "Performance Insight Explorer",
        "author": "DARAMOLA OMOYELE",
        "version": "2.0.0",
        "default_target_direction": "higher_is_better"
    }


def group_recommendations_by_category(recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group flat recommendation records into standard operational categories."""
    categories = {
        "Act": [],
        "Investigate": [],
        "Monitor": [],
        "Improve Reporting": []
    }
    for rec in (recommendations or []):
        cat = rec.get("category", "Act")
        if cat not in categories:
            cat = "Act"
        categories[cat].append(rec)
    return categories


from modules.reporting.export_builder import build_canonical_reporting_payload


def build_export_payload_from_state(state_or_df: Any = None, **kwargs: Any) -> Dict[str, Any]:
    """Gather live session state into a single immutable, validated export payload.
    Ensures zero fabricated data, active gate checking, and consistent schema across all export formats.
    """
    return build_canonical_reporting_payload(state_or_df=state_or_df, **kwargs)



def generate_executive_excel_pack(
    payload: Optional[Dict[str, Any]] = None,
    output_filepath: Optional[str] = None
) -> str:
    """Generate comprehensive multi-tab Excel analytical workbook from payload."""
    data = payload or build_export_payload_from_state()
    out_dir = os.path.join(os.getcwd(), "outputs", "reports")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_filepath or os.path.join(out_dir, f"Performance_Pack_{timestamp}.xlsx")
    
    raw_df_to_use = data.get("raw_df")
    if raw_df_to_use is None:
        raw_df_to_use = pd.DataFrame()
        
    profile_info = {
        "filename": data.get("filename", "Operational Dataset"),
        "sheet_name": data.get("active_sheet", "Default"),
        "row_count": data.get("row_count", 0),
        "column_count": data.get("column_count", 0)
    }
    
    assumptions_df = pd.DataFrame(data.get("assumptions", []))
    limitations_df = pd.DataFrame(data.get("limitations", []))
    audit_df = pd.DataFrame(data.get("audit_trail", []))
    
    trend_df = data.get("trend_summary", {}).get("trend_df") if data.get("trend_summary") else None
    comp_df = data.get("comparison_summary", {}).get("comparison_df") if data.get("comparison_summary") else None
    
    from src.reporting import generate_excel_summary
    generate_excel_summary(
        output_filepath=filepath,
        raw_df=raw_df_to_use,
        profile_info=profile_info,
        qa_report=data.get("qa_report", {}),
        kpi_results=data.get("kpi_results", {}),
        trend_df=trend_df,
        comp_df=comp_df,
        insights=data.get("approved_insights", []),
        recommendations=data.get("recommendations_by_category", {}),
        assumptions_df=assumptions_df,
        limitations_df=limitations_df,
        audit_df=audit_df
    )
    
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "EXCEL_EXPORT_GENERATED", "Generated Analytical Excel Workbook",
            filename=os.path.basename(filepath),
            details={"fingerprint": data.get("dataset_fingerprint"), "sheet": data.get("active_sheet")}
        )
        
    return filepath


def generate_powerpoint_deck(
    payload: Optional[Dict[str, Any]] = None,
    output_filepath: Optional[str] = None,
    include_appendix: bool = False
) -> str:
    """Generate professional 16:9 PowerPoint presentation deck from live payload."""
    data = payload or build_export_payload_from_state()
    out_dir = os.path.join(os.getcwd(), "outputs", "presentations")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_filepath or os.path.join(out_dir, f"Performance_Briefing_{timestamp}.pptx")
    
    project_metadata = {
        "filename": data.get("filename", "Operational Dataset"),
        "active_sheet": data.get("active_sheet", "Default"),
        "row_count": data.get("row_count", 0),
        "column_count": data.get("column_count", 0),
        "author": "DARAMOLA OMOYELE"
    }
    
    kpi_summary = data.get("kpi_results", {})
    
    from src.powerpoint import generate_powerpoint_presentation
    generate_powerpoint_presentation(
        output_filepath=filepath,
        project_metadata=project_metadata,
        qa_report=data.get("qa_report", {}),
        kpi_summary=kpi_summary,
        trend_summary=data.get("trend_summary"),
        comparison_summary=data.get("comparison_summary"),
        insights=data.get("approved_insights", []),
        recommendations=data.get("recommendations_by_category", {}),
        limitations=data.get("limitations", []),
        assumptions=data.get("assumptions", []),
        assessment_context=data.get("assessment_context", {}),
        row_granularity=data.get("row_granularity", "Periodic snapshot"),
        clean_df=data.get("raw_df"),
        confirmed_mappings=data.get("confirmed_mappings", {}),
        include_appendix=include_appendix
    )
    
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "PPTX_EXPORT_GENERATED", "Generated Executive PowerPoint Presentation",
            filename=os.path.basename(filepath),
            details={"fingerprint": data.get("dataset_fingerprint"), "sheet": data.get("active_sheet"), "appendix": include_appendix}
        )
        
    return filepath


def generate_pdf_report(
    payload: Optional[Dict[str, Any]] = None,
    audience: str = "Senior Leadership",
    output_filepath: Optional[str] = None
) -> str:
    """Generate audience-adapted A4 PDF brief using ReportLab Platypus."""
    data = payload or build_export_payload_from_state()
    out_dir = os.path.join(os.getcwd(), "outputs", "briefs")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    aud_slug = audience.lower().replace(" ", "_").replace("/", "_")
    filepath = output_filepath or os.path.join(out_dir, f"Executive_Briefing_{aud_slug}_{timestamp}.pdf")
    
    from src.pdf_report import generate_pdf_document
    generate_pdf_document(
        output_filepath=filepath,
        payload=data,
        audience=audience
    )
    
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "PDF_EXPORT_GENERATED", f"Generated Executive PDF Briefing ({audience})",
            filename=os.path.basename(filepath),
            details={"fingerprint": data.get("dataset_fingerprint"), "audience": audience}
        )
        
    return filepath


def generate_audit_trail_text(
    audit_events: Optional[List[Dict[str, Any]]] = None,
    output_filepath: Optional[str] = None
) -> str:
    """Generate plaintext reproducible audit log file."""
    events = audit_events
    if events is None:
        if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "get_events"):
            events = st.session_state.audit_logger.get_events()
        else:
            events = st.session_state.get("audit_trail", [])
            
    out_dir = os.path.join(os.getcwd(), "outputs", "audit")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_filepath or os.path.join(out_dir, f"audit_trail_{timestamp}.txt")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("="*85 + "\n")
        f.write("PERFORMANCE INSIGHT EXPLORER - AUDIT & REPRODUCIBILITY TRAIL\n")
        f.write(f"Author: DARAMOLA OMOYELE | Generated: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Fingerprint: {st.session_state.get('dataset_fingerprint', 'N/A')}\n")
        f.write("="*85 + "\n\n")
        
        if not events:
            f.write("No interactive events recorded in session.\n")
        else:
            for ev in events:
                f.write(f"[{ev.get('timestamp', 'N/A')}] EVENT: {ev.get('event_type', 'UNKNOWN')} | {ev.get('action', '')} | DETAILS: {ev.get('details', {})}\n")
                
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "log"):
        st.session_state.audit_logger.log(
            "AUDIT_EXPORT_GENERATED", "Exported Plaintext Audit Trail",
            filename=os.path.basename(filepath)
        )
        
    return filepath
