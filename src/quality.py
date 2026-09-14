"""Data Quality Engine for Performance Insight Explorer.
Executes two-stage quality assurance:
Stage A — Automatic Structural QA (Completeness, Uniqueness, Format, Outliers, Constants)
Stage B — Semantic QA (Record IDs, Denominator zeros, Target validity, Backlog reconciliation)
"""
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


def run_structural_qa(df: pd.DataFrame) -> Dict[str, Any]:
    """Stage A — Automatic Structural QA immediately after upload (No semantic mappings required)."""
    issues: List[Dict[str, Any]] = []
    issue_counter = 1
    row_count = len(df)
    
    if row_count == 0:
        return {
            "stage": "Structural QA",
            "issues": [{
                "issue_id": "SQA-001",
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
        
    total_cells = df.size
    total_nulls = int(df.isna().sum().sum())
    overall_missing_pct = round((total_nulls / total_cells * 100.0) if total_cells > 0 else 0.0, 2)
    
    # 1. Missingness
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            null_pct = round(null_count / row_count * 100.0, 2)
            sev = Severity.CRITICAL if null_pct > 30.0 else (Severity.WARNING if null_pct > 5.0 else Severity.INFO)
            issues.append({
                "issue_id": f"SQA-{issue_counter:03d}",
                "dimension": "Completeness",
                "severity": sev,
                "title": f"Missing Values in '{col}'",
                "description": f"Field '{col}' has {null_count:,} missing observations ({null_pct}%).",
                "field": col,
                "affected_count": null_count,
                "affected_pct": null_pct,
                "sample_indices": df[df[col].isna()].index.tolist()[:10],
                "sample_values": ["<NULL>"],
                "recommended_action": "Check whether missingness is systematic; do not silently impute.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # 2. Duplicate Rows
    dup_rows_mask = df.duplicated(keep="first")
    dup_row_count = int(dup_rows_mask.sum())
    if dup_row_count > 0:
        dup_pct = round(dup_row_count / row_count * 100.0, 2)
        issues.append({
            "issue_id": f"SQA-{issue_counter:03d}",
            "dimension": "Uniqueness",
            "severity": Severity.CRITICAL if dup_pct > 5.0 else Severity.WARNING,
            "title": "Duplicate Rows Detected",
            "description": f"Detected {dup_row_count:,} exact duplicate rows ({dup_pct}% of total records).",
            "field": "ALL_COLUMNS",
            "affected_count": dup_row_count,
            "affected_pct": dup_pct,
            "sample_indices": df[dup_rows_mask].index.tolist()[:10],
            "sample_values": ["Entire row duplicate"],
            "recommended_action": "Investigate source extract logic for double-counting; verify before aggregating.",
            "status": QualityStatus.UNRESOLVED
        })
        issue_counter += 1
        
    # 3. Invalid Dates & Unparsed Timestamps
    for col in df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        col_lower = col.lower()
        if any(k in col_lower for k in ["date", "month", "timestamp", "period"]):
            if not pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_datetime64_any_dtype(series):
                parsed = pd.to_datetime(series.astype(str).str.strip(), errors="coerce")
                invalid_mask = parsed.isna()
                invalid_count = int(invalid_mask.sum())
                if invalid_count > 0:
                    invalid_pct = round(invalid_count / len(series) * 100.0, 2)
                    issues.append({
                        "issue_id": f"SQA-{issue_counter:03d}",
                        "dimension": "Validity",
                        "severity": Severity.CRITICAL if invalid_pct > 5.0 else Severity.WARNING,
                        "title": f"Invalid Date Formats in '{col}'",
                        "description": f"Found {invalid_count:,} values ({invalid_pct}%) that could not be parsed as valid dates.",
                        "field": col,
                        "affected_count": invalid_count,
                        "affected_pct": invalid_pct,
                        "sample_indices": series[invalid_mask].index.tolist()[:10],
                        "sample_values": series[invalid_mask].head(5).astype(str).tolist(),
                        "recommended_action": "Review date strings (e.g. 'UNKNOWN', invalid days); format errors will cause time-series gaps.",
                        "status": QualityStatus.UNRESOLVED
                    })
                    issue_counter += 1
                    
    # 4. Negative Values in Numeric Columns
    for col in df.select_dtypes(include=['number']).columns:
        neg_mask = (df[col] < 0)
        neg_count = int(neg_mask.sum())
        if neg_count > 0:
            neg_pct = round(neg_count / row_count * 100.0, 2)
            issues.append({
                "issue_id": f"SQA-{issue_counter:03d}",
                "dimension": "Validity",
                "severity": Severity.WARNING,
                "title": f"Negative Values in '{col}'",
                "description": f"Field '{col}' contains {neg_count:,} negative observations ({neg_pct}%).",
                "field": col,
                "affected_count": neg_count,
                "affected_pct": neg_pct,
                "sample_indices": df[neg_mask].index.tolist()[:10],
                "sample_values": df[col][neg_mask].head(5).astype(str).tolist(),
                "recommended_action": "Verify if negative values represent cancellations/adjustments or data entry errors.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # 5. Category Whitespace / Case Inconsistency
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
            vals = df[col].dropna().astype(str)
            raw_uniques = list(vals.unique())
            cleaned_map = {}
            for v in raw_uniques:
                norm = v.strip().lower()
                cleaned_map.setdefault(norm, []).append(v)
            inconsistent_groups = [variants for variants in cleaned_map.values() if len(variants) > 1]
            if inconsistent_groups:
                diff_count = sum(len(g) - 1 for g in inconsistent_groups)
                # Find affected row indices where non-standard/lowercase occurs
                all_variants = [item for sublist in inconsistent_groups for item in sublist]
                affected_indices = df[df[col].astype(str).isin(all_variants)].index.tolist()
                issues.append({
                    "issue_id": f"SQA-{issue_counter:03d}",
                    "dimension": "Consistency",
                    "severity": Severity.WARNING,
                    "title": f"Category Case / Whitespace Inconsistency in '{col}'",
                    "description": f"Field '{col}' contains case/spacing discrepancies across categories: {inconsistent_groups}.",
                    "field": col,
                    "affected_count": len(all_variants),
                    "affected_pct": round(len(all_variants) / row_count * 100.0, 1),
                    "sample_indices": affected_indices[:10],
                    "sample_values": [f"Variants: {g}" for g in inconsistent_groups[:5]],
                    "recommended_action": "Apply standard text normalization (e.g. Title Case or standard lookup mapping).",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
                
    # 6. Statistical Outliers (Robust IQR Method: Q1 - 3*IQR, Q3 + 3*IQR)
    for col in df.select_dtypes(include=['number']).columns:
        s = df[col].dropna()
        if len(s) >= 4:
            q1 = float(s.quantile(0.25))
            q3 = float(s.quantile(0.75))
            iqr = q3 - q1
            if iqr > 0:
                lower_bound = q1 - 3.0 * iqr
                upper_bound = q3 + 3.0 * iqr
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_count = int(outlier_mask.sum())
                if outlier_count > 0:
                    outlier_indices = df[outlier_mask].index.tolist()
                    outlier_vals = df[col][outlier_mask].tolist()
                    issues.append({
                        "issue_id": f"SQA-{issue_counter:03d}",
                        "dimension": "Plausibility",
                        "severity": Severity.WARNING,
                        "title": f"Potential Statistical Outlier in '{col}'",
                        "description": "Potential statistical outlier — analyst review required.",
                        "field": col,
                        "affected_count": outlier_count,
                        "affected_pct": round(outlier_count / row_count * 100.0, 2),
                        "sample_indices": outlier_indices[:10],
                        "sample_values": [f"Row {idx}: {val}" for idx, val in zip(outlier_indices[:10], outlier_vals[:10])],
                        "method_used": "Robust IQR (Q1 - 3.0*IQR, Q3 + 3.0*IQR)",
                        "threshold": f"Lower: {lower_bound:.2f}, Upper: {upper_bound:.2f}",
                        "recommended_action": "Potential statistical outlier — analyst review required. Do not automatically delete or alter; verify if genuine operational event.",
                        "status": QualityStatus.UNRESOLVED
                    })
                    issue_counter += 1

    # 7. Constant / Zero-Variance Columns
    for col in df.columns:
        uniq = df[col].nunique(dropna=True)
        if uniq <= 1 and row_count > 1:
            issues.append({
                "issue_id": f"SQA-{issue_counter:03d}",
                "dimension": "Plausibility",
                "severity": Severity.INFO,
                "title": f"Constant Field '{col}'",
                "description": f"Field '{col}' has {uniq} unique value across all records (zero variance).",
                "field": col,
                "affected_count": row_count,
                "affected_pct": 100.0,
                "sample_indices": [0],
                "sample_values": [str(df[col].iloc[0]) if len(df) > 0 else "None"],
                "recommended_action": "Constant columns provide no variance for segmentation; consider excluding from drivers.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    crit_count = sum(1 for i in issues if i["severity"] == Severity.CRITICAL)
    warn_count = sum(1 for i in issues if i["severity"] == Severity.WARNING)
    info_count = sum(1 for i in issues if i["severity"] == Severity.INFO)
    
    health_score = max(0.0, 100.0 - (crit_count * 15.0) - (warn_count * 4.0) - (info_count * 1.0))
    
    return {
        "stage": "Structural QA",
        "issues": issues,
        "critical_count": crit_count,
        "warning_count": warn_count,
        "info_count": info_count,
        "total_issues": len(issues),
        "health_score": round(health_score, 1),
        "overall_missing_pct": overall_missing_pct
    }


def run_semantic_qa(df: pd.DataFrame, confirmed_mappings: Dict[str, str]) -> Dict[str, Any]:
    """Stage B — Semantic QA after confirmed mappings (Business logic & relational integrity)."""
    issues: List[Dict[str, Any]] = []
    issue_counter = 1
    row_count = len(df)
    
    if not confirmed_mappings:
        return {
            "stage": "Semantic QA",
            "issues": [],
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "total_issues": 0,
            "health_score": 100.0,
            "status": "Pending Confirmed Mappings"
        }
        
    role_to_col = {}
    for c, r in confirmed_mappings.items():
        r_str = r.get("suggested_role") if isinstance(r, dict) else (str(r) if r else None)
        if r_str and c in df.columns:
            role_to_col[r_str] = c
            
    # 1. Duplicate Record IDs
    if "record_id" in role_to_col:
        id_col = role_to_col["record_id"]
        dup_id_mask = df[id_col].duplicated(keep=False) & df[id_col].notna()
        dup_id_count = int(dup_id_mask.sum())
        if dup_id_count > 0:
            dup_id_pct = round(dup_id_count / row_count * 100.0, 2)
            issues.append({
                "issue_id": f"SEM-{issue_counter:03d}",
                "dimension": "Semantic Integrity",
                "severity": Severity.CRITICAL,
                "title": f"Duplicate Record IDs in '{id_col}'",
                "description": f"Mapped record ID '{id_col}' contains {dup_id_count:,} duplicate instances ({dup_id_pct}%).",
                "field": id_col,
                "affected_count": dup_id_count,
                "affected_pct": dup_id_pct,
                "sample_indices": df[dup_id_mask].index.tolist()[:10],
                "sample_values": df[id_col][dup_id_mask].head(5).astype(str).tolist(),
                "recommended_action": "Check row granularity; ensure multi-event cases are aggregated before rate calculations.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # 2. Mapped Denominator Zero Risks
    for den_role in ["target", "fte", "staff", "hours_available"]:
        if den_role in role_to_col:
            d_col = role_to_col[den_role]
            s_num = pd.to_numeric(df[d_col], errors="coerce")
            zero_mask = (s_num == 0)
            zero_count = int(zero_mask.sum())
            if zero_count > 0:
                zero_pct = round(zero_count / row_count * 100.0, 2)
                issues.append({
                    "issue_id": f"SEM-{issue_counter:03d}",
                    "dimension": "Calculation Safety",
                    "severity": Severity.WARNING,
                    "title": f"Zero Values in Mapped Denominator '{d_col}' ({den_role})",
                    "description": f"Mapped denominator '{d_col}' contains {zero_count:,} zeros ({zero_pct}%). KPI engine will safely return NaN.",
                    "field": d_col,
                    "affected_count": zero_count,
                    "affected_pct": zero_pct,
                    "sample_indices": df[zero_mask].index.tolist()[:10],
                    "sample_values": ["0"],
                    "recommended_action": "Ensure zero-capacity periods are documented in assumptions.",
                    "status": QualityStatus.UNRESOLVED
                })
                issue_counter += 1
                
    # 3. Backlog Inventory Reconciliation Gap
    if "opening_backlog" in role_to_col and "closing_backlog" in role_to_col and "received" in role_to_col and ("completed" in role_to_col or "actual" in role_to_col):
        o_col = role_to_col["opening_backlog"]
        c_col = role_to_col["closing_backlog"]
        r_col = role_to_col["received"]
        comp_col = role_to_col.get("completed") or role_to_col.get("actual")
        
        s_open = pd.to_numeric(df[o_col], errors="coerce")
        s_close = pd.to_numeric(df[c_col], errors="coerce")
        s_rec = pd.to_numeric(df[r_col], errors="coerce")
        s_comp = pd.to_numeric(df[comp_col], errors="coerce")
        
        expected_close = s_open + s_rec - s_comp
        gap = s_close - expected_close
        gap_mask = (gap.abs() > 0.01) & gap.notna()
        gap_count = int(gap_mask.sum())
        
        if gap_count > 0:
            gap_pct = round(gap_count / row_count * 100.0, 2)
            tot_gap = float(gap.abs().sum())
            issues.append({
                "issue_id": f"SEM-{issue_counter:03d}",
                "dimension": "Business Rule Integrity",
                "severity": Severity.WARNING if gap_pct < 10.0 else Severity.CRITICAL,
                "title": "Backlog Flow Reconciliation Discrepancy",
                "description": f"Found {gap_count:,} periods ({gap_pct}%) where Closing Backlog != Opening + Received - Completed (Total gap: {tot_gap:,.1f} cases).",
                "field": f"{c_col} vs Expected",
                "affected_count": gap_count,
                "affected_pct": gap_pct,
                "sample_indices": df[gap_mask].index.tolist()[:10],
                "sample_values": [f"Gap: {g:+,.1f}" for g in gap[gap_mask].head(5).tolist()],
                "recommended_action": "Investigate unrecorded transfers, adjustments, or reporting boundary lags.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    # 4. Hours Worked Exceeds Hours Scheduled
    if "hours_used" in role_to_col and "hours_available" in role_to_col:
        hu_col = role_to_col["hours_used"]
        ha_col = role_to_col["hours_available"]
        s_hu = pd.to_numeric(df[hu_col], errors="coerce")
        s_ha = pd.to_numeric(df[ha_col], errors="coerce")
        over_mask = (s_hu > s_ha * 1.5) & s_hu.notna() & s_ha.notna()
        over_count = int(over_mask.sum())
        if over_count > 0:
            over_pct = round(over_count / row_count * 100.0, 2)
            issues.append({
                "issue_id": f"SEM-{issue_counter:03d}",
                "dimension": "Plausibility",
                "severity": Severity.WARNING,
                "title": f"Excessive Hours Worked in '{hu_col}' vs '{ha_col}'",
                "description": f"Found {over_count:,} observations ({over_pct}%) where worked hours exceed scheduled capacity by >50% (potential unrecorded overtime).",
                "field": hu_col,
                "affected_count": over_count,
                "affected_pct": over_pct,
                "sample_indices": df[over_mask].index.tolist()[:10],
                "sample_values": df[hu_col][over_mask].head(5).astype(str).tolist(),
                "recommended_action": "Confirm whether overtime capacity is included in baseline hours available.",
                "status": QualityStatus.UNRESOLVED
            })
            issue_counter += 1
            
    crit_count = sum(1 for i in issues if i["severity"] == Severity.CRITICAL)
    warn_count = sum(1 for i in issues if i["severity"] == Severity.WARNING)
    info_count = sum(1 for i in issues if i["severity"] == Severity.INFO)
    
    health_score = max(0.0, 100.0 - (crit_count * 15.0) - (warn_count * 4.0) - (info_count * 1.0))
    
    return {
        "stage": "Semantic QA",
        "issues": issues,
        "critical_count": crit_count,
        "warning_count": warn_count,
        "info_count": info_count,
        "total_issues": len(issues),
        "health_score": round(health_score, 1),
        "status": "Completed"
    }


def run_quality_audit(
    df: pd.DataFrame,
    mappings: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Execute complete two-stage quality audit combining Structural and Semantic QA."""
    struct_res = run_structural_qa(df)
    sem_res = run_semantic_qa(df, mappings or {})
    
    combined_issues = struct_res["issues"] + sem_res["issues"]
    crit_count = struct_res["critical_count"] + sem_res["critical_count"]
    warn_count = struct_res["warning_count"] + sem_res["warning_count"]
    info_count = struct_res["info_count"] + sem_res["info_count"]
    
    combined_health = max(0.0, 100.0 - (crit_count * 12.0) - (warn_count * 3.5) - (info_count * 1.0))
    
    return {
        "structural": struct_res,
        "semantic": sem_res,
        "issues": combined_issues,
        "critical_count": crit_count,
        "warning_count": warn_count,
        "info_count": info_count,
        "total_issues": len(combined_issues),
        "health_score": round(combined_health, 1),
        "overall_missing_pct": struct_res["overall_missing_pct"]
    }


def evaluate_data_fitness(
    qa_report: Dict[str, Any],
    row_granularity: Any = "Periodic snapshot",
    confirmed_mappings: Optional[Dict[str, str]] = None,
    assessment_question: str = ""
) -> Dict[str, Any]:
    """Perform contextual Data Fitness Assessment based on QA results, row unit, and mappings."""
    qa_rep = qa_report or {}
    crit_count = qa_rep.get("critical_count", 0)
    warn_count = qa_rep.get("warning_count", 0)
    score = qa_rep.get("health_score", 100.0)
    issues = qa_rep.get("issues", [])
    mappings = confirmed_mappings or {}

    # Guard if a DataFrame is mistakenly passed as row_granularity
    gran_str = "Periodic snapshot"
    if isinstance(row_granularity, str) and row_granularity.strip():
        gran_str = row_granularity.strip()

    reasons = []
    caveats = []
    critical_blockers = []

    if crit_count > 0:
        for iss in issues:
            if iss.get("severity") == Severity.CRITICAL:
                msg = f"Critical Blocker: {iss.get('title', 'Unknown')} ({iss.get('description', '')})"
                critical_blockers.append(msg)
                reasons.append(msg)

    if warn_count > 0:
        for iss in issues:
            if iss.get("severity") == Severity.WARNING:
                caveats.append(f"{iss.get('title', 'Warning')}: {iss.get('description', '')}")

    if gran_str:
        caveats.append(f"Row Unit Governance: Record granularity confirmed as '{gran_str}'. Aggregations respect this unit.")

    if crit_count > 0:
        status = "Insufficient for requested analysis"
        summary = "Dataset has critical structural blockers that prevent reliable quantitative analysis until resolved."
    elif warn_count > 0 or len(caveats) > 0:
        status = "Fit for purpose with caveats"
        summary = f"Dataset is suitable for indicative operational analysis (Health Score: {score:.1f}/100) subject to documented caveats and mathematical safeguards."
    else:
        status = "Fit for purpose"
        summary = f"Dataset meets high data quality and structural standards (Health Score: {score:.1f}/100) with no identified blockers."

    return {
        "status": status,
        "fitness_status": status,
        "health_score": score,
        "summary": summary,
        "reasons": reasons if reasons else ["No fatal structural corruption detected across loaded fields."],
        "caveats": caveats if caveats else ["Standard operational assumptions apply."],
        "critical_blockers": critical_blockers,
        "assessment_question": assessment_question
    }

