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
    - Left joins to preserve all primary records (2,539 rows)
    - Deduplication of reference tables on join key if needed
    - Verified canonical mapping (Users.Operational Area -> Service, Users.Band -> Band)
    - Safe collision handling preventing placeholder primary columns from shadowing reference data
    - Error-safe, uncapped Availability % calculation
    - Service A & Band 3 conditional flag
    - Complete relationship QA verification summary
    """
    if primary_df is None or len(primary_df) == 0:
        return primary_df, {"status": "EMPTY", "joined_rows": 0, "joins_applied": 0, "relationship_qa": {}}

    model_df = primary_df.copy(deep=True)
    # Strip unnamed columns from Excel exports
    model_df = model_df.loc[:, ~model_df.columns.astype(str).str.contains("^Unnamed", na=False)]

    joins_applied = 0
    join_reports = []
    unmatched_keys_count = 0
    ref_duplicates_count = 0

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

        # Check duplicate keys in reference table
        if right_df[right_key].duplicated().any():
            ref_duplicates_count += int(right_df[right_key].duplicated().sum())
            right_df = right_df.drop_duplicates(subset=[right_key], keep="first")

        # Protect verified reference fields (e.g. Band, Operational Area, FTE, Start Date)
        # If primary contains unverified/placeholder Service or Band columns, rename them to avoid collision
        for ref_col in right_df.columns:
            if ref_col == right_key:
                continue
            if ref_col in model_df.columns:
                # Rename primary column so reference column takes canonical role
                model_df = model_df.rename(columns={ref_col: f"{ref_col}_primary"})
            if ref_col == "Operational Area" and "Service" in model_df.columns:
                model_df = model_df.rename(columns={"Service": "Service_primary"})

        # Prepare right columns
        cols_to_use = [right_key] + [c for c in right_df.columns if c != right_key]
        sub_right = right_df[cols_to_use].copy()

        # Ensure string type for reliable key matching
        model_df[left_key] = model_df[left_key].astype(str).str.strip()
        sub_right[right_key] = sub_right[right_key].astype(str).str.strip()

        # Execute join
        model_df = pd.merge(model_df, sub_right, left_on=left_key, right_on=right_key, how=join_type)

        # Drop redundant right_key if names differed
        if left_key != right_key and right_key in model_df.columns:
            model_df = model_df.drop(columns=[right_key])

        # Track unmatched rows
        if "Operational Area" in model_df.columns:
            unmatched = int(model_df["Operational Area"].isnull().sum())
            unmatched_keys_count = max(unmatched_keys_count, unmatched)

        joins_applied += 1
        join_reports.append({
            "right_dataset": right_ds_info.get("name", right_ds_id),
            "left_key": left_key,
            "right_key": right_key,
            "join_type": join_type
        })

    # Canonical Field Mapping
    # Operational Area from Users -> Service
    if "Operational Area" in model_df.columns:
        model_df["Service"] = model_df["Operational Area"]
    elif "Service" not in model_df.columns and "Service_primary" in model_df.columns:
        model_df["Service"] = model_df["Service_primary"]

    # Band from Users -> Band
    if "Band" not in model_df.columns and "Band_primary" in model_df.columns:
        model_df["Band"] = model_df["Band_primary"]

    # Standardize Start Date if present
    if "Start Date (UK Format)" in model_df.columns and "Start Date" not in model_df.columns:
        model_df["Start Date"] = model_df["Start Date (UK Format)"]
    elif "Start Date (US Format)" in model_df.columns and "Start Date" not in model_df.columns:
        model_df["Start Date"] = model_df["Start Date (US Format)"]

    if compute_derived:
        # 1. Uncapped Availability % = Available Hours / Contracted Hours
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
            
            # Error-safe: null/blank for zero denominator, missing numerator or denominator
            valid_mask = denom.notnull() & (denom != 0) & num.notnull()
            calculated_avail = np.where(valid_mask, num / denom, np.nan)
            
            # Use canonical 'Availability %' column
            model_df["Availability %"] = calculated_avail
            if "Availabilty %" in model_df.columns:
                model_df = model_df.drop(columns=["Availabilty %"])

        # 2. Service A & Band 3 Conditional Logic (Q3)
        if "Service" in model_df.columns and "Band" in model_df.columns:
            band_str = model_df["Band"].astype(str)
            band_is_3 = band_str.str.contains(r"\b3\b|Band\s*3", case=False, regex=True) | (band_str == "3")
            service_is_a = model_df["Service"].astype(str).str.strip().str.lower().isin(["service a", "service_a", "a"])
            model_df["Service A & Band 3"] = service_is_a & band_is_3

    # Calculate Relationship QA Summary Metrics
    total_rows = len(model_df)
    missing_service = int(model_df["Service"].isnull().sum()) if "Service" in model_df.columns else total_rows
    missing_band = int(model_df["Band"].isnull().sum()) if "Band" in model_df.columns else total_rows
    user_match_pct = float((total_rows - unmatched_keys_count) / total_rows * 100.0) if total_rows > 0 else 0.0

    qa_summary = {
        "analytical_rows": total_rows,
        "user_match_coverage_pct": user_match_pct,
        "unmatched_users": unmatched_keys_count,
        "duplicate_master_keys": ref_duplicates_count,
        "missing_service_after_join": missing_service,
        "missing_band_after_join": missing_band,
        "is_verified": (user_match_pct == 100.0 and missing_service == 0 and missing_band == 0)
    }

    metadata = {
        "status": "SUCCESS",
        "joined_rows": total_rows,
        "joined_columns": len(model_df.columns),
        "joins_applied": joins_applied,
        "join_reports": join_reports,
        "relationship_qa": qa_summary
    }

    return model_df, metadata
