"""Enterprise Data Profiling Engine for Performance Insight Explorer.
Analyzes dataset schema, distributions, cardinality, granularity, and resource requirements.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def infer_granularity_heuristic(df: pd.DataFrame) -> Tuple[str, float]:
    """Analyze dataframe columns and cardinality to infer likely data granularity.
    Returns (granularity_description, confidence_score).
    """
    if df is None or len(df) == 0:
        return "Empty Dataset", 0.0

    cols_lower = [str(c).lower() for c in df.columns]
    row_count = len(df)

    has_date = any(k in c for c in cols_lower for k in ["date", "timestamp", "time", "day"])
    has_period = any(k in c for c in cols_lower for k in ["month", "quarter", "year", "period", "week"])
    has_id = any(k in c for c in cols_lower for k in ["id", "ref", "urn", "ticket", "case_id", "user_id"])
    has_measures = any(pd.api.types.is_numeric_dtype(df[c]) for c in df.columns)

    # Check for unique IDs
    id_unique = False
    for c in df.columns:
        if any(k in str(c).lower() for k in ["id", "ref", "key", "urn", "code"]):
            if df[c].nunique() == row_count:
                id_unique = True
                break

    if id_unique and has_date:
        return "Event / Transaction Log (1 row = 1 distinct case or event)", 0.85
    elif has_id and (has_date or has_period):
        return "Periodic Snapshot (1 row = 1 entity per reporting period)", 0.80
    elif has_period and not id_unique:
        return "Aggregated Operational Summary (1 row = 1 team/service per period)", 0.75
    elif id_unique and not has_date:
        return "Master Entity Record (1 row = 1 entity profile)", 0.80
    else:
        return "Standard Operational Records (Confirm unit of analysis)", 0.50


def profile_dataset(df: pd.DataFrame, filename: str = "") -> Dict[str, Any]:
    """Generate comprehensive column-level and dataset-level profile."""
    if df is None or len(df) == 0:
        return {
            "row_count": 0,
            "col_count": 0,
            "memory_mb": 0.0,
            "columns": {},
            "inferred_granularity": "Empty Dataset",
            "granularity_confidence": 0.0,
            "potential_ids": [],
            "potential_dates": [],
            "potential_measures": [],
            "potential_dimensions": []
        }

    row_count = len(df)
    col_count = len(df.columns)
    mem_bytes = df.memory_usage(deep=True).sum()
    mem_mb = round(mem_bytes / (1024 * 1024), 2)

    granularity, gran_conf = infer_granularity_heuristic(df)

    columns_profile: Dict[str, Any] = {}
    potential_ids: List[str] = []
    potential_dates: List[str] = []
    potential_measures: List[str] = []
    potential_dimensions: List[str] = []

    date_ranges: Dict[str, Dict[str, str]] = {}

    for col in df.columns:
        series = df[col]
        non_null_count = int(series.notna().sum())
        null_count = int(series.isna().sum())
        null_pct = round((null_count / row_count) * 100.0, 2)
        unique_count = int(series.nunique(dropna=True))
        unique_pct = round((unique_count / row_count) * 100.0, 2) if row_count > 0 else 0.0

        col_lower = str(col).lower()
        inferred_type = "string"

        stats: Dict[str, Any] = {
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "unique_pct": unique_pct,
            "sample_values": series.dropna().head(5).astype(str).tolist()
        }

        # Check for numeric
        if pd.api.types.is_numeric_dtype(series):
            inferred_type = "numeric"
            num_series = series.dropna()
            if len(num_series) > 0:
                stats.update({
                    "min": float(num_series.min()),
                    "max": float(num_series.max()),
                    "mean": round(float(num_series.mean()), 2),
                    "median": round(float(num_series.median()), 2),
                    "std": round(float(num_series.std()), 2) if len(num_series) > 1 else 0.0,
                    "q25": round(float(num_series.quantile(0.25)), 2),
                    "q75": round(float(num_series.quantile(0.75)), 2),
                    "iqr": round(float(num_series.quantile(0.75) - num_series.quantile(0.25)), 2),
                    "zeros_count": int((num_series == 0).sum()),
                    "negatives_count": int((num_series < 0).sum())
                })
            potential_measures.append(str(col))

        # Check for datetime
        elif pd.api.types.is_datetime64_any_dtype(series):
            inferred_type = "datetime"
            dt_s = series.dropna()
            if len(dt_s) > 0:
                stats.update({
                    "min_date": str(dt_s.min()),
                    "max_date": str(dt_s.max()),
                    "date_span_days": (dt_s.max() - dt_s.min()).days
                })
                date_ranges[str(col)] = {"min": str(dt_s.min()), "max": str(dt_s.max())}
            potential_dates.append(str(col))

        # Check for date-like string
        elif any(k in col_lower for k in ["date", "timestamp", "time", "month", "period"]):
            # Try parse date sample
            parsed = pd.to_datetime(series.dropna().astype(str).str.strip(), errors="coerce")
            valid_dates = parsed.dropna()
            if len(valid_dates) > 0 and len(valid_dates) / max(len(series.dropna()), 1) >= 0.7:
                inferred_type = "datetime"
                stats.update({
                    "min_date": str(valid_dates.min()),
                    "max_date": str(valid_dates.max()),
                    "date_span_days": (valid_dates.max() - valid_dates.min()).days
                })
                date_ranges[str(col)] = {"min": str(valid_dates.min()), "max": str(valid_dates.max())}
                potential_dates.append(str(col))
            else:
                inferred_type = "category" if unique_count < 100 else "string"
                potential_dimensions.append(str(col))

        # Check for ID
        elif any(k in col_lower for k in ["id", "ref", "key", "urn", "code", "ticket", "user"]) and unique_pct > 80.0:
            inferred_type = "identifier"
            potential_ids.append(str(col))

        else:
            inferred_type = "category" if unique_count < 100 else "string"
            potential_dimensions.append(str(col))

        stats["inferred_type"] = inferred_type
        columns_profile[str(col)] = stats

    return {
        "filename": filename,
        "row_count": row_count,
        "col_count": col_count,
        "memory_mb": mem_mb,
        "inferred_granularity": granularity,
        "granularity_confidence": gran_conf,
        "columns": columns_profile,
        "potential_ids": potential_ids,
        "potential_dates": potential_dates,
        "potential_measures": potential_measures,
        "potential_dimensions": potential_dimensions,
        "date_ranges": date_ranges
    }
