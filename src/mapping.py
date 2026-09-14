"""Flexible column-role mapping engine for Performance Insight Explorer.
Enforces explicit user confirmation: suggested mappings NEVER activate KPIs automatically.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


ROLE_CATALOGUE = {
    "record_id": {
        "label": "Record ID",
        "description": "Unique identifier for each transaction, row, or case",
        "category": "Identity",
        "keywords": ["id", "record_id", "case_id", "ref", "reference", "identifier", "ticket_id", "urn", "application_id", "app_id", "row_id", "case_reference", "transaction_id"],
        "data_types": ["string", "integer"]
    },
    "date": {
        "label": "Date",
        "description": "Primary transaction, received, or observation timestamp/date",
        "category": "Time",
        "keywords": ["date", "timestamp", "created_date", "received_date", "completion_date", "submission_date", "event_date", "start_date", "end_date", "log_date", "date_received", "case_date"],
        "data_types": ["datetime", "date", "string"]
    },
    "reporting_period": {
        "label": "Reporting Period",
        "description": "Reporting cycle e.g. month, quarter, week, year, financial year, period",
        "category": "Time",
        "keywords": ["period", "month", "year", "quarter", "week", "reporting_period", "cal_month", "fin_year", "period_name", "period_id", "reporting_month", "cycle", "date_period"],
        "data_types": ["string", "integer", "datetime"]
    },
    "team": {
        "label": "Team",
        "description": "Operational team or squad executing the work",
        "category": "Dimensions",
        "keywords": ["team", "service_team", "operational_team", "team_name", "unit", "squad", "group", "crew", "section", "operational_unit", "service_area", "handling_team", "ops_team"],
        "data_types": ["string", "category"]
    },
    "department": {
        "label": "Department",
        "description": "Higher organizational unit / department / division",
        "category": "Dimensions",
        "keywords": ["department", "dept", "division", "directorate", "branch", "service", "function", "business_unit"],
        "data_types": ["string", "category"]
    },
    "branch": {
        "label": "Branch",
        "description": "Local branch or office",
        "category": "Dimensions",
        "keywords": ["branch", "office", "centre", "center", "hub", "depot"],
        "data_types": ["string", "category"]
    },
    "location": {
        "label": "Location",
        "description": "Geographical region, site, or location",
        "category": "Dimensions",
        "keywords": ["location", "region", "area", "site", "zone", "territory", "city", "postcode", "country", "district", "place"],
        "data_types": ["string", "category"]
    },
    "category": {
        "label": "Category",
        "description": "Workstream or operational category classification",
        "category": "Dimensions",
        "keywords": ["category", "class", "classification", "stream", "workstream", "discipline", "domain", "case_classification"],
        "data_types": ["string", "category"]
    },
    "case_type": {
        "label": "Case Type",
        "description": "Type or complexity grade of the case/application/work item",
        "category": "Dimensions",
        "keywords": ["case_type", "type", "subtype", "work_type", "item_type", "request_type", "application_type", "complexity", "priority_level"],
        "data_types": ["string", "category"]
    },
    "status": {
        "label": "Status",
        "description": "Current lifecycle state (e.g. Open, Closed, Pending, In Progress)",
        "category": "Dimensions",
        "keywords": ["status", "state", "stage", "outcome", "disposition", "resolution", "phase", "condition", "current_status", "case_status"],
        "data_types": ["string", "category"]
    },
    "actual": {
        "label": "Actual Performance",
        "description": "Observed volume or KPI output achieved",
        "category": "Performance",
        "keywords": ["actual", "achieved", "output", "delivered", "result", "performance", "volume", "cases_completed", "cases_out", "target_completed", "actual_output"],
        "data_types": ["numeric", "float", "integer"]
    },
    "target": {
        "label": "Target",
        "description": "Expected performance standard, goal, or SLA benchmark",
        "category": "Performance",
        "keywords": ["target", "output_target", "target_output", "expected", "goal", "benchmark", "standard", "sla", "budget", "plan", "threshold", "sla_target", "target_volume", "sla_target_days", "target_cases", "vol_target"],
        "data_types": ["numeric", "float", "integer"]
    },
    "received": {
        "label": "Cases Received",
        "description": "Incoming demand volume / new cases received",
        "category": "Performance",
        "keywords": ["received", "demand_received", "demand", "inflow", "incoming", "new_cases", "intake", "applications", "submissions", "opened", "created", "inputs", "cases_received", "cases_in", "work_in", "vol_received"],
        "data_types": ["numeric", "float", "integer"]
    },
    "completed": {
        "label": "Cases Completed",
        "description": "Processed volume / cases closed / decisions made",
        "category": "Performance",
        "keywords": ["completed", "cases_closed", "closed", "resolved", "processed", "finished", "decisions", "finalised", "outputs", "clearances", "cases_completed", "cases_out", "work_out", "done", "vol_completed"],
        "data_types": ["numeric", "float", "integer"]
    },
    "opening_backlog": {
        "label": "Opening Backlog",
        "description": "Queue / work in progress at start of period",
        "category": "Performance",
        "keywords": ["opening_backlog", "open_work_start", "opening_queue", "start_backlog", "opening_wip", "starting_open", "initial_backlog", "beginning_backlog", "opening_bl", "start_work", "open_start", "start_queue"],
        "data_types": ["numeric", "float", "integer"]
    },
    "closing_backlog": {
        "label": "Closing Backlog",
        "description": "Queue / work in progress at end of period",
        "category": "Performance",
        "keywords": ["closing_backlog", "open_work_end", "closing_queue", "end_backlog", "closing_wip", "ending_open", "final_backlog", "outstanding", "backlog", "pending", "closing_bl", "end_work", "open_end", "end_queue"],
        "data_types": ["numeric", "float", "integer"]
    },
    "staff": {
        "label": "Available Staff",
        "description": "Headcount of operational staff available",
        "category": "Capacity",
        "keywords": ["staff", "headcount", "employees", "people", "team_size", "agents", "assessors", "officers", "inspectors", "staff_count"],
        "data_types": ["numeric", "float", "integer"]
    },
    "fte": {
        "label": "Available FTE",
        "description": "Full-Time Equivalent staff capacity",
        "category": "Capacity",
        "keywords": ["fte", "available_fte", "active_fte", "full_time_equivalent", "staff_fte", "capacity_fte", "resource_fte", "total_fte"],
        "data_types": ["numeric", "float", "integer"]
    },
    "hours_available": {
        "label": "Hours Available",
        "description": "Total scheduled / available working hours",
        "category": "Capacity",
        "keywords": ["hours_available", "scheduled_hours", "available_hours", "capacity_hours", "total_hours", "standard_hours", "contracted_hours", "hours_scheduled", "planned_hours", "hours"],
        "data_types": ["numeric", "float", "integer"]
    },
    "hours_used": {
        "label": "Hours Used",
        "description": "Actual productive or recorded working hours",
        "category": "Capacity",
        "keywords": ["hours_used", "productive_hours", "worked_hours", "logged_hours", "actual_hours", "utilised_hours", "utilized_hours", "hours_spent", "hours_worked", "active_hours"],
        "data_types": ["numeric", "float", "integer"]
    },
    "processing_time": {
        "label": "Processing Time",
        "description": "Duration, turnaround days/hours, or cycle time to complete",
        "category": "Performance",
        "keywords": ["processing_time", "median_turnaround_days", "turnaround_days", "turnaround", "tat", "cycle_time", "duration", "days", "elapsed", "handling_time", "lead_time", "age_days", "avg_turnaround_days", "processing_duration_days", "turnaround_time", "avg_days"],
        "data_types": ["numeric", "float", "integer"]
    },
    "cost": {
        "label": "Cost",
        "description": "Financial cost or spend associated with activity",
        "category": "Other",
        "keywords": ["cost", "unit_cost_gbp", "unit_cost", "spend", "expenditure", "budget_spent", "expense", "amount", "case_cost_gbp", "cost_gbp", "cost_per_case"],
        "data_types": ["numeric", "float", "integer"]
    },
    "quality_measure": {
        "label": "Quality Measure",
        "description": "Audit score, accuracy rate, error rate, compliance %",
        "category": "Other",
        "keywords": ["quality_measure", "quality_score_pct", "quality", "accuracy", "error_rate", "audit_score", "compliance", "pass_rate", "defect_rate", "first_time_fix", "quality_audit_score", "quality_score"],
        "data_types": ["numeric", "float", "integer"]
    },
    "customer_measure": {
        "label": "Customer Measure",
        "description": "CSAT, NPS, satisfaction score, complaints count",
        "category": "Other",
        "keywords": ["customer_measure", "customer_satisfaction_pct", "csat", "nps", "satisfaction", "complaints", "feedback_score", "rating", "customer_score", "customer_satisfaction", "csat_pct", "csat_score"],
        "data_types": ["numeric", "float", "integer"]
    },
    "wait_time": {
        "label": "Wait Time / Queue Delay",
        "description": "Average queue delay or customer wait duration",
        "category": "Performance",
        "keywords": ["wait_time", "waiting_time", "queue_time", "delay_days", "average_wait_minutes", "wait_minutes", "wait_hours", "queue_delay", "hold_time"],
        "data_types": ["numeric", "float", "integer"]
    },
    "numerator": {
        "label": "Custom Numerator",
        "description": "Custom subtotal or numerator for calculated ratio",
        "category": "Other",
        "keywords": ["numerator", "num", "subtotal", "portion", "count_positive", "numerator_value"],
        "data_types": ["numeric", "float", "integer"]
    },
    "denominator": {
        "label": "Custom Denominator",
        "description": "Custom base count or denominator for calculated ratio",
        "category": "Other",
        "keywords": ["denominator", "den", "base", "total_possible", "sample_size", "base_count", "population", "denominator_value"],
        "data_types": ["numeric", "float", "integer"]
    },
    "other_measure": {
        "label": "Other Metric / KPI",
        "description": "General numerical operational metric or custom indicator",
        "category": "Other",
        "keywords": ["other_measure", "other", "metric", "measure", "custom_metric", "kpi", "score", "value", "indicator"],
        "data_types": ["numeric", "float", "integer"]
    }
}

SEMANTIC_ROLES = list(ROLE_CATALOGUE.keys())


def get_role_catalogue() -> Dict[str, Any]:
    return ROLE_CATALOGUE


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(name)).lower().strip("_")


def suggest_mappings(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Analyze DataFrame columns and produce PROVISIONAL suggestions only.
    Suggested mappings NEVER activate KPIs until explicitly confirmed by the analyst.
    """
    suggestions = {}
    if df is None or len(df.columns) == 0:
        return {}
        
    for col in df.columns:
        norm_col = _normalize_name(col)
        tokens = set(norm_col.split("_"))
        series = df[col]
        is_num = pd.api.types.is_numeric_dtype(series)
        
        is_dt = pd.api.types.is_datetime64_any_dtype(series)
        if not is_dt and not is_num and len(series.dropna()) > 0:
            try:
                sample_valid = series.dropna().astype(str).str.strip().head(20)
                parsed = pd.to_datetime(sample_valid, format="mixed", errors="coerce")
                if parsed.notna().sum() / len(sample_valid) >= 0.8:
                    is_dt = True
            except Exception:
                pass
                
        best_role = None
        best_score = 0.0
        role_scores = []
        
        for role_key, role_meta in ROLE_CATALOGUE.items():
            score = 0.0
            keywords = role_meta["keywords"]
            
            # Exact match on role key or synonym
            if norm_col == role_key or norm_col in keywords:
                score = 0.95
            else:
                for kw in keywords:
                    kw_tokens = set(kw.split("_"))
                    # If all tokens of a multi-word keyword match
                    if len(kw_tokens) > 1 and kw_tokens.issubset(tokens):
                        score = max(score, 0.90)
                    elif kw in norm_col or norm_col in kw:
                        score = max(score, 0.80)
                    elif kw_tokens.issubset(tokens):
                        score = max(score, 0.75)
                    elif any(kt in tokens for kt in kw_tokens if len(kt) > 2):
                        score = max(score, 0.50)
                        
            # Role domain boosts
            if role_meta["category"] in ["Performance", "Capacity", "Other"]:
                if is_num:
                    score = min(1.0, score + 0.05) if score > 0 else 0.0
                elif not is_dt and score > 0.5:
                    score = max(0.2, score - 0.3)
                    
            if role_key in ["date", "reporting_period"]:
                if is_dt:
                    score = min(1.0, score + 0.15) if score > 0 else 0.80
                elif not is_num and any(k in norm_col for k in ["date", "time", "month", "year", "period", "quarter", "week"]):
                    score = max(score, 0.85)
                    
            if score > 0:
                role_scores.append((role_key, round(score, 2)))
                if score > best_score:
                    best_score = score
                    best_role = role_key
                    
        role_scores.sort(key=lambda x: x[1], reverse=True)
        
        suggestions[col] = {
            "suggested_role": best_role if best_score >= 0.45 else None,
            "confidence": round(best_score, 2) if best_role and best_score >= 0.45 else 0.0,
            "all_scores": role_scores[:3],
            "status": "Suggested" if best_role and best_score >= 0.45 else "Unmapped"
        }
        
    return suggestions


