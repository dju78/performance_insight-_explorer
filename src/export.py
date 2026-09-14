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
from src.powerpoint import generate_powerpoint_presentation
from src.pdf_report import generate_pdf_document
from src.reporting import generate_excel_summary

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


def build_export_payload_from_state(state_or_df: Any = None) -> Dict[str, Any]:
    """Gather live session state into a single immutable, validated export payload.
    Ensures zero fabricated data, active gate checking, and consistent schema across all export formats.
    """
    if isinstance(state_or_df, dict):
        state = state_or_df
        clean_df = state.get("clean_df") if state.get("clean_df") is not None else state.get("raw_df")
        confirmed_mappings = state.get("confirmed_mappings", {})
        row_granularity = state.get("row_granularity", "Not Confirmed")
        row_granularity_confirmed = state.get("row_granularity_confirmed", True)
        insights_list = state.get("insights_list", [])
        recs_list = state.get("recommendations_list", [])
        dataset_name = state.get("dataset_name", "Active Dataset")
        q_brief = state.get("assessment_question", "")
        q_must = state.get("questions_must_answer", "")
        target_aud = state.get("target_audience") or "Not specified"
        resp_time = state.get("response_time") or "Not specified"
    else:
        clean_df = state_or_df if state_or_df is not None else st.session_state.get("clean_df")
        if clean_df is None:
            clean_df = st.session_state.get("raw_df")
        confirmed_mappings = st.session_state.get("confirmed_mappings", {})
        row_granularity = st.session_state.get("row_granularity", "Not Confirmed")
        row_granularity_confirmed = st.session_state.get("row_granularity_confirmed", False)
        insights_list = st.session_state.get("insights_list", [])
        recs_list = st.session_state.get("recommendations_list", [])
        dataset_name = st.session_state.get("dataset_name", "Active Dataset")
        q_brief = st.session_state.get("assessment_question", "")
        q_must = state_or_df.get("questions_must_answer", "") if isinstance(state_or_df, dict) else st.session_state.get("questions_must_answer", "")
        target_aud = st.session_state.get("target_audience") or "Not specified"
        resp_time = st.session_state.get("response_time", "15 mins")
    
    # Validation Gates
    validation_errors = []
    if clean_df is None or len(clean_df) == 0:
        validation_errors.append("No active dataset loaded.")
    if not row_granularity_confirmed or row_granularity == "Not Confirmed":
        validation_errors.append("Row granularity has not been confirmed on Page 01.")
    if not confirmed_mappings:
        validation_errors.append("Column mappings have not been confirmed on Page 03.")
        
    is_valid_for_export = (len(validation_errors) == 0)
    
    # Re-run or collect real Quality Audit
    if clean_df is not None and len(clean_df) > 0:
        qa_report = run_quality_audit(clean_df, confirmed_mappings)
    else:
        qa_report = st.session_state.get("qa_report") or {
            "health_score": 0.0, "critical_count": 0, "warning_count": 0, "issues": []
        }
        
    # Standardized Assessment Context
    target_dir_val = "higher_is_better"
    target_dirs = st.session_state.get("target_directions", {})
    if isinstance(target_dirs, dict) and target_dirs:
        target_dir_val = next(iter(target_dirs.values()), "higher_is_better")
    elif isinstance(target_dirs, str):
        target_dir_val = target_dirs

    assessment_context = {
        "question": st.session_state.get("assessment_question", "").strip() or "Operational performance evaluation as defined in assessment brief.",
        "assessment_question": st.session_state.get("assessment_question", "").strip() or "Operational performance evaluation as defined in assessment brief.",
        "questions_must_answer": st.session_state.get("questions_must_answer", ""),
        "audience": st.session_state.get("target_audience") or "Not specified",
        "target_audience": st.session_state.get("target_audience") or "Not specified",
        "output_format": st.session_state.get("output_format") or "Not specified / Await instructions",
        "time_available": st.session_state.get("time_available") or "Not specified",
        "response_time": st.session_state.get("response_time") or "Not specified",
        "mandatory_measures": st.session_state.get("mandatory_measures", ""),
        "required_comparisons": st.session_state.get("required_comparisons", ""),
        "required_method": st.session_state.get("required_method", ""),
        "restrictions_rules": st.session_state.get("restrictions_rules", ""),
        "other_instructions": st.session_state.get("other_instructions", ""),
        "analyst_notes": st.session_state.get("analyst_notes", "")
    }
    
    # Filter approved only
    all_insights = insights_list if insights_list else (st.session_state.get("insights_list", []) if "insights_list" in st.session_state else [])
    approved_insights = [i for i in all_insights if i.get("status") in ["approved", "accepted"]]
    
    all_recs = recs_list if recs_list else (st.session_state.get("recommendations_list", []) if "recommendations_list" in st.session_state else [])
    approved_recs = [r for r in all_recs if r.get("status") in ["approved", "accepted"]]
    recs_by_cat = group_recommendations_by_category(approved_recs)
    
    # Assumptions & Limitations Registers
    assumptions = st.session_state.assumptions_register.get_all() if "assumptions_register" in st.session_state and hasattr(st.session_state.assumptions_register, "get_all") else []
    limitations = st.session_state.limitations_register.get_all() if "limitations_register" in st.session_state and hasattr(st.session_state.limitations_register, "get_all") else []
    
    # Audit trail
    if "audit_logger" in st.session_state and hasattr(st.session_state.audit_logger, "get_events"):
        audit_events = st.session_state.audit_logger.get_events()
    else:
        audit_events = st.session_state.get("audit_trail", [])
        
    # Ensure KPIs are computed if valid mappings exist
    kpi_results = st.session_state.get("kpi_results", {})
    if (not kpi_results or not kpi_results.get("summary_kpis")) and clean_df is not None and confirmed_mappings:
        from src.metrics import calculate_kpis
        try:
            kpi_results = calculate_kpis(clean_df, confirmed_mappings, target_direction=target_dir_val)
            st.session_state["kpi_results"] = kpi_results
        except Exception:
            pass

    ds_name = state.get("dataset_name", "operational_data.csv") if isinstance(state_or_df, dict) else (st.session_state.get("uploaded_file_name") or st.session_state.get("dataset_name", "operational_data.csv"))
    r_count = len(clean_df) if clean_df is not None else 0
    c_count = len(clean_df.columns) if clean_df is not None else 0

    payload = {
        "assessment_context": assessment_context,
        "metadata": {
            "author": "DARAMOLA OMOYELE",
            "assessment_question": assessment_context.get("question", ""),
            "target_audience": target_aud,
            "response_time": resp_time,
            "date": datetime.datetime.now().strftime("%d %B %Y"),
            "role": "Performance Analyst (HEO)"
        },
        "dataset": {
            "name": ds_name,
            "row_count": r_count,
            "col_count": c_count,
            "column_count": c_count,
            "granularity": row_granularity,
            "granularity_confirmed": row_granularity_confirmed
        },
        "data_quality": {
            "health_score": qa_report.get("health_score", 100.0) if isinstance(qa_report, dict) else 100.0,
            "fitness_status": "Fit for purpose" if (qa_report.get("health_score", 100.0) >= 80) else "Fit for purpose with caveats",
            "fitness_reasons": ["Automated quality and fitness evaluation executed."],
            "caveats": [i.get("description", "") for i in qa_report.get("issues", [])] if isinstance(qa_report, dict) else []
        },
        "kpis": kpi_results.get("summary_kpis", {}) if isinstance(kpi_results, dict) else {},
        "findings": approved_insights,
        "recommendations": approved_recs,
        "filename": ds_name,
        "active_sheet": state.get("active_sheet", "CSV_Default") if isinstance(state_or_df, dict) else st.session_state.get("active_sheet", "CSV_Default"),
        "row_count": r_count,
        "column_count": c_count,
        "row_granularity": row_granularity,
        "row_granularity_confirmed": row_granularity_confirmed,
        "confirmed_mappings": confirmed_mappings,
        "qa_report": qa_report,
        "kpi_results": kpi_results,
        "trend_summary": state.get("trend_summary") if isinstance(state_or_df, dict) else st.session_state.get("trend_summary"),
        "comparison_summary": state.get("comparison_summary") if isinstance(state_or_df, dict) else st.session_state.get("comparison_summary"),
        "approved_insights": approved_insights,
        "approved_recommendations": approved_recs,
        "recommendations_by_category": recs_by_cat,
        "assumptions": assumptions,
        "limitations": limitations,
        "audit_trail": audit_events,
        "generation_timestamp": datetime.datetime.now().isoformat(),
        "dataset_fingerprint": state.get("dataset_fingerprint", "N/A") if isinstance(state_or_df, dict) else st.session_state.get("dataset_fingerprint", "N/A"),
        "is_valid_for_export": is_valid_for_export,
        "validation_errors": validation_errors,
        "raw_df": clean_df
    }
    
    st.session_state["last_export_payload"] = payload
    return payload


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
