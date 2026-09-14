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
    """Synthesize evidence across the 5 operational pillars: Demand, Capacity, Process, Complexity, Data Quality."""
    role_to_col = {r: c for c, r in mappings.items() if r and c in df.columns}
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
                
    # 2. CAPACITY
    if "fte" in role_to_col:
        s_fte = pd.to_numeric(df[role_to_col["fte"]], errors="coerce").dropna()
        pillars["capacity"]["findings"].append(f"Average staffed capacity is {s_fte.mean():.1f} FTE (range {s_fte.min():.1f} - {s_fte.max():.1f}).")
        
    if "utilisation_pct" in kpi_results.get("summary_kpis", {}):
        u_val = kpi_results["summary_kpis"]["utilisation_pct"]["value"]
        if u_val is not None:
            pillars["capacity"]["findings"].append(f"Operational utilisation is {u_val:.1f}%.")
            if u_val > 92.0:
                pillars["capacity"]["findings"].append("High utilisation (>92%) indicates little buffer capacity, increasing backlog queuing risk.")
                pillars["capacity"]["risk_level"] = "High"
            elif u_val < 70.0:
                pillars["capacity"]["findings"].append("Utilisation below 70% suggests potential under-utilised hours or idle capacity.")
                pillars["capacity"]["risk_level"] = "Medium"
                
    # 3. PROCESS
    if "processing_time" in role_to_col:
        s_tat = pd.to_numeric(df[role_to_col["processing_time"]], errors="coerce").dropna()
        if len(s_tat) > 0:
            pillars["process"]["findings"].append(f"Median cycle time is {s_tat.median():.1f} days (90th percentile is {s_tat.quantile(0.9):.1f} days).")
            if s_tat.mean() > s_tat.median() * 1.3:
                pillars["process"]["findings"].append("Right-skewed distribution indicates a long tail of stalled or complex outlier cases.")
                pillars["process"]["risk_level"] = "Medium"
                
    if "backlog_change" in kpi_results.get("summary_kpis", {}):
        bl_val = kpi_results["summary_kpis"]["backlog_change"]["value"]
        if bl_val > 0:
            pillars["process"]["findings"].append(f"Backlog has expanded by {bl_val:,.0f} cases over the observed window.")
            pillars["process"]["risk_level"] = "High"
            
    # 4. COMPLEXITY
    if "case_type" in role_to_col or "category" in role_to_col:
        c_col = role_to_col.get("case_type") or role_to_col.get("category")
        top_cats = df[c_col].value_counts(normalize=True).head(3).to_dict()
        top_str = ", ".join([f"{k} ({v*100:.1f}%)" for k, v in top_cats.items()])
        pillars["complexity"]["findings"].append(f"Top case mix classifications: {top_str}.")
        
    # 5. DATA QUALITY
    crit_count = qa_report.get("critical_count", 0)
    warn_count = qa_report.get("warning_count", 0)
    health_score = qa_report.get("health_score", 100.0)
    
    pillars["data_quality"]["findings"].append(f"Data Health Score: {health_score:.1f}/100 with {crit_count} critical and {warn_count} warning issues.")
    if crit_count > 0:
        pillars["data_quality"]["findings"].append("Critical data anomalies (e.g. missing values, reconciliation gaps) must be resolved before finalizing causal conclusions.")
        pillars["data_quality"]["risk_level"] = "High"
    elif warn_count > 0:
        pillars["data_quality"]["risk_level"] = "Medium"
        
    return pillars