def suggest_column_mappings(df: pd.DataFrame) -> Dict[str, str]:
    """Simple dictionary helper returning {column_name: suggested_role_or_empty}."""
    rich_suggestions = suggest_mappings(df)
    return {col: info["suggested_role"] or "" for col, info in rich_suggestions.items()}


def validate_mappings(
    confirmed_mappings: Optional[Dict[str, str]],
    df: pd.DataFrame
) -> Dict[str, Any]:
    """Validate user CONFIRMED mappings and determine enabled analytical modules and KPIs."""
    if not confirmed_mappings:
        return {
            "role_to_col": {},
            "col_to_role": {},
            "kpi_status": {
                k: {"enabled": False, "required": [], "available": []}
                for k in ["target_achievement", "productivity", "utilisation", "backlog_observed", "backlog_reconciliation", "estimated_net_flow", "processing_time", "time_trends", "comparisons"]
            },
            "enabled_kpi_count": 0,
            "has_time": False,
            "available_dimensions": []
        }
        
    role_to_col: Dict[str, str] = {}
    for col, role in confirmed_mappings.items():
        if role and role in ROLE_CATALOGUE and col in df.columns:
            role_to_col[role] = col
            
    kpi_status = {}
    has_actual = "actual" in role_to_col or "completed" in role_to_col
    has_target = "target" in role_to_col
    kpi_status["target_achievement"] = {
        "enabled": has_actual and has_target,
        "required": ["actual (or completed)", "target"],
        "available": [r for r in ["actual", "completed", "target"] if r in role_to_col]
    }
    
    has_completed = "completed" in role_to_col or "actual" in role_to_col
    has_fte = "fte" in role_to_col
    has_staff = "staff" in role_to_col
    kpi_status["productivity"] = {
        "enabled": has_completed and (has_fte or has_staff),
        "required": ["completed", "fte (or staff)"],
        "available": [r for r in ["completed", "actual", "fte", "staff"] if r in role_to_col]
    }
    
    has_h_used = "hours_used" in role_to_col
    has_h_avail = "hours_available" in role_to_col
    kpi_status["utilisation"] = {
        "enabled": has_h_used and has_h_avail,
        "required": ["hours_used", "hours_available"],
        "available": [r for r in ["hours_used", "hours_available"] if r in role_to_col]
    }
    
    has_open_bl = "opening_backlog" in role_to_col
    has_close_bl = "closing_backlog" in role_to_col
    kpi_status["backlog_observed"] = {
        "enabled": has_open_bl and has_close_bl,
        "required": ["opening_backlog", "closing_backlog"],
        "available": [r for r in ["opening_backlog", "closing_backlog"] if r in role_to_col]
    }
    
    has_received = "received" in role_to_col
    kpi_status["backlog_reconciliation"] = {
        "enabled": has_open_bl and has_close_bl and has_received and has_completed,
        "required": ["opening_backlog", "closing_backlog", "received", "completed"],
        "available": [r for r in ["opening_backlog", "closing_backlog", "received", "completed"] if r in role_to_col]
    }
    
    kpi_status["estimated_net_flow"] = {
        "enabled": has_received and has_completed,
        "required": ["received", "completed"],
        "available": [r for r in ["received", "completed"] if r in role_to_col]
    }
    
    kpi_status["processing_time"] = {
        "enabled": "processing_time" in role_to_col,
        "required": ["processing_time"],
        "available": [r for r in ["processing_time"] if r in role_to_col]
    }
    
    has_time = "date" in role_to_col or "reporting_period" in role_to_col
    kpi_status["time_trends"] = {
        "enabled": has_time,
        "required": ["date or reporting_period"],
        "available": [r for r in ["date", "reporting_period"] if r in role_to_col]
    }
    
    dimension_roles = ["team", "department", "branch", "location", "category", "case_type", "status"]
    available_dims = [r for r in dimension_roles if r in role_to_col]
    kpi_status["comparisons"] = {
        "enabled": len(available_dims) > 0,
        "required": ["at least one dimension role"],
        "available": available_dims
    }
    
    enabled_count = sum(1 for v in kpi_status.values() if v["enabled"])
    
    return {
        "role_to_col": role_to_col,
        "col_to_role": {k: v for k, v in confirmed_mappings.items() if v},
        "kpi_status": kpi_status,
        "enabled_kpi_count": enabled_count,
        "has_time": has_time,
        "available_dimensions": available_dims
    }


def validate_mapping_integrity(df: pd.DataFrame, mappings: Dict[str, str]) -> Dict[str, List[str]]:
    """Validate mapping integrity and return errors and warnings."""
    errors = []
    warnings = []
    if not mappings:
        warnings.append("No column mappings have been confirmed yet.")
        return {"errors": errors, "warnings": warnings}
        
    for col, role in mappings.items():
        if col not in df.columns:
            errors.append(f"Mapped column '{col}' does not exist in dataset.")
            
    for col, role in mappings.items():
        if col in df.columns and role in ["actual", "target", "fte", "hours_available", "hours_used", "opening_backlog", "closing_backlog", "received", "completed", "processing_time"]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.isna().sum() > len(df) * 0.5:
                    warnings.append(f"Column '{col}' mapped to '{role}' contains >50% non-numeric values.")
                    
    return {"errors": errors, "warnings": warnings}
