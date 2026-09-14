"""Data profiling module for Performance Insight Explorer.
Calculates structural statistics, data types, candidate roles, uniqueness, and value distributions.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def profile_dataset(df: pd.DataFrame, filename: str = "", sheet_name: str = "") -> Dict[str, Any]:
    """Generate a comprehensive profile of the input DataFrame."""
    row_count = len(df)
    col_count = len(df.columns)
    
    memory_bytes = int(df.memory_usage(deep=True).sum())
    if memory_bytes < 1024:
        memory_str = f"{memory_bytes} B"
    elif memory_bytes < 1024 * 1024:
        memory_str = f"{memory_bytes / 1024:.1f} KB"
    else:
        memory_str = f"{memory_bytes / (1024 * 1024):.2f} MB"
        
    column_profiles = []
    candidate_dates = []
    candidate_numerics = []
    candidate_categoricals = []
    candidate_ids = []
    
    for col in df.columns:
        series = df[col]
        non_null_count = int(series.notna().sum())
        null_count = int(series.isna().sum())
        null_pct = round((null_count / row_count * 100.0) if row_count > 0 else 0.0, 2)
        unique_count = int(series.nunique(dropna=True))
        
        sample_vals = series.dropna().unique()[:5].tolist()
        sample_vals_str = [str(x) for x in sample_vals]
        
        is_numeric = False
        is_datetime = False
        is_categorical = False
        is_id = False
        is_constant = (unique_count <= 1)
        inferred_type = "text"
        
        if pd.api.types.is_numeric_dtype(series):
            is_numeric = True
            inferred_type = "integer" if pd.api.types.is_integer_dtype(series) else "numeric"
        else:
            valid_series = series.dropna().astype(str).str.strip()
            if len(valid_series) > 0:
                coerced = pd.to_numeric(valid_series, errors="coerce")
                if coerced.notna().sum() / len(valid_series) > 0.8:
                    is_numeric = True
                    inferred_type = "numeric (text-encoded)"
                    
        if not is_numeric or not pd.api.types.is_numeric_dtype(series):
            valid_series = series.dropna().astype(str).str.strip()
            if len(valid_series) > 0:
                try:
                    test_sample = valid_series.head(100)
                    parsed = pd.to_datetime(test_sample, errors="coerce")
                    if parsed.notna().sum() / len(test_sample) >= 0.7:
                        is_datetime = True
                        inferred_type = "datetime"
                except Exception:
                    pass
                    
        if is_datetime or pd.api.types.is_datetime64_any_dtype(series):
            is_datetime = True
            inferred_type = "datetime"
            
        if not is_numeric and not is_datetime:
            if unique_count > 0 and (unique_count <= 50 or (row_count > 0 and unique_count / row_count < 0.2)):
                is_categorical = True
                inferred_type = "categorical"
            else:
                inferred_type = "text"
                
        if unique_count > 0 and row_count > 0 and (unique_count / row_count >= 0.95):
            is_id = True
            candidate_ids.append(col)
            
        numeric_summary = {}
        if is_numeric:
            s_num = pd.to_numeric(series, errors="coerce").dropna()
            if len(s_num) > 0:
                numeric_summary = {
                    "min": float(s_num.min()),
                    "max": float(s_num.max()),
                    "mean": round(float(s_num.mean()), 2),
                    "median": round(float(s_num.median()), 2),
                    "std": round(float(s_num.std()), 2) if len(s_num) > 1 else 0.0,
                    "zero_count": int((s_num == 0).sum()),
                    "negative_count": int((s_num < 0).sum())
                }
                candidate_numerics.append(col)
                
        datetime_summary = {}
        if is_datetime:
            try:
                s_dt = pd.to_datetime(series, errors="coerce").dropna()
                if len(s_dt) > 0:
                    min_d = s_dt.min().strftime("%Y-%m-%d")
                    max_d = s_dt.max().strftime("%Y-%m-%d")
                    span_days = int((s_dt.max() - s_dt.min()).days)
                    datetime_summary = {
                        "min_date": min_d,
                        "max_date": max_d,
                        "date_span_days": span_days,
                        "parsed_count": int(len(s_dt))
                    }
                    candidate_dates.append(col)
            except Exception:
                pass
                
        cat_summary = {}
        if is_categorical or unique_count <= 20:
            top_counts = series.value_counts(dropna=True).head(5).to_dict()
            cat_summary = {
                "top_categories": {str(k): int(v) for k, v in top_counts.items()}
            }
            if col not in candidate_dates and col not in candidate_numerics:
                candidate_categoricals.append(col)
                
        col_prof = {
            "name": col,
            "dtype": str(series.dtype),
            "inferred_type": inferred_type,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "is_constant": is_constant,
            "is_id": is_id,
            "sample_values": sample_vals_str,
            "numeric_summary": numeric_summary,
            "datetime_summary": datetime_summary,
            "categorical_summary": cat_summary
        }
        column_profiles.append(col_prof)
        
    global_date_range = None
    if candidate_dates:
        first_d_col = candidate_dates[0]
        s_dt = pd.to_datetime(df[first_d_col], errors="coerce").dropna()
        if len(s_dt) > 0:
            global_date_range = {
                "column": first_d_col,
                "min": s_dt.min().strftime("%Y-%m-%d"),
                "max": s_dt.max().strftime("%Y-%m-%d"),
                "span_days": int((s_dt.max() - s_dt.min()).days)
            }
            
    return {
        "filename": filename,
        "sheet_name": sheet_name,
        "row_count": row_count,
        "column_count": col_count,
        "memory_usage_bytes": memory_bytes,
        "memory_usage_str": memory_str,
        "columns": column_profiles,
        "candidate_dates": candidate_dates,
        "candidate_numerics": candidate_numerics,
        "candidate_categoricals": candidate_categoricals,
        "candidate_ids": candidate_ids,
        "global_date_range": global_date_range,
        "head_records": df.head(10).to_dict(orient="records"),
        "tail_records": df.tail(10).to_dict(orient="records")
    }
