"""Relationship and Multi-Dataset Join Engine.
Provides relationship validation, key integrity analysis, and joined analytical model generation.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def validate_relationship(
    left_df: pd.DataFrame,
    left_key: str,
    right_df: pd.DataFrame,
    right_key: str,
    left_name: str = "Primary",
    right_name: str = "Reference"
) -> Dict[str, Any]:
    """Validate the join integrity between two datasets on specified key columns.
    
    Returns detailed metrics:
    - Match count and match percentage
    - Unmatched rows count
    - Duplicate key detection in reference table
    - Null / missing key counts
    - Cardinality assessment
    - Diagnostic warnings and status
    """
    if left_df is None or right_df is None:
        return {
            "is_valid": False,
            "status": "ERROR",
            "warnings": ["One or both datasets are not loaded."],
            "match_rate": 0.0,
            "matched_rows": 0,
            "unmatched_rows": 0,
            "left_total_rows": 0,
            "right_total_rows": 0,
            "right_duplicates": 0
        }

    if left_key not in left_df.columns:
        return {
            "is_valid": False,
            "status": "ERROR",
            "warnings": [f"Key column '{left_key}' not found in '{left_name}' dataset."],
            "match_rate": 0.0,
            "matched_rows": 0,
            "unmatched_rows": len(left_df),
            "left_total_rows": len(left_df),
            "right_total_rows": len(right_df),
            "right_duplicates": 0
        }

    if right_key not in right_df.columns:
        return {
            "is_valid": False,
            "status": "ERROR",
            "warnings": [f"Key column '{right_key}' not found in '{right_name}' dataset."],
            "match_rate": 0.0,
            "matched_rows": 0,
            "unmatched_rows": len(left_df),
            "left_total_rows": len(left_df),
            "right_total_rows": len(right_df),
            "right_duplicates": 0
        }

    left_s = left_df[left_key]
    right_s = right_df[right_key]

    left_total = len(left_df)
    right_total = len(right_df)

    # Missing / Null key counts
    left_nulls = int(left_s.isnull().sum() + (left_s == "").sum())
    right_nulls = int(right_s.isnull().sum() + (right_s == "").sum())

    # Right duplicates
    right_valid_keys = right_s.dropna()
    right_duplicates = int(right_valid_keys.duplicated().sum())

    # Match computation
    right_key_set = set(right_valid_keys.astype(str).str.strip())
    
    # Check string match
    left_str_keys = left_s.dropna().astype(str).str.strip()
    matched_mask = left_str_keys.isin(right_key_set)
    matched_rows = int(matched_mask.sum())
    unmatched_rows = left_total - matched_rows
    match_rate = float(matched_rows / left_total) if left_total > 0 else 0.0

    warnings = []
    status = "OPTIMAL"

    if match_rate == 1.0 and right_duplicates == 0 and left_nulls == 0:
        status = "OPTIMAL"
    elif match_rate >= 0.95:
        status = "GOOD"
    elif match_rate >= 0.70:
        status = "WARNING"
        warnings.append(f"Join coverage is {match_rate:.1%}. {unmatched_rows:,} rows in '{left_name}' do not match '{right_name}'.")
    else:
        status = "ERROR" if match_rate == 0.0 else "WARNING"
        warnings.append(f"Low join coverage: {match_rate:.1%} ({matched_rows:,}/{left_total:,} rows matched).")

    if right_duplicates > 0:
        warnings.append(f"Reference dataset '{right_name}' contains {right_duplicates:,} duplicate key values. A join may multiply primary rows unless deduplicated.")
        if status == "OPTIMAL":
            status = "WARNING"

    if left_nulls > 0:
        warnings.append(f"Primary dataset '{left_name}' contains {left_nulls:,} empty or null key values.")

    if right_nulls > 0:
        warnings.append(f"Reference dataset '{right_name}' contains {right_nulls:,} empty or null key values.")

    # Cardinality
    if right_duplicates == 0:
        cardinality = "Many-to-One (Look-up)"
    else:
        cardinality = "Many-to-Many"

    return {
        "is_valid": match_rate > 0.0,
        "status": status,
        "left_name": left_name,
        "right_name": right_name,
        "left_key": left_key,
        "right_key": right_key,
        "left_total_rows": left_total,
        "right_total_rows": right_total,
        "left_unique_keys": int(left_s.nunique(dropna=True)),
        "right_unique_keys": int(right_s.nunique(dropna=True)),
        "matched_rows": matched_rows,
        "unmatched_rows": unmatched_rows,
        "match_rate": match_rate,
        "right_duplicates": right_duplicates,
        "left_nulls": left_nulls,
        "right_nulls": right_nulls,
        "cardinality": cardinality,
        "warnings": warnings
    }


def build_joined_analytical_model(
    primary_df: pd.DataFrame,
    relationships: List[Dict[str, Any]],
    datasets: Dict[str, Any],
    compute_derived: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Join primary dataset with reference datasets and compute standard derived analytical fields.
    
    Handles:
    - Left joins to preserve all primary records
    - Automatic deduplication of 1-to-many reference tables if key duplicates exist
    - Semantic alignment (e.g. Operational Area -> Service, Band -> Band)
    - Error-safe, uncapped Availability % calculation
    - Service A & Band 3 conditional evaluation
    """
    if primary_df is None or len(primary_df) == 0:
        return primary_df, {"status": "EMPTY", "joined_rows": 0, "joins_applied": 0}

    model_df = primary_df.copy(deep=True)
    # Strip unnamed columns from Excel exports
    model_df = model_df.loc[:, ~model_df.columns.astype(str).str.contains("^Unnamed", na=False)]

    joins_applied = 0
    join_reports = []

    for rel in relationships:
        right_ds_id = rel.get("right_dataset_id") or rel.get("right_dataset")
        right_ds_info = datasets.get(right_ds_id)
        if not right_ds_info or right_ds_info.get("clean_df") is None:
            continue

        right_df = right_ds_info["clean_df"].copy(deep=True)
        right_df = right_df.loc[:, ~right_df.columns.astype(str).str.contains("^Unnamed", na=False)]

        left_key = rel.get("left_key", "")
        right_key = rel.get("right_key", "")
        join_type = rel.get("join_type", "left")

        if left_key not in model_df.columns or right_key not in right_df.columns:
            continue

        # Deduplicate reference table on right_key if duplicates exist
        if right_df[right_key].duplicated().any():
            right_df = right_df.drop_duplicates(subset=[right_key], keep="first")

        # Select non-conflicting columns from right_df
        # If right_df contains 'Operational Area' and model doesn't have 'Service', we'll bring it over
        cols_to_use = [right_key]
        for col in right_df.columns:
            if col == right_key:
                continue
            if col in model_df.columns:
                # If primary column is all null or empty, drop it from model so reference replaces it
                if model_df[col].isnull().all():
                    model_df = model_df.drop(columns=[col])
                    cols_to_use.append(col)
                else:
                    # Rename reference column to avoid collision
                    right_df = right_df.rename(columns={col: f"{col}_ref"})
                    cols_to_use.append(f"{col}_ref")
            else:
                cols_to_use.append(col)

        sub_right = right_df[cols_to_use].copy()
        
        # Ensure join key types match (convert to string if mixed)
        model_df[left_key] = model_df[left_key].astype(str).str.strip()
        sub_right[right_key] = sub_right[right_key].astype(str).str.strip()

        model_df = pd.merge(model_df, sub_right, left_on=left_key, right_on=right_key, how=join_type)
        
        # If left_key != right_key, drop the redundant right_key
        if left_key != right_key and right_key in model_df.columns:
            model_df = model_df.drop(columns=[right_key])

        joins_applied += 1
        join_reports.append({
            "right_dataset": right_ds_info.get("name", right_ds_id),
            "left_key": left_key,
            "right_key": right_key,
            "join_type": join_type
        })

    # Post-join semantic alignment
    if "Operational Area" in model_df.columns and ("Service" not in model_df.columns or model_df["Service"].isnull().all()):
        model_df["Service"] = model_df["Operational Area"]

    if compute_derived:
        # Question 1: Uncapped Availability % = Available Hours / Contracted Hours
        # Safe division: blank/NaN where Contracted Hours is 0, null, or missing
        avail_col = None
        contract_col = None
        for col in model_df.columns:
            col_l = col.lower().strip()
            if "avail" in col_l and "hour" in col_l:
                avail_col = col
            elif "contract" in col_l and "hour" in col_l:
                contract_col = col

        if avail_col and contract_col:
            num = pd.to_numeric(model_df[avail_col], errors="coerce")
            denom = pd.to_numeric(model_df[contract_col], errors="coerce")
            
            valid_mask = denom.notnull() & (denom != 0) & num.notnull()
            # Calculate uncapped Availability %
            calculated_avail = np.where(valid_mask, num / denom, np.nan)
            
            # If 'Availability %' or 'Availabilty %' exists in source, prioritize clean calculation
            target_avail_col = "Availability %"
            for col in model_df.columns:
                if "avail" in col.lower() and "%" in col:
                    target_avail_col = col
                    break
            model_df[target_avail_col] = calculated_avail

        # Question 3: Service A & Band 3 condition
        if "Service" in model_df.columns and "Band" in model_df.columns:
            band_str = model_df["Band"].astype(str)
            band_is_3 = band_str.str.contains(r"\b3\b|Band\s*3", case=False, regex=True) | (band_str == "3")
            service_is_a = model_df["Service"].astype(str).str.strip().str.lower().isin(["service a", "service_a", "a"])
            model_df["Service A & Band 3"] = service_is_a & band_is_3

    metadata = {
        "status": "SUCCESS",
        "joined_rows": len(model_df),
        "joined_columns": len(model_df.columns),
        "joins_applied": joins_applied,
        "join_reports": join_reports
    }

    return model_df, metadata
