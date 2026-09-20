"""Intelligent Semantic Column Mapping Engine for Performance Insight Explorer.
Maps heterogeneous column schemas to standardized analytical roles across sectors:
Government, Healthcare, Retail & Consumer Pricing, Sales, Customer Service, HR, Manufacturing, Finance, and Operations.

Calculates confidence scores using:
1. Lexical and semantic token matching
2. Column data type suitability
3. Statistical cardinality & value distributions
4. Unique value heuristics and repetition penalties
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
        "description": "Unique key per item, transaction, case, ticket, application, patient, or customer",
        "category": "Identity",
        "keywords": ["item_id", "record_id", "unique_id", "case_id", "case_ref", "app_id", "application_id", "patient_id", "account_id", "txn_id", "order_id", "user_id", "reference", "urn", "ticket_id"],
        "expected_types": ["string", "integer", "numeric"],
        "min_cardinality_pct": 0.50
    },
    "date": {
        "label": "Date / Timestamp",
        "description": "Primary chronological event, date, submission, receipt, or transaction timestamp",
        "category": "Time",
        "keywords": ["date", "timestamp", "datetime", "transaction_date", "trans_date", "created_at", "received_date", "completion_date", "submission_date", "event_date", "log_date", "month_date", "day", "week"],
        "expected_types": ["datetime", "date", "string"],
        "min_cardinality_pct": 0.001
    },
    "reporting_period": {
        "label": "Reporting Period / Cycle",
        "description": "Aggregated calendar interval (e.g., Month, Quarter, Financial Year, Cycle)",
        "category": "Time",
        "keywords": ["period", "reporting_period", "month", "quarter", "year", "fin_year", "fy", "cycle", "cal_month", "period_name", "reporting_month"],
        "expected_types": ["string", "category", "integer"],
        "min_cardinality_pct": 0.001
    },
    "volume_inflow": {
        "label": "Volume Inflow / Demand",
        "description": "Incoming demand volume, cases received, applications, contacts, or tickets opened",
        "category": "Metric",
        "keywords": ["cases_received", "received", "inflow", "incoming", "demand", "new_cases", "applications_received", "intake", "contacts", "tickets_opened", "referrals_received"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "actual": {
        "label": "Actual Performance / Completed Output",
        "description": "Observed volume completed, cases closed, resolved output, or delivered units",
        "category": "Metric",
        "keywords": ["cases_completed", "completed", "actual", "achieved", "output", "delivered", "cases_closed", "resolved_cases", "resolved", "volume_out"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "kpi_metric": {
        "label": "Performance Metric / KPI Value",
        "description": "Primary quantitative performance measure, price, cost, revenue, rate, score, or volume",
        "category": "Metric",
        "keywords": [
            "reported_price", "price", "cost", "revenue", "sales", "amount", "value",
            "score", "rate", "count", "volume", "duration", "waiting_time", "response_time",
            "productivity", "performance", "total_sales", "actual_revenue",
            "metric", "total_cost", "spend", "target_achievement", "efficiency"
        ],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "category": {
        "label": "Category / Group Dimension",
        "description": "Category, classification, cohort, sector, business domain, or grouping dimension",
        "category": "Dimension",
        "keywords": ["category", "category_name", "group", "grouping", "classification", "sector", "division", "segment", "cluster"],
        "expected_types": ["string", "category"],
        "min_cardinality_pct": 0.001
    },
    "category_code": {
        "label": "Category Code / Numeric Group",
        "description": "Numeric category code, grouping ID, classification index, or category number",
        "category": "Dimension",
        "keywords": ["category_num", "cat_num", "category_no", "category_code", "cat_code", "group_code", "group_num", "class_num", "type_code", "cat_id"],
        "expected_types": ["integer", "numeric", "string"],
        "min_cardinality_pct": 0.001
    },
    "product_service": {
        "label": "Product / Item Dimension",
        "description": "Product name, item description, service line, good, article, or offering dimension",
        "category": "Dimension",
        "keywords": ["item_name", "item", "product", "product_name", "service", "offering", "specialty", "case_type", "application_type", "commodity", "sku", "good", "article"],
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
        "description": "Geographical territory, region, district, site, depot, ward, or location",
        "category": "Dimension",
        "keywords": ["region", "location", "territory", "area", "zone", "site", "district", "city", "postcode", "country", "ward", "hub"],
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
    "target": {
        "label": "Target / Goal Benchmark",
        "description": "Performance standard, SLA threshold, quota, budget, or planned volume",
        "category": "Metric",
        "keywords": ["target", "expected", "goal", "benchmark", "sla", "standard", "budget", "quota", "planned", "sla_target"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.001
    },
    "numerator": {
        "label": "KPI Numerator",
        "description": "Numerator measure for custom rate or percentage calculations",
        "category": "Metric",
        "keywords": ["numerator", "passed_count", "compliant_cases", "errors", "successes", "hits", "positive_outcomes", "resolved_cases"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "denominator": {
        "label": "KPI Denominator",
        "description": "Denominator measure or base population for rate calculations",
        "category": "Metric",
        "keywords": ["denominator", "total_audited", "sample_size", "total_population", "eligible_cases", "opportunities", "total_cases"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "duration_wait_time": {
        "label": "Duration / Waiting Time",
        "description": "Processing duration, turnaround days, wait time, cycle time, or queue delay",
        "category": "Metric",
        "keywords": ["duration", "processing_time", "turnaround", "wait_time", "cycle_time", "lead_time", "tat", "latency", "days_to_close", "turnaround_days"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "capacity_fte": {
        "label": "Capacity / FTE Workforce",
        "description": "Full-Time Equivalent staff, headcount, available hours, or machine capacity",
        "category": "Metric",
        "keywords": ["fte", "headcount", "staff", "workforce", "capacity", "hours_available", "agents", "resources", "contracted_hours", "staff_fte"],
        "expected_types": ["numeric"],
        "min_cardinality_pct": 0.01
    },
    "predictor_driver": {
        "label": "Predictor / Operational Driver",
        "description": "Explanatory variable, complexity score, tenure, or operational condition",
        "category": "Diagnostic",
        "keywords": ["complexity", "experience", "tenure", "escalation", "seniority", "priority", "difficulty", "risk_score"],
        "expected_types": ["numeric", "category", "string"],
        "min_cardinality_pct": 0.001
    }
}


def suggest_semantic_mappings(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Infer recommended semantic roles for all columns in dataframe with confidence scores.
    Returns {column_name: {"suggested_role": str, "confidence": float, "reasoning": str, "category": str, "label": str}}.
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
        col_snake = "_".join(col_clean.split())
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
                if kw == col_clean or kw == col_snake:
                    conf += 0.70
                    reasons.append(f"Exact match on keyword '{kw}'")
                    break
                elif kw in tokens:
                    conf += 0.55
                    reasons.append(f"Contains token keyword '{kw}'")
                    break
                elif len(kw) >= 5 and kw in col_snake:
                    conf += 0.40
                    reasons.append(f"Contains keyword substring '{kw}'")
                    break

            # 2. Data Type Compatibility
            exp_types = meta["expected_types"]
            if "numeric" in exp_types and is_numeric:
                conf += 0.25
                reasons.append("Matches numeric data type")
            elif "datetime" in exp_types and (is_datetime or "date" in tokens or "timestamp" in tokens):
                conf += 0.35
                reasons.append("Matches temporal data type")
            elif "string" in exp_types and not is_numeric and not is_datetime:
                conf += 0.15
                reasons.append("Matches categorical/string data type")

            # 3. Cardinality & Distribution Suitability
            if role_key == "record_id":
                if unique_ratio >= 0.70:
                    conf += 0.25
                    reasons.append("High uniqueness ratio (>70%)")
                elif unique_ratio < 0.30 or any(c in col_clean for c in ["category", "cat_num", "group", "class", "tier", "grade", "cases_received", "cases_completed", "turnaround", "count"]):
                    conf -= 0.60
                    reasons.append("Low cardinality: repeating values not suitable for unique identifier")
            elif role_key in ["category", "category_code"] and (unique_count < 100 or unique_ratio < 0.30):
                conf += 0.20
                reasons.append("Categorical grouping distribution")
            elif meta["category"] == "Dimension" and unique_count < 100 and unique_ratio < 0.30:
                conf += 0.15
                reasons.append("Categorical distribution")

            # Penalties for mismatched types
            if "numeric" in exp_types and not is_numeric:
                conf -= 0.40
            if "datetime" in exp_types and not is_datetime and not any(k in col_clean for k in ["date", "time", "month", "period", "timestamp", "year"]):
                conf -= 0.40
            if meta["category"] == "Dimension" and is_datetime:
                conf -= 0.50

            conf = min(1.0, max(0.0, conf))

            if conf > best_confidence:
                best_confidence = round(conf, 2)
                best_role = role_key
                best_reason = "; ".join(reasons) if reasons else "Heuristic match"

        # Explicit heuristic overrides for precision
        if "category_num" in col_clean or "cat_num" in col_clean:
            if best_role == "record_id" or best_confidence < 0.40:
                best_role = "category_code"
                best_confidence = 0.85
                best_reason = "Identified as numeric category classification code"

        if "cases_received" in col_snake:
            best_role = "volume_inflow"
            best_confidence = 0.95
            best_reason = "Exact match on demand inflow measure"

        if "cases_completed" in col_snake:
            best_role = "actual"
            best_confidence = 0.95
            best_reason = "Exact match on actual output measure"

        if is_datetime or col_snake == "transaction_date" or (("date" in tokens or "timestamp" in tokens) and not is_numeric):
            if best_role != "date":
                best_role = "date"
                best_confidence = 0.95
                best_reason = "Identified as chronological date dimension"

        results[col_str] = {
            "suggested_role": best_role if best_confidence >= 0.35 else "unmapped",
            "confidence": best_confidence if best_confidence >= 0.35 else 0.0,
            "reasoning": best_reason if best_confidence >= 0.35 else "No strong semantic pattern detected",
            "category": SEMANTIC_ROLE_CATALOG.get(best_role, {}).get("category", "Unassigned") if best_role else "Unassigned",
            "label": SEMANTIC_ROLE_CATALOG.get(best_role, {}).get("label", "Unmapped") if best_role else "Unmapped"
        }

    return results
