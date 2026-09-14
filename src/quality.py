"""Data Quality Engine for Performance Insight Explorer.
Executes multi-dimensional quality audits: Completeness, Uniqueness, Validity, Consistency, Integrity, Plausibility.
Severity classification: Critical, Warning, Information. Status tracking: Unresolved, Reviewed, Accepted.
"""
import re
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class Severity:
    CRITICAL = "Critical"
    WARNING = "Warning"
    INFO = "Information"


class QualityStatus:
    UNRESOLVED = "Unresolved"
    REVIEWED = "Reviewed"
    ACCEPTED = "Accepted"


def run_quality_audit(
    df: pd.DataFrame,
    mappings: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Execute thorough, transparent data quality scan across all dimensions."""
    issues: List[Dict[str, Any]] = []
    issue_counter = 1
    row_count = len(df)
    
    if row_count == 0:
        return {
            "issues": [{
                "issue_id": "QA-001",
                "dimension": "Completeness",
                "severity": Severity.CRITICAL,
                "title": "Empty Dataset",
                "description": "The loaded dataset contains zero rows.",
                "field": "ALL",
                "affected_count": 0,
                "affected_pct": 100.0,
                "sample_indices": [],
                "sample_values": [],
                "recommended_action": "Verify file export or worksheet selection.",
                "status": QualityStatus.UNRESOLVED
            }],
            "critical_count": 1,
            "warning_count": 0,
            "info_count": 0,
            "total_issues": 1,
            "health_score": 0.0,
            "overall_missing_pct": 100.0
        }
        
    role_to_col = {}
    if mappings:
        for c, r in mappings.items():
            if r and c in df.columns:
                role_to_col[r] = c
                
    # ---------------- 1. COMPLETENESS ----------------
    total_cells = df.size
    total_nulls = int(df.isna().sum().sum())
    overall_missing_pct = round((total_nulls / total_cells * 100.0) if total_cells > 0 else 0.0, 2)
    
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            null_pct = round(null_count / row_count * 100.0, 2)
            is_mapped_key = (col in mappings and mappings.get(col) in ["record_id", "date", "actual", "target", "completed", "received", "team"]) if mappings else False
            
            if is_mapped_key and null_pct > 10.0:
                sev = Severity.CRITICAL
            elif null_pct > 30.0:
                sev = Severity.CRITICAL
            elif null_pct > 5.0:
                sev = Severity.WARNING
            else:
                sev = Severity.INFO
                
            null_indices = df[df[col].isna()].index.tolist()[:10]
            
            issues.append({
                "issue_id": f"QA-{issue_counter:03d}",
                "dimension": "Completeness",
                "severity": sev,
                "title": f"Missing Values in '{col}'",
                "description": f"Field '{col}' has {null_count:,} missing observations ({null_pct}%).",
                "field": col,
                "affected_count": null_count,
                "affected_pct": null_pct,
                "sample_indices": null_indices,
                "sample_values": ["<NULL>"],
                "recommended_action": "Check if missingness is concentrated in specific periods or groups; do not silently impute.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # ---------------- 2. UNIQUENESS ----------------
    dup_rows_mask = df.duplicated(keep="first")
    dup_row_count = int(dup_rows_mask.sum())
    if dup_row_count > 0:
        dup_pct = round(dup_row_count / row_count * 100.0, 2)
        dup_indices = df[dup_rows_mask].index.tolist()[:10]
        issues.append({
            "issue_id": f"QA-{issue_counter:03d}",
            "dimension": "Uniqueness",
            "severity": Severity.CRITICAL if dup_pct > 5.0 else Severity.WARNING,
            "title": "Duplicate Rows Detected",
            "description": f"Detected {dup_row_count:,} exact duplicate rows ({dup_pct}% of total records).",
            "field": "ALL_COLUMNS",
            "affected_count": dup_row_count,
            "affected_pct": dup_pct,
            "sample_indices": dup_indices,
            "sample_values": ["Entire row duplicate"],
            "recommended_action": "Investigate source extract logic for double-counting; verify before aggregating.",
            "status": QualityStatus.UNRESOLVED
        })
        issue_counter += 1
        
    if "record_id" in role_to_col:
        id_col = role_to_col["record_id"]
        dup_id_mask = df[id_col].duplicated(keep=False) & df[id_col].notna()
        dup_id_count = int(dup_id_mask.sum())
        if dup_id_count > 0:
            dup_id_pct = round(dup_id_count / row_count * 100.0, 2)
            dup_id_samples = df[dup_id_mask][id_col].head(5).astype(str).tolist()
            issues.append({
                "issue_id": f"QA-{issue_counter:03d}",
                "dimension": "Uniqueness",
                "severity": Severity.CRITICAL,
                "title": f"Duplicate Record IDs in '{id_col}'",
                "description": f"Field '{id_col}' contains {dup_id_count:,} non-unique identifier instances ({dup_id_pct}%).",
                "field": id_col,
                "affected_count": dup_id_count,
                "affected_pct": dup_id_pct,
                "sample_indices": df[dup_id_mask].index.tolist()[:10],
                "sample_values": dup_id_samples,
                "recommended_action": "Check whether dataset is case-level or event/history-level where IDs repeat by stage.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # ---------------- 3. VALIDITY & FORMAT ----------------
    for col in df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
            
        col_lower = col.lower()
        if (mappings and mappings.get(col) in ["date", "reporting_period"]) or any(k in col_lower for k in ["date", "month", "timestamp"]):
            if not pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_datetime64_any_dtype(series):
                parsed = pd.to_datetime(series.astype(str).str.strip(), errors="coerce")
                invalid_mask = parsed.isna()
                invalid_count = int(invalid_mask.sum())
                if invalid_count > 0:
                    invalid_pct = round(invalid_count / len(series) * 100.0, 2)
                    bad_samples = series[invalid_mask].head(5).astype(str).tolist()
                    issues.append({
                        "issue_id": f"QA-{issue_counter:03d}",
                        "dimension": "Validity",
                        "severity": Severity.CRITICAL if invalid_pct > 5.0 else Severity.WARNING,
                        "title": f"Invalid Date Values in '{col}'",
                        "description": f"Found {invalid_count:,} values ({invalid_pct}%) that could not be parsed as valid dates.",
                        "field": col,
                        "affected_count": invalid_count,
                        "affected_pct": invalid_pct,
                        "sample_indices": series[invalid_mask].index.tolist()[:10],
                        "sample_values": bad_samples,
                        "recommended_action": "Review date strings (e.g. '2025-02-31', 'UNKNOWN'); format errors will cause time-series gaps.",
                        "status": QualityStatus.UNRESOLVED
                    })
                    issue_counter += 1
                    
        is_capacity_or_vol = False
        if mappings and mappings.get(col) in ["received", "completed", "opening_backlog", "closing_backlog", "staff", "fte", "hours_available", "hours_used", "actual", "target", "processing_time"]:
            is_capacity_or_vol = True
        elif any(k in col_lower for k in ["cases", "fte", "staff", "hours", "count", "received", "completed", "backlog", "days", "turnaround"]):
            is_capacity_or_vol = True
            
        if is_capacity_or_vol:
            s_num = pd.to_numeric(series, errors="coerce")
            neg_mask = (s_num < 0)
            neg_count = int(neg_mask.sum())
            if neg_count > 0:
                neg_pct = round(neg_count / len(series) * 100.0, 2)
                neg_samples = s_num[neg_mask].head(5).astype(str).tolist()
                issues.append({
                    "issue_id": f"QA-{issue_counter:03d}",
                    "dimension": "Validity",
                    "severity": Severity.CRITICAL if mappings and mappings.get(col) else Severity.WARNING,
                    "title": f"Negative Values in Volume/Capacity Field '{col}'",
                    "description": f"Field '{col}' contains {neg_count:,} negative observations ({neg_pct}%). Negative volumes/capacities are invalid.",
                    "field": col,
                    "affected_count": neg_count,
                    "affected_pct": neg_pct,
                    "sample_indices": s_num[neg_mask].index.tolist()[:10],
                    "sample_values": neg_samples,
                    "recommended_action": "Check if negative values represent adjustments/cancellations rather than genuine operational volume.",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
                
        is_denominator = False
        if mappings and mappings.get(col) in ["target", "fte", "staff", "hours_available"]:
            is_denominator = True
        elif any(k in col_lower for k in ["target", "available_hours", "staff_fte", "target_output"]):
            is_denominator = True
            
        if is_denominator:
            s_num = pd.to_numeric(series, errors="coerce")
            zero_mask = (s_num == 0)
            zero_count = int(zero_mask.sum())
            if zero_count > 0:
                zero_pct = round(zero_count / len(series) * 100.0, 2)
                issues.append({
                    "issue_id": f"QA-{issue_counter:03d}",
                    "dimension": "Validity",
                    "severity": Severity.WARNING,
                    "title": f"Zero Values in Potential Denominator '{col}'",
                    "description": f"Field '{col}' has {zero_count:,} zero observations ({zero_pct}%). Division by zero will be safely guarded by setting resulting KPI to NaN.",
                    "field": col,
                    "affected_count": zero_count,
                    "affected_pct": zero_pct,
                    "sample_indices": s_num[zero_mask].index.tolist()[:10],
                    "sample_values": ["0"],
                    "recommended_action": "Zero denominators are protected in the KPI engine; ensure reporting captures genuine inactive periods.",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
                
    # ---------------- 4. CONSISTENCY ----------------
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
            vals = df[col].dropna().astype(str)
            raw_uniques = set(vals.unique())
            cleaned_uniques = set(vals.str.strip().str.lower().unique())
            if len(raw_uniques) > len(cleaned_uniques):
                diff_count = len(raw_uniques) - len(cleaned_uniques)
                issues.append({
                    "issue_id": f"QA-{issue_counter:03d}",
                    "dimension": "Consistency",
                    "severity": Severity.WARNING,
                    "title": f"Case / Whitespace Inconsistency in '{col}'",
                    "description": f"Field '{col}' contains {diff_count} redundant category variants caused by case differences or trailing spaces (e.g. 'Team Alpha' vs 'team alpha').",
                    "field": col,
                    "affected_count": len(raw_uniques),
                    "affected_pct": round(diff_count / max(1, len(raw_uniques)) * 100.0, 1),
                    "sample_indices": [],
                    "sample_values": list(raw_uniques)[:6],
                    "recommended_action": "Group comparisons will normalize casing for display; recommend cleaning upstream master data.",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
                
    # ---------------- 5. PLAUSIBILITY & DISTRIBUTION ----------------
    for col in df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
            
        if series.nunique() <= 1:
            issues.append({
                "issue_id": f"QA-{issue_counter:03d}",
                "dimension": "Plausibility",
                "severity": Severity.INFO,
                "title": f"Constant Column '{col}'",
                "description": f"Field '{col}' has only 1 unique value across all records: '{series.iloc[0]}'.",
                "field": col,
                "affected_count": len(series),
                "affected_pct": 100.0,
                "sample_indices": [],
                "sample_values": [str(series.iloc[0])],
                "recommended_action": "Constant columns provide no variance for statistical comparisons or trend modeling.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
        if pd.api.types.is_numeric_dtype(series) and len(series) >= 10:
            s_num = series.astype(float)
            q25 = s_num.quantile(0.25)
            q75 = s_num.quantile(0.75)
            iqr = q75 - q25
            if iqr > 0:
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outlier_mask = (s_num < lower_bound) | (s_num > upper_bound)
                outlier_count = int(outlier_mask.sum())
                if outlier_count > 0:
                    outlier_pct = round(outlier_count / len(series) * 100.0, 2)
                    outlier_samples = s_num[outlier_mask].head(5).tolist()
                    issues.append({
                        "issue_id": f"QA-{issue_counter:03d}",
                        "dimension": "Plausibility",
                        "severity": Severity.WARNING if outlier_pct > 5.0 else Severity.INFO,
                        "title": f"Statistical Outliers in '{col}' (IQR Method)",
                        "description": f"Field '{col}' has {outlier_count} values ({outlier_pct}%) outside standard IQR bounds [{lower_bound:.1f}, {upper_bound:.1f}].",
                        "field": col,
                        "affected_count": outlier_count,
                        "affected_pct": outlier_pct,
                        "sample_indices": s_num[outlier_mask].index.tolist()[:10],
                        "sample_values": [str(round(x, 2)) for x in outlier_samples],
                        "recommended_action": "Review outliers with operational SME. DO NOT delete; use median/IQR robust metrics.",
                        "status": QualityStatus.UNRESOLVED
                    })
                    issue_counter += 1
                    
    # ---------------- 6. INTEGRITY & RECONCILIATION ----------------
    if all(k in role_to_col for k in ["opening_backlog", "closing_backlog", "received", "completed"]):
        open_col = role_to_col["opening_backlog"]
        close_col = role_to_col["closing_backlog"]
        rec_col = role_to_col["received"]
        comp_col = role_to_col["completed"]
        
        try:
            s_open = pd.to_numeric(df[open_col], errors="coerce").fillna(0)
            s_close = pd.to_numeric(df[close_col], errors="coerce").fillna(0)
            s_rec = pd.to_numeric(df[rec_col], errors="coerce").fillna(0)
            s_comp = pd.to_numeric(df[comp_col], errors="coerce").fillna(0)
            
            expected_close = s_open + s_rec - s_comp
            gap = (s_close - expected_close).abs()
            mismatch_mask = (gap > 0.001)
            mismatch_count = int(mismatch_mask.sum())
            if mismatch_count > 0:
                mismatch_pct = round(mismatch_count / row_count * 100.0, 2)
                max_gap = float(gap.max())
                issues.append({
                    "issue_id": f"QA-{issue_counter:03d}",
                    "dimension": "Integrity",
                    "severity": Severity.CRITICAL,
                    "title": "Backlog Inventory Reconciliation Discrepancy",
                    "description": f"Closing backlog does not balance with Opening + Received - Completed in {mismatch_count:,} rows ({mismatch_pct}%). Max gap: {max_gap:,.1f}.",
                    "field": f"{close_col} vs Expected",
                    "affected_count": mismatch_count,
                    "affected_pct": mismatch_pct,
                    "sample_indices": df[mismatch_mask].index.tolist()[:10],
                    "sample_values": [f"Reported: {s_close.iloc[i]}, Expected: {expected_close.iloc[i]}" for i in df[mismatch_mask].index[:3]],
                    "recommended_action": "Investigate unrecorded case transfers, cancellations, or discrepancies between intake and case management systems.",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
        except Exception:
            pass
            
    crit_count = sum(1 for x in issues if x["severity"] == Severity.CRITICAL)
    warn_count = sum(1 for x in issues if x["severity"] == Severity.WARNING)
    info_count = sum(1 for x in issues if x["severity"] == Severity.INFO)
    
    health_deductions = (crit_count * 25.0) + (warn_count * 5.0) + (info_count * 1.0)
    health_score = max(0.0, round(100.0 - health_deductions, 1))
    
    return {
        "issues": issues,
        "critical_count": crit_count,
        "warning_count": warn_count,
        "info_count": info_count,
        "total_issues": len(issues),
        "health_score": health_score,
        "overall_missing_pct": overall_missing_pct
    }
