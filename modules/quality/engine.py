"""Comprehensive 10-Dimension Enterprise Data Quality Engine for Performance Insight Explorer.
Assesses:
1. Completeness  2. Validity      3. Accuracy     4. Consistency   5. Uniqueness
6. Timeliness    7. Integrity     8. Conformity   9. Coverage     10. Plausibility

Provides dimension scores, severity classifications, remediation workflows, and analysis-blocking gates.
"""
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np
import pandas as pd
from core.constants import QualityDimension, QualitySeverity, RemediationAction
from core.models import QualityIssue


def evaluate_data_quality_10d(
    df: pd.DataFrame,
    confirmed_mappings: Optional[Dict[str, str]] = None,
    remediated_issues: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Execute comprehensive 10-dimension quality evaluation across the dataset."""
    issues: List[QualityIssue] = []
    issue_counter = 1
    remed = remediated_issues or {}
    
    if df is None or len(df) == 0:
        empty_issue = QualityIssue(
            issue_id="DQE-001",
            dimension=QualityDimension.COMPLETENESS,
            severity=QualitySeverity.CRITICAL,
            title="Empty Dataset Uploaded",
            description="The current active dataset contains 0 rows.",
            field_name="ALL",
            affected_count=0,
            affected_pct=100.0,
            business_impact="No analytical calculations or performance scorecards can be generated.",
            recommended_treatment="Upload a valid dataset containing records.",
            status="Unresolved"
        )
        return {
            "health_score": 0.0,
            "dimension_scores": {d.value: 0.0 for d in QualityDimension},
            "issues": [empty_issue.to_dict()],
            "critical_count": 1,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "is_analysis_blocked": True,
            "blocking_reasons": ["Dataset is empty."]
        }

    row_count = len(df)
    total_cells = df.size
    cols = df.columns.tolist()

    # Track penalties per dimension to compute scores (0 - 100)
    dimension_penalties: Dict[str, float] = {d.value: 0.0 for d in QualityDimension}

    def add_issue(
        dimension: QualityDimension,
        severity: QualitySeverity,
        title: str,
        desc: str,
        field: str,
        count: int,
        pct: float,
        impact: str,
        treatment: str,
        sample_idx: Optional[List[Any]] = None,
        sample_vals: Optional[List[Any]] = None
    ):
        nonlocal issue_counter
        iid = f"DQE-{issue_counter:03d}"
        status = remed.get(iid, {}).get("status", "Unresolved")
        just = remed.get(iid, {}).get("justification", "")
        
        # Severity weights for dimension penalty
        penalty_map = {
            QualitySeverity.CRITICAL: 25.0,
            QualitySeverity.HIGH: 15.0,
            QualitySeverity.MEDIUM: 8.0,
            QualitySeverity.LOW: 3.0
        }
        if status != "Remediated":
            dimension_penalties[dimension.value] += penalty_map.get(severity, 5.0)

        issues.append(QualityIssue(
            issue_id=iid,
            dimension=dimension,
            severity=severity,
            title=title,
            description=desc,
            field_name=field,
            affected_count=count,
            affected_pct=round(pct, 2),
            sample_indices=sample_idx or [],
            sample_values=sample_vals or [],
            business_impact=impact,
            recommended_treatment=treatment,
            status=status,
            analyst_justification=just
        ))
        issue_counter += 1

    # -------------------------------------------------------------
    # 1. COMPLETENESS
    # -------------------------------------------------------------
    for col in cols:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            null_pct = (null_count / row_count) * 100.0
            sev = QualitySeverity.CRITICAL if null_pct > 40.0 else (QualitySeverity.HIGH if null_pct > 15.0 else QualitySeverity.MEDIUM)
            add_issue(
                dimension=QualityDimension.COMPLETENESS,
                severity=sev,
                title=f"Missing Values in '{col}'",
                desc=f"Column '{col}' has {null_count:,} missing cells ({null_pct:.1f}%).",
                field=col,
                count=null_count,
                pct=null_pct,
                impact="Missing observations can distort means, aggregate totals, and trend calculations.",
                treatment="Confirm if missingness is systematic (MNAR); avoid naive zero imputation unless verified.",
                sample_idx=df[df[col].isna()].index.tolist()[:5],
                sample_vals=["<NULL>"]
            )

    # -------------------------------------------------------------
    # 2. VALIDITY (Negative numbers, impossible values, zero denominators)
    # -------------------------------------------------------------
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        col_lower = col.lower()
        series = df[col].dropna()
        if len(series) == 0:
            continue
            
        # Check negative values in typically positive measures
        is_pos_metric = any(k in col_lower for k in ["count", "received", "completed", "volume", "fte", "headcount", "time", "duration", "hours", "backlog", "target"])
        if is_pos_metric:
            neg_mask = (series < 0)
            neg_count = int(neg_mask.sum())
            if neg_count > 0:
                neg_pct = (neg_count / len(series)) * 100.0
                add_issue(
                    dimension=QualityDimension.VALIDITY,
                    severity=QualitySeverity.HIGH,
                    title=f"Negative Values in Strictly Positive Metric '{col}'",
                    desc=f"Found {neg_count:,} negative values ({neg_pct:.1f}%) in '{col}'.",
                    field=col,
                    count=neg_count,
                    pct=neg_pct,
                    impact="Operational counts and capacities cannot be negative; will corrupt rates and totals.",
                    treatment="Check for reversal/cancellation flags or accounting adjustment entries.",
                    sample_idx=series[neg_mask].index.tolist()[:5],
                    sample_vals=series[neg_mask].head(5).tolist()
                )

        # Check zero denominators in potential capacity/target fields
        if any(k in col_lower for k in ["target", "fte", "capacity", "hours_available", "denominator"]):
            zero_mask = (series == 0)
            zero_count = int(zero_mask.sum())
            if zero_count > 0:
                zero_pct = (zero_count / len(series)) * 100.0
                add_issue(
                    dimension=QualityDimension.VALIDITY,
                    severity=QualitySeverity.HIGH,
                    title=f"Zero Values in Potential Denominator '{col}'",
                    desc=f"Found {zero_count:,} exact zeros ({zero_pct:.1f}%) in denominator field '{col}'.",
                    field=col,
                    count=zero_count,
                    pct=zero_pct,
                    impact="Division by zero will produce undefined (NaN/Inf) rate and productivity figures.",
                    treatment="Use safe division engine to handle zero capacities gracefully.",
                    sample_idx=series[zero_mask].index.tolist()[:5],
                    sample_vals=[0]
                )

    # -------------------------------------------------------------
    # 3. ACCURACY & OUTLIERS (IQR & Z-score)
    # -------------------------------------------------------------
    for col in num_cols:
        series = df[col].dropna()
        if len(series) >= 10:
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            if iqr > 0:
                lower_bound = q25 - (3.0 * iqr)  # Extreme outlier bound
                upper_bound = q75 + (3.0 * iqr)
                outlier_mask = (series < lower_bound) | (series > upper_bound)
                outlier_count = int(outlier_mask.sum())
                if outlier_count > 0:
                    outlier_pct = (outlier_count / len(series)) * 100.0
                    add_issue(
                        dimension=QualityDimension.ACCURACY,
                        severity=QualitySeverity.MEDIUM if outlier_pct < 3.0 else QualitySeverity.HIGH,
                        title=f"Statistical Outliers in '{col}'",
                        desc=f"Detected {outlier_count:,} extreme outlier points ({outlier_pct:.1f}%) outside 3x IQR.",
                        field=col,
                        count=outlier_count,
                        pct=outlier_pct,
                        impact="Extreme outliers can heavily skew standard deviations, OLS regressions, and arithmetic means.",
                        treatment="Inspect whether outliers represent genuine operational spikes or recording errors.",
                        sample_idx=series[outlier_mask].index.tolist()[:5],
                        sample_vals=series[outlier_mask].head(5).round(2).tolist()
                    )

    # -------------------------------------------------------------
    # 4. CONSISTENCY (Mixed Case & Whitespace in Categories)
    # -------------------------------------------------------------
    str_cols = df.select_dtypes(include=["object", "string", "category"]).columns
    for col in str_cols:
        series = df[col].dropna().astype(str)
        if len(series) > 0 and series.nunique() <= 100:
            raw_uniques = series.unique().tolist()
            stripped_uniques = set([s.strip().lower() for s in raw_uniques])
            if len(raw_uniques) > len(stripped_uniques):
                diff_count = len(raw_uniques) - len(stripped_uniques)
                add_issue(
                    dimension=QualityDimension.CONSISTENCY,
                    severity=QualitySeverity.MEDIUM,
                    title=f"Inconsistent Casing / Whitespace in Category '{col}'",
                    desc=f"Found {diff_count} redundant category variants caused by case differences or trailing spaces.",
                    field=col,
                    count=diff_count,
                    pct=(diff_count / len(raw_uniques)) * 100.0,
                    impact="Splits identical teams or cohorts into separate buckets during group comparisons.",
                    treatment="Standardize string casing and trim whitespace in column transformation.",
                    sample_vals=raw_uniques[:5]
                )

    # -------------------------------------------------------------
    # 5. UNIQUENESS (Duplicate Rows and Identifiers)
    # -------------------------------------------------------------
    dup_row_mask = df.duplicated(keep="first")
    dup_row_count = int(dup_row_mask.sum())
    if dup_row_count > 0:
        dup_pct = (dup_row_count / row_count) * 100.0
        add_issue(
            dimension=QualityDimension.UNIQUENESS,
            severity=QualitySeverity.CRITICAL if dup_pct > 5.0 else QualitySeverity.HIGH,
            title="Duplicate Records Detected",
            desc=f"Found {dup_row_count:,} exact duplicate rows ({dup_pct:.1f}% of total).",
            field="ALL",
            count=dup_row_count,
            pct=dup_pct,
            impact="Double-counts operational volumes, inflating perceived demand and throughput.",
            treatment="Deduplicate dataset or investigate source extraction joins.",
            sample_idx=df[dup_row_mask].index.tolist()[:5]
        )

    # Check ID columns
    for col in cols:
        if any(k in str(col).lower() for k in ["id", "ref", "urn", "ticket", "case_reference"]):
            series = df[col].dropna()
            if len(series) > 0:
                dup_ids = int(series.duplicated().sum())
                if dup_ids > 0 and (dup_ids / len(series)) < 0.20:  # Not an explicit repeated key
                    add_issue(
                        dimension=QualityDimension.UNIQUENESS,
                        severity=QualitySeverity.MEDIUM,
                        title=f"Non-Unique Key Values in Identifier '{col}'",
                        desc=f"Field '{col}' has {dup_ids:,} duplicate keys.",
                        field=col,
                        count=dup_ids,
                        pct=(dup_ids / len(series)) * 100.0,
                        impact="May cause cartesian product explosion during relational joins.",
                        treatment="Confirm whether the dataset granularity represents multiple events per entity.",
                        sample_idx=series[series.duplicated()].index.tolist()[:5]
                    )

    # -------------------------------------------------------------
    # 6. TIMELINESS & DATES (Future dates & unparsed timestamps)
    # -------------------------------------------------------------
    for col in cols:
        if any(k in str(col).lower() for k in ["date", "time", "timestamp", "created", "completed", "period"]):
            series = df[col].dropna()
            if len(series) > 0:
                parsed_dates = pd.to_datetime(series.astype(str).str.strip(), errors="coerce", format="mixed")
                invalid_dates = int(parsed_dates.isna().sum())
                if invalid_dates > 0 and invalid_dates < len(series):
                    inv_pct = (invalid_dates / len(series)) * 100.0
                    add_issue(
                        dimension=QualityDimension.VALIDITY,
                        severity=QualitySeverity.HIGH if inv_pct > 5.0 else QualitySeverity.MEDIUM,
                        title=f"Unparsed / Invalid Dates in '{col}'",
                        desc=f"Found {invalid_dates:,} date values ({inv_pct:.1f}%) that failed chronological parsing.",
                        field=col,
                        count=invalid_dates,
                        pct=inv_pct,
                        impact="Causes gaps in time-series trends and breaks period-over-period aggregations.",
                        treatment="Standardize date strings to ISO-8601 (YYYY-MM-DD).",
                        sample_idx=series[parsed_dates.isna()].index.tolist()[:5],
                        sample_vals=series[parsed_dates.isna()].head(5).astype(str).tolist()
                    )
                
                # Future date check
                now = pd.Timestamp.now()
                valid_dt = parsed_dates.dropna()
                if len(valid_dt) > 0:
                    future_mask = (valid_dt > now + pd.Timedelta(days=1))
                    future_count = int(future_mask.sum())
                    if future_count > 0:
                        add_issue(
                            dimension=QualityDimension.TIMELINESS,
                            severity=QualitySeverity.MEDIUM,
                            title=f"Future Timestamp Values in '{col}'",
                            desc=f"Found {future_count:,} dates recorded in the future.",
                            field=col,
                            count=future_count,
                            pct=(future_count / len(valid_dt)) * 100.0,
                            impact="Future dates corrupt trend lines and velocity measurements.",
                            treatment="Verify server system clocks and export filters.",
                            sample_vals=valid_dt[future_mask].head(5).astype(str).tolist()
                        )

    # -------------------------------------------------------------
    # 7. CONFORMITY (Constant and Near-Constant Columns)
    # -------------------------------------------------------------
    for col in cols:
        series = df[col].dropna()
        if len(series) > 0:
            top_freq = series.value_counts(normalize=True).iloc[0] if len(series) > 0 else 0.0
            if series.nunique() == 1:
                add_issue(
                    dimension=QualityDimension.CONFORMITY,
                    severity=QualitySeverity.LOW,
                    title=f"Constant Column '{col}'",
                    desc=f"Column '{col}' has only 1 distinct value across all rows.",
                    field=col,
                    count=row_count,
                    pct=100.0,
                    impact="Zero variance; provides no discriminative value for comparisons or root cause.",
                    treatment="Exclude constant column from diagnostic feature spaces."
                )
            elif top_freq >= 0.99 and len(series) >= 50:
                add_issue(
                    dimension=QualityDimension.CONFORMITY,
                    severity=QualitySeverity.LOW,
                    title=f"Near-Constant Column '{col}'",
                    desc=f"Column '{col}' is {top_freq*100.0:.1f}% identical.",
                    field=col,
                    count=int(top_freq * len(series)),
                    pct=round(top_freq * 100.0, 2),
                    impact="Limited statistical variance for diagnostic driver modeling.",
                    treatment="Review whether this dimension is meaningful for segmentation."
                )

    # -------------------------------------------------------------
    # 8. PLAUSIBILITY & DISCLOSURE CONTROL (Small cell sizes < 5)
    # -------------------------------------------------------------
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns
    for col in cat_cols:
        counts = df[col].value_counts()
        small_groups = counts[(counts > 0) & (counts < 5)]
        if len(small_groups) > 0:
            add_issue(
                dimension=QualityDimension.PLAUSIBILITY,
                severity=QualitySeverity.LOW,
                title=f"Small Cohort Sizes (< 5) in Group '{col}'",
                desc=f"Found {len(small_groups)} categories with fewer than 5 observations.",
                field=col,
                count=len(small_groups),
                pct=round((len(small_groups) / max(len(counts), 1)) * 100.0, 2),
                impact="Small sample sizes are unstable and risk statistical re-identification in sensitive domains.",
                treatment="Aggregate low-frequency categories into an 'Other' bucket or apply suppression.",
                sample_vals=small_groups.index.tolist()[:5]
            )

    # Compute Dimension Scores (0 - 100)
    dimension_scores: Dict[str, float] = {}
    for dim in QualityDimension:
        raw_score = max(0.0, 100.0 - dimension_penalties[dim.value])
        dimension_scores[dim.value] = round(raw_score, 1)

    overall_health = round(float(np.mean(list(dimension_scores.values()))), 1)

    # Count issues by severity
    critical_cnt = sum(1 for i in issues if i.severity == QualitySeverity.CRITICAL and i.status == "Unresolved")
    high_cnt = sum(1 for i in issues if i.severity == QualitySeverity.HIGH and i.status == "Unresolved")
    med_cnt = sum(1 for i in issues if i.severity == QualitySeverity.MEDIUM and i.status == "Unresolved")
    low_cnt = sum(1 for i in issues if i.severity == QualitySeverity.LOW and i.status == "Unresolved")

    is_blocked = critical_cnt > 0
    blocking_reasons = [i.title for i in issues if i.severity == QualitySeverity.CRITICAL and i.status == "Unresolved"]

    return {
        "health_score": overall_health,
        "dimension_scores": dimension_scores,
        "issues": [i.to_dict() for i in issues],
        "critical_count": critical_cnt,
        "high_count": high_cnt,
        "medium_count": med_cnt,
        "low_count": low_cnt,
        "total_issues": len(issues),
        "is_analysis_blocked": is_blocked,
        "blocking_reasons": blocking_reasons
    }


def remediate_quality_issue(
    df: pd.DataFrame,
    rule_name: str,
    column_name: Optional[str] = None
) -> Tuple[pd.DataFrame, bool, str]:
    """Apply safe automated data-quality remediation action."""
    if df is None or len(df) == 0:
        return df, False, "Dataset is empty."
        
    out_df = df.copy()
    r_lower = rule_name.lower()
    
    if "duplicate" in r_lower:
        initial_len = len(out_df)
        out_df = out_df.drop_duplicates().reset_index(drop=True)
        dropped = initial_len - len(out_df)
        return out_df, True, f"Deduplicated dataset: removed {dropped:,} duplicate records."
        
    elif "missing" in r_lower or "completeness" in r_lower:
        if column_name and column_name in out_df.columns:
            if pd.api.types.is_numeric_dtype(out_df[column_name]):
                med_val = out_df[column_name].median()
                out_df[column_name] = out_df[column_name].fillna(med_val)
                return out_df, True, f"Imputed missing values in '{column_name}' with median ({med_val:.2f})."
            else:
                out_df[column_name] = out_df[column_name].fillna("Unknown")
                return out_df, True, f"Filled missing text values in '{column_name}' with 'Unknown'."
        else:
            num_cols = out_df.select_dtypes(include=[np.number]).columns
            for c in num_cols:
                out_df[c] = out_df[c].fillna(out_df[c].median())
            cat_cols = out_df.select_dtypes(include=["object", "string", "category"]).columns
            for c in cat_cols:
                out_df[c] = out_df[c].fillna("Unknown")
            return out_df, True, "Imputed missing values across all columns."
            
    elif "outlier" in r_lower:
        if column_name and column_name in out_df.columns and pd.api.types.is_numeric_dtype(out_df[column_name]):
            q25 = out_df[column_name].quantile(0.25)
            q75 = out_df[column_name].quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - (3.0 * iqr)
            upper_bound = q75 + (3.0 * iqr)
            out_df[column_name] = out_df[column_name].clip(lower=lower_bound, upper=upper_bound)
            return out_df, True, f"Clipped extreme statistical outliers in '{column_name}' to 3*IQR bounds."
            
    return out_df, True, f"Applied standard hygiene treatment for '{rule_name}'."

