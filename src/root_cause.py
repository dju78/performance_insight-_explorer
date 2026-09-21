"""Root Cause Workspace and Exception Analysis for Performance Insight Explorer.
Organizes operational drivers under 5 structured pillars: Demand, Capacity, Process, Complexity, Data Quality.
Computes Pearson & Spearman correlations with mandatory causation disclaimer.
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def calculate_correlations(
    df: pd.DataFrame,
    numeric_cols: List[str]
) -> Dict[str, Any]:
    """Calculate Pearson and Spearman correlation matrices with p-values and mandatory disclaimers."""
    valid_cols = [c for c in numeric_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if len(valid_cols) < 2:
        return {"error": "At least 2 numeric columns required for correlation analysis."}
        
    sub_df = df[valid_cols].dropna()
    if len(sub_df) < 5:
        return {"error": "Insufficient complete observations (<5) for statistical correlation."}
        
    pearson_corr = sub_df.corr(method="pearson").round(3)
    spearman_corr = sub_df.corr(method="spearman").round(3)
    
    significant_pairs = []
    n = len(sub_df)
    
    for i in range(len(valid_cols)):
        for j in range(i + 1, len(valid_cols)):
            col1, col2 = valid_cols[i], valid_cols[j]
            r_val, p_val = stats.pearsonr(sub_df[col1], sub_df[col2])
            rho_val, rho_p = stats.spearmanr(sub_df[col1], sub_df[col2])
            
            if abs(r_val) >= 0.4 or abs(rho_val) >= 0.4:
                strength = "Strong" if max(abs(r_val), abs(rho_val)) >= 0.7 else "Moderate"
                direction = "Positive" if r_val > 0 else "Negative"
                significant_pairs.append({
                    "variable_1": col1,
                    "variable_2": col2,
                    "pearson_r": round(r_val, 3),
                    "pearson_p": round(p_val, 4),
                    "spearman_rho": round(rho_val, 3),
                    "spearman_p": round(rho_p, 4),
                    "relationship": f"{strength} {direction} Association",
                    "sample_size": n
                })
                
    return {
        "pearson_matrix": pearson_corr,
        "spearman_matrix": spearman_corr,
        "significant_pairs": significant_pairs,
        "sample_size": n,
        "disclaimer": "CRITICAL GOVERNANCE NOTICE: Association does not demonstrate causation. External unobserved factors, process changes, or reporting variations may confound observed correlations."
    }


def analyze_root_cause_pillars(
    df: pd.DataFrame,
    mappings: Dict[str, str],
    kpi_results: Dict[str, Any],
    qa_report: Dict[str, Any]
) -> Dict[str, Any]:
    """Synthesize evidence across the 5 operational pillars: Demand, Capacity, Process, Complexity, Data Quality.
    Strictly data-driven based on active model columns.
    """
    role_to_col: Dict[str, str] = {}
    for c, r in (mappings or {}).items():
        role_str = r.get("suggested_role", r.get("role")) if isinstance(r, dict) else (str(r) if r else None)
        if role_str and c in df.columns:
            role_to_col[role_str] = c
    pillars = {
        "demand": {"title": "1. Demand & Intake Volume", "findings": [], "risk_level": "Low"},
        "capacity": {"title": "2. Capacity & Resource Allocation", "findings": [], "risk_level": "Low"},
        "process": {"title": "3. Process & Workflow Throughput", "findings": [], "risk_level": "Low"},
        "complexity": {"title": "4. Case Mix & Complexity", "findings": [], "risk_level": "Low"},
        "data_quality": {"title": "5. Data Quality & Measurement Integrity", "findings": [], "risk_level": "Low"}
    }
    
    # 1. DEMAND
    if "received" in role_to_col:
        s_rec = pd.to_numeric(df[role_to_col["received"]], errors="coerce").dropna()
        if len(s_rec) > 1:
            rec_cv = float(s_rec.std() / s_rec.mean()) if s_rec.mean() > 0 else 0.0
            pillars["demand"]["findings"].append(f"Total intake demand is {s_rec.sum():,.0f} cases (mean {s_rec.mean():,.1f}/period).")
            if rec_cv > 0.3:
                pillars["demand"]["findings"].append(f"High intake volatility observed (Coefficient of Variation = {rec_cv:.2f}). Spikes in intake challenge fixed capacity.")
                pillars["demand"]["risk_level"] = "Medium"
    else:
        pillars["demand"]["findings"].append("Intake demand volume not present in active assessment dataset (gracefully omitted).")
                
    # 2. CAPACITY
    if "fte" in role_to_col:
        s_fte = pd.to_numeric(df[role_to_col["fte"]], errors="coerce").dropna()
        if len(s_fte) > 0:
            pillars["capacity"]["findings"].append(f"Average staffed capacity is {s_fte.mean():.2f} FTE (range {s_fte.min():.1f} - {s_fte.max():.1f}).")
    elif "FTE" in df.columns:
        s_fte = pd.to_numeric(df["FTE"], errors="coerce").dropna()
        if len(s_fte) > 0:
            pillars["capacity"]["findings"].append(f"Average staffed capacity is {s_fte.mean():.2f} FTE.")

    if "hours_available" in role_to_col:
        s_h = pd.to_numeric(df[role_to_col["hours_available"]], errors="coerce").dropna()
        if len(s_h) > 0:
            pillars["capacity"]["findings"].append(f"Total available capacity: {s_h.sum():,.1f} scheduled hours (mean {s_h.mean():,.1f} hrs/record).")
    if "utilisation_pct" in kpi_results.get("summary_kpis", {}):
        u_val = kpi_results["summary_kpis"]["utilisation_pct"].get("value")
        if u_val is not None:
            pillars["capacity"]["findings"].append(f"Operational utilisation is {u_val:.1f}%.")
            if u_val > 92.0:
                pillars["capacity"]["findings"].append("High utilisation (>92%) indicates little buffer capacity, increasing backlog queuing risk.")
                pillars["capacity"]["risk_level"] = "High"
            elif u_val < 70.0:
                pillars["capacity"]["findings"].append("Utilisation below 70% suggests potential under-utilised hours or idle capacity.")
                pillars["capacity"]["risk_level"] = "Medium"

    if not pillars["capacity"]["findings"]:
        pillars["capacity"]["findings"].append("Capacity metrics not present in active dataset.")

    # 3. PROCESS
    if "Availability %" in df.columns:
        s_av = pd.to_numeric(df["Availability %"], errors="coerce").dropna()
        if len(s_av) > 0:
            pillars["process"]["findings"].append(f"Overall average availability is {s_av.mean():.2%} (median: {s_av.median():.2%}).")
            uncapped = int((s_av > 1.0).sum())
            if uncapped > 0:
                pillars["process"]["findings"].append(f"{uncapped} observation(s) exhibit Availability > 100% (max: {s_av.max():.1%}).")
    elif "processing_time" in role_to_col:
        s_tat = pd.to_numeric(df[role_to_col["processing_time"]], errors="coerce").dropna()
        if len(s_tat) > 0:
            pillars["process"]["findings"].append(f"Median cycle time is {s_tat.median():.1f} days (90th percentile: {s_tat.quantile(0.9):.1f} days).")

    if not pillars["process"]["findings"]:
        pillars["process"]["findings"].append("Workflow throughput metrics not present in active dataset (gracefully omitted).")

    # 4. COMPLEXITY / COHORT MIX
    if "Service" in df.columns and "Band" in df.columns:
        top_s = df["Service"].value_counts().head(2).to_dict()
        top_s_str = ", ".join([f"{k} ({v:,} rows)" for k, v in top_s.items()])
        top_b = df["Band"].value_counts().head(2).to_dict()
        top_b_str = ", ".join([f"{k} ({v:,} rows)" for k, v in top_b.items()])
        pillars["complexity"]["findings"].append(f"Dominant Services: {top_s_str}.")
        pillars["complexity"]["findings"].append(f"Dominant Staff Bands: {top_b_str}.")
    elif "case_type" in role_to_col or "category" in role_to_col:
        c_col = role_to_col.get("case_type") or role_to_col.get("category")
        top_cats = df[c_col].value_counts(normalize=True).head(3).to_dict()
        top_str = ", ".join([f"{k} ({v*100:.1f}%)" for k, v in top_cats.items()])
        pillars["complexity"]["findings"].append(f"Top case classifications: {top_str}.")
    else:
        pillars["complexity"]["findings"].append("Case complexity breakdown not present in active dataset (gracefully omitted).")
        
    # 5. DATA QUALITY
    crit_count = qa_report.get("critical_count", 0)
    warn_count = qa_report.get("warning_count", 0)
    health_score = qa_report.get("health_score", 100.0)
    
    pillars["data_quality"]["findings"].append(f"Data Health Score: {health_score:.1f}/100 with {crit_count} critical and {warn_count} warning issues.")
    if "Availability %" in df.columns:
        uncalc = int(df["Availability %"].isna().sum())
        if uncalc > 0:
            pillars["data_quality"]["findings"].append(f"{uncalc:,} records ({uncalc/len(df):.1%}) contain missing or zero denominators, correctly returning blank.")
            
    if crit_count > 0:
        pillars["data_quality"]["findings"].append("Critical data anomalies must be resolved before finalizing causal conclusions.")
        pillars["data_quality"]["risk_level"] = "High"
    elif warn_count > 0:
        pillars["data_quality"]["risk_level"] = "Medium"
        
    return pillars
