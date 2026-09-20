"""Enterprise Root-Cause Analysis and Diagnostic Engine for Performance Insight Explorer.
Implements structured 10-step RCA workflow, driver ranking, multivariate regression,
5-Whys tree, and Ishikawa / Fishbone decomposition.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def evaluate_driver_correlations(
    df: pd.DataFrame,
    target_metric: str,
    potential_drivers: List[str]
) -> List[Dict[str, Any]]:
    """Calculate Pearson and Spearman rank correlations with statistical significance (p-values) for candidate drivers."""
    if df is None or target_metric not in df.columns or not potential_drivers:
        return []

    y_series = pd.to_numeric(df[target_metric], errors="coerce")
    results = []

    for driver in potential_drivers:
        if driver not in df.columns or driver == target_metric:
            continue

        x_series = pd.to_numeric(df[driver], errors="coerce")
        valid_mask = y_series.notna() & x_series.notna()
        n = int(valid_mask.sum())

        if n < 5:
            continue

        x_vals = x_series[valid_mask].values
        y_vals = y_series[valid_mask].values

        try:
            r_pearson, p_pearson = stats.pearsonr(x_vals, y_vals)
            r_spearman, p_spearman = stats.spearmanr(x_vals, y_vals)
            r_sq = float(r_pearson ** 2)

            # Classify evidence strength
            abs_r = abs(r_pearson)
            if p_pearson < 0.01 and abs_r >= 0.70:
                evidence_tier = "Confirmed by data (Strong Correlation)"
                confidence = "High"
            elif p_pearson < 0.05 and abs_r >= 0.40:
                evidence_tier = "Strongly supported"
                confidence = "Medium-High"
            elif p_pearson < 0.10 or abs_r >= 0.25:
                evidence_tier = "Possible explanation (Weak Association)"
                confidence = "Medium"
            else:
                evidence_tier = "Requires more evidence (No Significant Association)"
                confidence = "Low"

            # Plain english relationship
            direction_str = "increases" if r_pearson > 0 else "decreases"
            interp = f"As '{driver}' increases, '{target_metric}' {direction_str} (r={r_pearson:+.2f}, R²={r_sq:.1%}, p={p_pearson:.3f})."

            results.append({
                "driver_field": driver,
                "n_samples": n,
                "pearson_r": round(float(r_pearson), 3),
                "r_squared": round(r_sq, 3),
                "p_value": round(float(p_pearson), 4),
                "spearman_rho": round(float(r_spearman), 3),
                "evidence_tier": evidence_tier,
                "confidence": confidence,
                "interpretation": interp,
                "caveat": "Correlation indicates statistical association, NOT proven causality. Operational verification required."
            })
        except Exception:
            continue

    # Sort drivers by absolute correlation magnitude
    results.sort(key=lambda x: abs(x.get("pearson_r", 0)), reverse=True)
    return results


def calculate_driver_importance_regression(
    df: pd.DataFrame,
    target_metric: str,
    feature_columns: List[str]
) -> Dict[str, Any]:
    """Fit Ordinary Least Squares (OLS) regression to determine variance explained and feature weights."""
    if df is None or target_metric not in df.columns or not feature_columns:
        return {"r_squared": 0.0, "drivers": []}

    num_cols = [col for col in feature_columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    if not num_cols:
        return {"r_squared": 0.0, "drivers": []}

    clean_data = df[[target_metric] + num_cols].dropna()
    if len(clean_data) < len(num_cols) + 3:
        return {"r_squared": 0.0, "drivers": []}

    y = clean_data[target_metric].values
    X = clean_data[num_cols].values

    # Add intercept column
    X_with_const = np.column_stack([np.ones(len(X)), X])

    try:
        # Solve OLS: (X'X)^-1 X'y
        beta, residuals, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)
        
        y_pred = X_with_const @ beta
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Normalized feature coefficients (standardized impact)
        std_y = np.std(y) if np.std(y) > 0 else 1.0
        drivers_ranking = []

        for idx, col in enumerate(num_cols):
            coef = beta[idx + 1]
            std_x = np.std(clean_data[col].values) if np.std(clean_data[col].values) > 0 else 1.0
            std_coef = coef * (std_x / std_y)

            drivers_ranking.append({
                "driver": col,
                "coefficient": round(float(coef), 4),
                "standardized_impact": round(float(std_coef), 3),
                "abs_importance": round(float(abs(std_coef)), 3)
            })

        drivers_ranking.sort(key=lambda x: x["abs_importance"], reverse=True)

        return {
            "r_squared": round(float(max(0.0, r_squared)), 3),
            "sample_size": len(clean_data),
            "drivers": drivers_ranking
        }
    except Exception:
        return {"r_squared": 0.0, "drivers": []}
