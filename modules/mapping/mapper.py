"""Intelligent Semantic Column Mapping Engine for Performance Insight Explorer.
Maps heterogeneous column schemas to standardized analytical roles across sectors:
Government, Healthcare, Sales, Customer Service, HR, Manufacturing, Finance, and Operations.

Calculates confidence scores using:
1. Lexical and semantic token matching
2. Column data type suitability
3. Statistical cardinality & value distributions
4. Value pattern heuristics
"""
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from core.security import is_index_like_column


SEMANTIC_ROLE_CATALOG = {
    "index_identifier": {
        "label": "Index / Row Position",
        "description": "Sequential row position, dataframe index, or unnamed imported column",
        "category": "System",
        "keywords": ["unnamed", "index", "idx", "row_num", "row_number", "level_0"],
        "expected_types": ["integer", "numeric"],
        "min_cardinality_pct": 0.80
    },
    "record_id": {
        "label": "Unique Identifier",
        "description": "Unique key per case, ticket, application, patient, transaction, or customer",
        "category": "Identity",
        "keywords": ["id", "identifier", "ref", "reference", "urn", "ticket", "case_id", "case_ref", "app_id", "application_id", "patient_id", "account_id", "txn_id", "order_id", "user_id"],
        "expected_types": ["string", "integer"],
        "min_cardinality_pct": 0.70
    },
    "date": {
        "label": "Date / Timestamp",
        "description": "Primary chronological event, submission, receipt, or transaction timestamp",
        "category": "Time",
        "keywords": ["date", "timestamp", "datetime", "created_at", "received_date", "completion_date", "submission_date", "event_date", "log_date", "trans_date"],
        "expected_types": ["datetime", "date", "string"],
        "min_cardinality_pct": 0.01
    },
    "reporting_period": {
        "label": "Reporting Period / Cycle",
        "description": "Aggregated calendar interval (e.g., Month, Quarter, Financial Year, Cycle)",
        "category": "Time",
        "keywords": ["period", "reporting_period", "month", "quarter", "year", "fin_year", "fy", "cycle", "cal_month", "period_name"],
        "expected_types": ["string", "category", "integer"],
        "min_cardinality_pct": 0.001
    },
    "entity": {
        "label": "Entity / Organization",
        "description": "Organization, hospital trust, council, subsidiary, legal entity, or client",
        "category": "Dimension",
        "keywords": ["organization", "entity", "company", "trust", "council", "firm", "client", "institution", "agency", "authority"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "department": {
        "label": "Department / Directorate",
        "description": "High-level functional division, directorate, department, or business unit",
        "category": "Dimension",
        "keywords": ["department", "dept", "division", "directorate", "function", "business_unit", "faculty", "service_line"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "team": {
        "label": "Team / Squad",
        "description": "Operational squad, handling team, pod, branch, or clinical unit executing the work",
        "category": "Dimension",
        "keywords": ["team", "squad", "pod", "unit", "operational_team", "service_team", "work_group", "crew", "handling_team"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "region": {
        "label": "Region / Geography",
        "description": "Geographical territory, region, district, site, depot, or location",
        "category": "Dimension",
        "keywords": ["region", "location", "territory", "area", "zone", "site", "district", "city", "postcode", "country", "hub"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "product_service": {
        "label": "Product / Service Line",
        "description": "Service stream, product family, offering, curriculum, or clinical specialty",
        "category": "Dimension",
        "keywords": ["product", "service", "offering", "specialty", "case_type", "application_type", "stream", "workstream", "service_type"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "customer_segment": {
        "label": "Customer / User Group",
        "description": "Service user cohort, customer tier, patient category, demographic, or persona",
        "category": "Dimension",
        "keywords": ["customer", "client_type", "user_group", "patient_type", "cohort", "tier", "segment", "demographic", "grade", "band"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "status": {
        "label": "Status / Lifecycle State",
        "description": "Current workflow state (e.g. Open, In Progress, Closed, Pending, Escalated)",
        "category": "Dimension",
        "keywords": ["status", "state", "stage", "phase", "case_status", "disposition", "condition", "progress"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "actual": {
        "label": "Actual Performance / Output",
        "description": "Observed volume delivered, achieved performance, or completed output",
        "category": "Metric",
        "keywords": ["actual", "achieved", "output", "delivered", "result", "cases_completed", "completed", "closed", "resolved", "volume_out"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "target": {
        "label": "Target / Goal Benchmark",
        "description": "Performance standard, SLA threshold, quota, or planned volume",
        "category": "Metric",
        "keywords": ["target", "expected", "goal", "benchmark", "sla", "standard", "budget", "quota", "planned", "sla_target"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.001
    },
    "benchmark": {
        "label": "External Benchmark / Peer Baseline",
        "description": "National benchmark, peer group standard, or regulatory ceiling",
        "category": "Metric",
        "keywords": ["benchmark", "peer_avg", "national_avg", "industry_standard", "regulatory_limit"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.001
    },
    "volume_inflow": {
        "label": "Volume Inflow / Cases Received",
        "description": "Incoming demand volume, applications received, contacts made, or arrivals",
        "category": "Metric",
        "keywords": ["received", "inflow", "incoming", "demand", "new_cases", "applications", "intake", "contacts", "tickets_opened"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "numerator": {
        "label": "KPI Numerator",
        "description": "Numerator measure for custom rate or percentage calculations",
        "category": "Metric",
        "keywords": ["numerator", "passed_count", "compliant_cases", "errors", "successes", "hits", "positive_outcomes"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "denominator": {
        "label": "KPI Denominator",
        "description": "Denominator measure or base population for rate calculations",
        "category": "Metric",
        "keywords": ["denominator", "total_audited", "sample_size", "total_population", "eligible_cases", "opportunities"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "cost": {
        "label": "Cost / Expenditure",
        "description": "Direct cost, operational spend, unit cost, or expenditure amount",
        "category": "Metric",
        "keywords": ["cost", "spend", "expenditure", "budget_used", "expense", "unit_cost", "direct_cost"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "revenue": {
        "label": "Revenue / Income",
        "description": "Sales revenue, billing, income, recovery, or earned fee",
        "category": "Metric",
        "keywords": ["revenue", "income", "sales", "turnover", "billing", "fees", "collections"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "quality_measure": {
        "label": "Quality / Accuracy Score",
        "description": "Customer satisfaction (CSAT), audit quality score, error rate, or compliance %",
        "category": "Metric",
        "keywords": ["quality", "csat", "nps", "satisfaction", "compliance", "accuracy", "error_rate", "defect_rate", "score"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "duration_wait_time": {
        "label": "Duration / Waiting Time",
        "description": "Processing duration, turnaround days, wait time, cycle time, or queue delay",
        "category": "Metric",
        "keywords": ["duration", "processing_time", "turnaround", "wait_time", "cycle_time", "lead_time", "tat", "latency", "days_to_close"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "capacity_fte": {
        "label": "Capacity / FTE Workforce",
        "description": "Full-Time Equivalent staff, headcount, available hours, or machine capacity",
        "category": "Metric",
        "keywords": ["fte", "headcount", "staff", "workforce", "capacity", "hours_available", "agents", "resources"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "backlog_opening": {
        "label": "Opening Backlog / WIP",
        "description": "Queue inventory or work-in-progress cases at start of period",
        "category": "Metric",
        "keywords": ["opening_backlog", "start_backlog", "initial_queue", "opening_wip", "open_start"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "backlog_closing": {
        "label": "Closing Backlog / WIP",
        "description": "Queue inventory or work-in-progress cases at end of period",
        "category": "Metric",
        "keywords": ["closing_backlog", "end_backlog", "final_queue", "closing_wip", "open_end", "outstanding"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "predictor_driver": {
        "label": "Predictor / Operational Driver",
        "description": "Explanatory variable, complexity score, tenure, or operational condition",
        "category": "Diagnostic",
        "keywords": ["complexity", "experience", "tenure", "escalation", "seniority", "priority", "difficulty"],
        "expected_types": ["numeric", "category", "string"],
        "min_cardinality_pct": 0.001
    }
}


def suggest_semantic_mappings(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Infer recommended semantic roles for all columns in dataframe with confidence scores.
    Returns {column_name: {"suggested_role": str, "confidence": float, "reasoning": str, "category": str}}.
    """
    if df is None or len(df) == 0:
        return {}

    row_count = len(df)
    results: Dict[str, Dict[str, Any]] = {}

    for col in df.columns:
        col_str = str(col)
        series = df[col]

        # Prioritize index-like / unnamed columns
        if is_index_like_column(col, series):
            results[col_str] = {
                "suggested_role": "index_identifier",
                "confidence": 0.95,
                "reasoning": "Index-like sequential/unnamed column; excluded from automatic date and metric recommendations",
                "category": "System",
                "label": "Index / Row Position"
            }
            continue

        col_clean = re.sub(r"[^a-zA-Z0-9_]", " ", col_str).lower().strip()
        tokens = set(col_clean.split())
        non_null_count = series.notna().sum()
        unique_count = series.nunique(dropna=True)
        unique_ratio = (unique_count / max(non_null_count, 1))

        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_datetime = pd.api.types.is_datetime64_any_dtype(series)

        best_role: Optional[str] = None
        best_confidence: float = 0.0
        best_reason: str = "Default unassigned"

        for role_key, meta in SEMANTIC_ROLE_CATALOG.items():
            conf = 0.0
            reasons = []

            # 1. Lexical Keyword Matching
            keywords = meta["keywords"]
            for kw in keywords:
                if kw == col_clean:
                    conf += 0.65
                    reasons.append(f"Exact match on keyword '{kw}'")
                    break
                elif kw in tokens:
                    conf += 0.50
                    reasons.append(f"Contains token keyword '{kw}'")
                    break
                elif len(kw) >= 4 and kw in col_clean:
                    conf += 0.40
                    reasons.append(f"Contains keyword substring '{kw}'")
                    break

            # 2. Data Type Compatibility
            exp_types = meta["expected_types"]
            if "numeric" in exp_types and is_numeric:
                conf += 0.25
                reasons.append("Matches numeric data type")
            elif "datetime" in exp_types and (is_datetime or "date" in col_clean):
                conf += 0.30
                reasons.append("Matches temporal data type")
            elif "string" in exp_types and not is_numeric:
                conf += 0.15
                reasons.append("Matches categorical/string data type")

            # 3. Cardinality & Distribution Suitability
            if role_key == "record_id" and unique_ratio >= 0.80:
                conf += 0.25
                reasons.append("High cardinality (>80% unique)")
            elif meta["category"] == "Dimension" and unique_count < 100 and unique_ratio < 0.20:
                conf += 0.15
                reasons.append("Categorical grouping distribution")

            # Penalties for mismatched types
            if "numeric" in exp_types and not is_numeric:
                conf -= 0.40
            if role_key == "record_id" and unique_ratio < 0.20:
                conf -= 0.30

            conf = min(1.0, max(0.0, conf))

            if conf > best_confidence:
                best_confidence = round(conf, 2)
                best_role = role_key
                best_reason = "; ".join(reasons) if reasons else "Heuristic match"

        results[col_str] = {
            "suggested_role": best_role if best_confidence >= 0.35 else "unmapped",
            "confidence": best_confidence if best_confidence >= 0.35 else 0.0,
            "reasoning": best_reason if best_confidence >= 0.35 else "No strong semantic pattern detected",
            "category": SEMANTIC_ROLE_CATALOG.get(best_role, {}).get("category", "Unassigned") if best_role else "Unassigned",
            "label": SEMANTIC_ROLE_CATALOG.get(best_role, {}).get("label", "Unmapped") if best_role else "Unmapped"
        }

    return results
