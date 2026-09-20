"""Dynamic No-Code KPI Configuration and Evaluation Engine for Performance Insight Explorer.
Supports dynamic KPI definitions, custom formulas, numerator/denominator rates, composite scores,
direction-aware threshold evaluation (RAG status), and safe zero-denominator mathematics.
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from core.constants import TargetDirection
from core.models import KPIDefinition


def safe_divide(
    num: Union[float, int, pd.Series, np.ndarray],
    den: Union[float, int, pd.Series, np.ndarray],
    fill_value: float = np.nan
) -> Union[float, pd.Series, np.ndarray]:
    """Perform zero-safe division returning fill_value when denominator is zero, NaN, or numerator is NaN."""
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        s_num = pd.to_numeric(num, errors="coerce")
        s_den = pd.to_numeric(den, errors="coerce").replace({0: np.nan, 0.0: np.nan})
        res = s_num / s_den
        return res.fillna(fill_value)
    else:
        try:
            f_num = float(num)
            f_den = float(den)
            if np.isnan(f_num) or np.isnan(f_den) or f_den == 0.0:
                return fill_value
            return f_num / f_den
        except Exception:
            return fill_value


def evaluate_kpi_rag_status(
    actual: Optional[float],
    kpi_def: KPIDefinition
) -> Dict[str, Any]:
    """Evaluate RAG (Red/Amber/Green) performance status with directional awareness.
    Supports: Higher is Better, Lower is Better, Target Range, Exact Target, Informational.
    """
    if actual is None or np.isnan(actual):
        return {
            "status": "No Data",
            "color": "#6c757d",  # Neutral gray
            "icon": "⚪",
            "variance": None,
            "variance_pct": None,
            "attainment_pct": None,
            "interpretation": "No data available to evaluate KPI."
        }

    target = kpi_def.target_value
    direction = kpi_def.directionality
    if isinstance(direction, str):
        direction = TargetDirection(direction)

    if direction == TargetDirection.INFORMATIONAL:
        return {
            "status": "Informational",
            "color": "#0d6efd",  # Informational blue
            "icon": "ℹ️",
            "variance": None,
            "variance_pct": None,
            "attainment_pct": None,
            "interpretation": f"Current value: {actual:,.2f} {kpi_def.unit} (Informational benchmark only)."
        }

    if target is None and direction != TargetDirection.TARGET_RANGE:
        return {
            "status": "Informational",
            "color": "#0d6efd",
            "icon": "ℹ️",
            "variance": None,
            "variance_pct": None,
            "attainment_pct": None,
            "interpretation": f"Current value: {actual:,.2f} {kpi_def.unit} (No target benchmark configured)."
        }

    var_num = (actual - target) if target is not None else 0.0
    var_pct = (var_num / target * 100.0) if (target is not None and target != 0.0 and not np.isnan(target)) else 0.0
    attainment = (actual / target * 100.0) if (target is not None and target != 0.0 and not np.isnan(target)) else None

    # 1. Higher Is Better
    if direction == TargetDirection.HIGHER_IS_BETTER:
        crit_thresh = kpi_def.critical_threshold if kpi_def.critical_threshold is not None else (target * 0.85)
        warn_thresh = kpi_def.warning_threshold if kpi_def.warning_threshold is not None else (target * 0.95)

        if actual >= target:
            status = "Green (Meeting Target)"
            color = "#198754"
            icon = "🟢"
            interp = f"Surplus: {var_pct:+.1f}% above target benchmark ({var_num:+,.2f} {kpi_def.unit})."
        elif actual >= warn_thresh:
            status = "Amber (Near Target / Warning)"
            color = "#ffc107"
            icon = "🟡"
            interp = f"Minor shortfall: {abs(var_pct):.1f}% below target ({var_num:+,.2f} {kpi_def.unit})."
        else:
            status = "Red (Critical Shortfall)"
            color = "#dc3545"
            icon = "🔴"
            interp = f"Severe deficit: {abs(var_pct):.1f}% below target ({var_num:+,.2f} {kpi_def.unit})."

    # 2. Lower Is Better (e.g. wait time, error rate, backlog)
    elif direction == TargetDirection.LOWER_IS_BETTER:
        crit_thresh = kpi_def.critical_threshold if kpi_def.critical_threshold is not None else (target * 1.25)
        warn_thresh = kpi_def.warning_threshold if kpi_def.warning_threshold is not None else (target * 1.05)

        if actual <= target:
            status = "Green (Within Limit)"
            color = "#198754"
            icon = "🟢"
            interp = f"Favorable: {abs(var_pct):.1f}% below upper threshold ceiling ({var_num:+,.2f} {kpi_def.unit})."
        elif actual <= warn_thresh:
            status = "Amber (Warning / Approaching Limit)"
            color = "#ffc107"
            icon = "🟡"
            interp = f"Exceeding standard slightly by {var_pct:+.1f}% ({var_num:+,.2f} {kpi_def.unit})."
        else:
            status = "Red (Critical Breach)"
            color = "#dc3545"
            icon = "🔴"
            interp = f"Critical threshold breach: {var_pct:+.1f}% above target limit ({var_num:+,.2f} {kpi_def.unit})."

    # 3. Target Range (e.g., Bed occupancy 85-90%)
    elif direction == TargetDirection.TARGET_RANGE:
        t_min = kpi_def.target_min if kpi_def.target_min is not None else (target * 0.90)
        t_max = kpi_def.target_max if kpi_def.target_max is not None else (target * 1.10)

        if t_min <= actual <= t_max:
            status = "Green (In Target Range)"
            color = "#198754"
            icon = "🟢"
            interp = f"Optimal: Within ideal band [{t_min:,.1f} - {t_max:,.1f} {kpi_def.unit}]."
        else:
            status = "Amber (Out of Range)"
            color = "#ffc107"
            icon = "🟡"
            interp = f"Deviation: Outside target range [{t_min:,.1f} - {t_max:,.1f} {kpi_def.unit}]."

    # 4. Exact Target
    else:
        if round(actual, 2) == round(target, 2):
            status = "Green (Exact Target)"
            color = "#198754"
            icon = "🟢"
            interp = f"Exact match on target standard {target:,.2f} {kpi_def.unit}."
        else:
            status = "Amber (Variance Observed)"
            color = "#ffc107"
            icon = "🟡"
            interp = f"Variance of {var_num:+,.2f} {kpi_def.unit} from target {target:,.2f}."

    return {
        "status": status,
        "color": color,
        "icon": icon,
        "variance": round(var_num, 2),
        "variance_pct": round(var_pct, 2),
        "attainment_pct": round(attainment, 1) if attainment is not None else None,
        "interpretation": interp
    }


def compute_kpi_value(
    df: pd.DataFrame,
    kpi_def: KPIDefinition
) -> Tuple[Optional[float], Optional[pd.Series], str]:
    """Evaluate a KPI definition on dataframe.
    Returns (aggregated_scalar_value, row_level_series, status_message).
    """
    if df is None or len(df) == 0:
        return None, None, "Dataframe is empty."

    # Sample size validation
    if len(df) < kpi_def.min_sample_size:
        return None, None, f"Insufficient sample size (N={len(df)} < Minimum required N={kpi_def.min_sample_size})."

    agg = kpi_def.aggregation_method.lower()

    try:
        # Case A: Rate / Ratio with Numerator & Denominator
        if kpi_def.numerator_field and kpi_def.denominator_field:
            num_col = kpi_def.numerator_field
            den_col = kpi_def.denominator_field

            if num_col not in df.columns or den_col not in df.columns:
                return None, None, f"Required columns ('{num_col}' or '{den_col}') not found in dataset."

            num_series = pd.to_numeric(df[num_col], errors="coerce")
            den_series = pd.to_numeric(df[den_col], errors="coerce")

            row_series = safe_divide(num_series, den_series)
            if kpi_def.unit == "%" or "pct" in kpi_def.id:
                row_series = row_series * 100.0

            # Aggregation logic
            if agg in ["sum_ratio", "rate", "percentage", "weighted"]:
                total_num = num_series.sum()
                total_den = den_series.sum()
                scalar_val = float(safe_divide(total_num, total_den))
                if kpi_def.unit == "%" or "pct" in kpi_def.id:
                    scalar_val = scalar_val * 100.0
            elif agg == "mean":
                scalar_val = float(row_series.mean())
            elif agg == "median":
                scalar_val = float(row_series.median())
            else:
                scalar_val = float(row_series.mean())

            return round(scalar_val, 2), row_series, "Calculated successfully."

        # Case B: Single Source Field Aggregation
        elif kpi_def.source_field:
            col = kpi_def.source_field
            if col not in df.columns:
                return None, None, f"Source column '{col}' not found in dataset."

            series = pd.to_numeric(df[col], errors="coerce")

            if agg == "sum":
                scalar = float(series.sum())
            elif agg == "mean" or agg == "average":
                scalar = float(series.mean())
            elif agg == "median":
                scalar = float(series.median())
            elif agg == "count":
                scalar = float(series.count())
            elif agg == "iqr":
                scalar = float(series.quantile(0.75) - series.quantile(0.25))
            else:
                scalar = float(series.mean())

            return round(scalar, 2), series, "Calculated successfully."

        # Case C: Row Count
        elif agg == "count":
            return float(len(df)), pd.Series([1]*len(df), index=df.index), "Calculated total row count."

        else:
            return None, None, "Invalid KPI configuration: Neither source_field nor numerator/denominator provided."

    except Exception as e:
        return None, None, f"Calculation failed: {str(e)}"
