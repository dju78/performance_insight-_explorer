"""KPI Engine and mathematical formulas for Performance Insight Explorer.
Protects all divisions against zero-denominators, clearly flags estimated measures,
and supports customizable target directionality:
- higher_is_better (e.g. completions, revenue, quality)
- lower_is_better (e.g. turnaround time, backlog, cost, error rate)
- neutral (descriptive benchmark only)
"""
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd


class TargetDirection:
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


def safe_divide(
    numerator: Union[pd.Series, np.ndarray, float, int],
    denominator: Union[pd.Series, np.ndarray, float, int],
    fill_value: float = np.nan,
    default: Optional[float] = None
) -> Union[pd.Series, np.ndarray, float]:
    actual_fill = default if default is not None else fill_value
    """Divide numerator by denominator, safely replacing 0 or invalid denominators with fill_value."""
    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        num_s = pd.to_numeric(numerator, errors="coerce")
        den_s = pd.to_numeric(denominator, errors="coerce")
        result = num_s / den_s.replace({0: np.nan, 0.0: np.nan})
        return result.fillna(actual_fill)
    else:
        try:
            num = float(numerator)
            den = float(denominator)
            if den == 0.0 or np.isnan(den):
                return actual_fill
            return num / den
        except Exception:
            return actual_fill


def evaluate_target_variance(
    actual: Optional[float],
    target: Optional[float],
    direction: str = TargetDirection.HIGHER_IS_BETTER
) -> Dict[str, Any]:
    """Calculate variance and direction-aware evaluation between actual and target.
    
    direction: 'higher_is_better', 'lower_is_better', or 'neutral'
    """
    if actual is None:
        return {"variance_num": None, "variance_pct": None, "is_favorable": None, "commentary": "No actual value recorded."}
    if target is None:
        return {"variance_num": None, "variance_pct": None, "is_favorable": None, "commentary": "No target specified."}
        
    act_f = float(actual)
    tgt_f = float(target)
    var_num = act_f - tgt_f
    
    if tgt_f == 0.0 or np.isnan(tgt_f):
        var_pct = 0.0
        commentary = "Zero target baseline; variance percentage calculated against zero."
        if direction == TargetDirection.HIGHER_IS_BETTER:
            is_favorable = (var_num >= 0)
        elif direction == TargetDirection.LOWER_IS_BETTER:
            is_favorable = (var_num <= 0)
        else:
            is_favorable = None
        return {
            "variance_num": round(var_num, 2),
            "variance_pct": var_pct,
            "is_favorable": is_favorable,
            "commentary": commentary
        }
        
    var_pct = round((var_num / tgt_f) * 100.0, 2)
    
    if direction == TargetDirection.LOWER_IS_BETTER:
        is_favorable = (var_num <= 0)
        if is_favorable:
            commentary = f"Favorable reduction: {abs(var_pct):.1f}% lower than target ({var_num:+,.2f})."
        else:
            commentary = f"Unfavorable increase: exceeding upper threshold by {var_pct:.1f}% ({var_num:+,.2f})."
    elif direction == TargetDirection.HIGHER_IS_BETTER:
        is_favorable = (var_num >= 0)
        if is_favorable:
            commentary = f"Favorable surplus: {var_pct:+.1f}% above target benchmark."
        else:
            commentary = f"Performance shortfall: {abs(var_pct):.1f}% below target benchmark."
    else:  # neutral
        is_favorable = None
        commentary = f"Neutral tracking vs benchmark: {var_pct:+.1f}% difference ({var_num:+,.2f})."
        
    return {
        "variance_num": round(var_num, 2),
        "variance_pct": var_pct,
        "is_favorable": is_favorable,
        "commentary": commentary
    }


def calculate_kpis(
    df: pd.DataFrame,
    mappings: Dict[str, str],
    target_direction: str = TargetDirection.HIGHER_IS_BETTER
) -> Dict[str, Any]:
    """Calculate all supported operational performance KPIs from confirmed mapped columns.
    
    mappings: dict of {source_column: role_key}
    target_direction: 'higher_is_better', 'lower_is_better', 'neutral'
    """
    if not mappings:
        return {
            "calculated_df": pd.DataFrame(index=df.index if df is not None else []),
            "summary_kpis": {},
            "active_kpi_keys": [],
            "role_to_col": {},
            "target_direction": target_direction
        }
        
    role_to_col: Dict[str, str] = {}
    for col, role in mappings.items():
        role_str = role.get("suggested_role") if isinstance(role, dict) else (str(role) if role else None)
        if role_str and col in df.columns:
            role_to_col[role_str] = col
            
    calc_df = pd.DataFrame(index=df.index)
    summary_kpis = {}
    active_kpi_keys = []
    
    # 1. TARGET ACHIEVEMENT & VARIANCE
    actual_col = role_to_col.get("actual") or role_to_col.get("completed")
    target_col = role_to_col.get("target")
    
    if actual_col and target_col:
        s_act = pd.to_numeric(df[actual_col], errors="coerce")
        s_tgt = pd.to_numeric(df[target_col], errors="coerce")
        
        calc_df["target_achievement_pct"] = safe_divide(s_act, s_tgt) * 100.0
        calc_df["target_variance"] = s_act - s_tgt
        calc_df["target_variance_pct"] = safe_divide(s_act - s_tgt, s_tgt) * 100.0
        
        tot_act = float(s_act.sum())
        tot_tgt = float(s_tgt.sum())
        agg_achieve = safe_divide(tot_act, tot_tgt) * 100.0
        agg_var = tot_act - tot_tgt
        agg_var_pct = safe_divide(tot_act - tot_tgt, tot_tgt) * 100.0
        
        var_eval = evaluate_target_variance(tot_act, tot_tgt, direction=target_direction)
        
        summary_kpis["target_achievement_pct"] = {
            "name": "Target Achievement %",
            "value": round(agg_achieve, 2) if not np.isnan(agg_achieve) else None,
            "unit": "%",
            "is_estimated": False,
            "formula": "Sum(Actual) / Sum(Target) * 100",
            "target_direction": target_direction,
            "is_favorable": var_eval["is_favorable"],
            "description": "Weighted target achievement across the selected dataset.",
            "interpretation": var_eval["commentary"]
        }
        summary_kpis["target_variance"] = {
            "name": "Target Variance",
            "value": round(agg_var, 2) if not np.isnan(agg_var) else None,
            "unit": "Units",
            "is_estimated": False,
            "formula": "Sum(Actual) - Sum(Target)",
            "target_direction": target_direction,
            "is_favorable": var_eval["is_favorable"],
            "description": "Net absolute difference between actual performance and target standard.",
            "interpretation": var_eval["commentary"]
        }
        active_kpi_keys.extend(["target_achievement_pct", "target_variance", "target_variance_pct"])
        
    # 2. PRODUCTIVITY (Sum(Completed) / Sum(FTE or Staff))
    comp_col = role_to_col.get("completed") or role_to_col.get("actual")
    fte_col = role_to_col.get("fte")
    staff_col = role_to_col.get("staff")
    
    if comp_col and (fte_col or staff_col):
        s_comp = pd.to_numeric(df[comp_col], errors="coerce")
        denom_col = fte_col if fte_col else staff_col
        denom_name = "FTE" if fte_col else "Staff"
        s_denom = pd.to_numeric(df[denom_col], errors="coerce")
        
        calc_df["productivity"] = safe_divide(s_comp, s_denom)
        
        tot_comp = float(s_comp.sum())
        tot_denom = float(s_denom.sum())
        
        prod_val = safe_divide(tot_comp, tot_denom)
        
        summary_kpis["productivity"] = {
            "name": f"Productivity (Completed / {denom_name})",
            "value": round(prod_val, 2) if not np.isnan(prod_val) else None,
            "unit": f"Cases per {denom_name}-period",
            "is_estimated": False,
            "formula": f"Sum(Completed) / Sum({denom_name})",
            "description": f"Overall throughput delivery per aggregate {denom_name}-period exposure.",
            "interpretation": f"Overall throughput delivery rate is {prod_val:.2f} cases per {denom_name}-period. Case mix complexity and segment capacity should be reviewed before evaluating team variances."
        }
        active_kpi_keys.append("productivity")
        
    # 3. UTILISATION %
    h_used_col = role_to_col.get("hours_used")
    h_avail_col = role_to_col.get("hours_available")
    
    if h_used_col and h_avail_col:
        s_used = pd.to_numeric(df[h_used_col], errors="coerce")
        s_avail = pd.to_numeric(df[h_avail_col], errors="coerce")
        
        calc_df["utilisation_pct"] = safe_divide(s_used, s_avail) * 100.0
        
        tot_used = float(s_used.sum())
        tot_avail = float(s_avail.sum())
        agg_util = safe_divide(tot_used, tot_avail) * 100.0
        
        summary_kpis["utilisation_pct"] = {
            "name": "Utilisation %",
            "value": round(agg_util, 2) if not np.isnan(agg_util) else None,
            "unit": "%",
            "is_estimated": False,
            "formula": "Sum(Hours Used) / Sum(Hours Available) * 100",
            "description": "Proportion of scheduled capacity hours actively worked.",
            "interpretation": f"Utilisation is {agg_util:.1f}%. Interpret against the organisation's agreed operational benchmark; elevated levels may indicate capacity pressure."
        }
        active_kpi_keys.append("utilisation_pct")
        
    # 4. BACKLOG MOVEMENT & RECONCILIATION
    open_bl_col = role_to_col.get("opening_backlog")
    close_bl_col = role_to_col.get("closing_backlog")
    rec_col = role_to_col.get("received")
    time_col = role_to_col.get("reporting_period") or role_to_col.get("date")
    
    if open_bl_col and close_bl_col:
        s_open = pd.to_numeric(df[open_bl_col], errors="coerce")
        s_close = pd.to_numeric(df[close_bl_col], errors="coerce")
        calc_df["backlog_change"] = s_close - s_open
        
        if time_col and time_col in df.columns and len(df) > 0:
            df_time = df[[time_col, open_bl_col, close_bl_col]].dropna(subset=[time_col]).copy()
            df_time["_dt"] = pd.to_datetime(df_time[time_col], format="mixed", errors="coerce")
            if df_time["_dt"].notna().sum() > 0:
                min_p = df_time.sort_values("_dt").iloc[0]["_dt"]
                max_p = df_time.sort_values("_dt").iloc[-1]["_dt"]
                init_open = float(pd.to_numeric(df_time[df_time["_dt"] == min_p][open_bl_col], errors="coerce").sum())
                final_close = float(pd.to_numeric(df_time[df_time["_dt"] == max_p][close_bl_col], errors="coerce").sum())
            else:
                periods_sorted = sorted(df_time[time_col].astype(str).unique())
                init_open = float(pd.to_numeric(df_time[df_time[time_col].astype(str) == periods_sorted[0]][open_bl_col], errors="coerce").sum())
                final_close = float(pd.to_numeric(df_time[df_time[time_col].astype(str) == periods_sorted[-1]][close_bl_col], errors="coerce").sum())
            obs_net_change = final_close - init_open
        else:
            obs_net_change = float(s_close.iloc[-1] - s_open.iloc[0]) if len(df) > 0 and s_close.notna().iloc[-1] and s_open.notna().iloc[0] else float(s_close.sum() - s_open.sum())
            
        summary_kpis["backlog_change"] = {
            "name": "Observed Backlog Change",
            "value": round(obs_net_change, 2),
            "unit": "Cases",
            "is_estimated": False,
            "formula": "Latest Period Total Closing Backlog - Earliest Period Total Opening Backlog" if time_col else "Final Closing - Initial Opening",
            "description": "Net observed queue inventory change across the active dataset.",
            "interpretation": "Positive indicates expanding backlog queue; negative indicates queue reduction."
        }
        active_kpi_keys.append("backlog_change")
        
        if rec_col and comp_col:
            s_rec = pd.to_numeric(df[rec_col], errors="coerce")
            s_comp_rec = pd.to_numeric(df[comp_col], errors="coerce")
            
            calc_df["expected_closing_backlog"] = s_open + s_rec - s_comp_rec
            calc_df["backlog_reconciliation_gap"] = s_close - calc_df["expected_closing_backlog"]
            
            tot_gap = float(calc_df["backlog_reconciliation_gap"].abs().sum())
            
            summary_kpis["backlog_reconciliation_gap"] = {
                "name": "Backlog Reconciliation Gap",
                "value": round(tot_gap, 2),
                "unit": "Cases (Abs Sum)",
                "is_estimated": False,
                "formula": "Sum(|Reported Closing - (Opening + Received - Completed)|)",
                "description": "Total discrepancy between reported inventory and flow accounting.",
                "interpretation": "A non-zero reconciliation gap indicates unrecorded transfers, adjustments, or reporting errors."
            }
            active_kpi_keys.extend(["expected_closing_backlog", "backlog_reconciliation_gap"])
            
    # 5. ESTIMATED NET FLOW PRESSURE (WHEN BACKLOG IS ABSENT)
    if rec_col and comp_col:
        s_rec = pd.to_numeric(df[rec_col], errors="coerce")
        s_comp = pd.to_numeric(df[comp_col], errors="coerce")
        
        calc_df["estimated_net_flow"] = s_rec - s_comp
        calc_df["completion_rate_pct"] = safe_divide(s_comp, s_rec) * 100.0
        
        tot_rec = float(s_rec.sum())
        tot_comp = float(s_comp.sum())
        net_flow_tot = tot_rec - tot_comp
        agg_comp_rate = safe_divide(tot_comp, tot_rec) * 100.0
        
        summary_kpis["estimated_net_flow"] = {
            "name": "Estimated Net Flow Pressure",
            "value": round(net_flow_tot, 2),
            "unit": "Cases",
            "is_estimated": True,
            "formula": "Sum(Cases Received) - Sum(Cases Completed)",
            "description": "ESTIMATED MEASURE: Net inflow pressure on operational capacity when formal backlog data is unavailable.",
            "interpretation": "ESTIMATED: Positive indicates demand exceeds completions, increasing queue pressure."
        }
        summary_kpis["completion_rate_pct"] = {
            "name": "Completion Rate %",
            "value": round(agg_comp_rate, 2) if not np.isnan(agg_comp_rate) else None,
            "unit": "%",
            "is_estimated": False,
            "formula": "Sum(Cases Completed) / Sum(Cases Received) * 100",
            "description": "Ratio of closed volume to newly received demand in the same period.",
            "interpretation": "Values >= 100% indicate throughput keeping pace with or outpacing incoming demand."
        }
        active_kpi_keys.extend(["estimated_net_flow", "completion_rate_pct"])
        
    # 6. PROCESSING TIME STATS
    proc_time_col = role_to_col.get("processing_time")
    if proc_time_col:
        s_tat = pd.to_numeric(df[proc_time_col], errors="coerce").dropna()
        if len(s_tat) > 0:
            med_tat = float(s_tat.median())
            mean_tat = float(s_tat.mean())
            p90_tat = float(s_tat.quantile(0.90))
            
            summary_kpis["processing_time_median"] = {
                "name": "Processing Time (Median)",
                "value": round(med_tat, 2),
                "unit": "Days / Hours",
                "is_estimated": False,
                "formula": "Median(Processing Time)",
                "description": "50th percentile turnaround duration (robust to extreme outliers).",
                "interpretation": f"Median turnaround is {med_tat:.1f} vs mean {mean_tat:.1f}; 90% of cases completed within {p90_tat:.1f} units."
            }
            active_kpi_keys.append("processing_time_median")
            
    # 7. QUALITY MEASURE
    qual_col = role_to_col.get("quality_measure")
    if qual_col:
        s_qual = pd.to_numeric(df[qual_col], errors="coerce").dropna()
        if len(s_qual) > 0:
            mean_qual = float(s_qual.mean())
            summary_kpis["quality_measure_mean"] = {
                "name": "Quality Audit Score (Mean)",
                "value": round(mean_qual, 2),
                "unit": "Score / %",
                "is_estimated": False,
                "formula": "Mean(Quality Score)",
                "description": "Average recorded quality audit or compliance rating.",
                "interpretation": f"Overall quality benchmark is {mean_qual:.1f}."
            }
            active_kpi_keys.append("quality_measure_mean")
            
    # 8. CUSTOMER MEASURE
    csat_col = role_to_col.get("customer_measure")
    if csat_col:
        s_csat = pd.to_numeric(df[csat_col], errors="coerce").dropna()
        if len(s_csat) > 0:
            mean_csat = float(s_csat.mean())
            summary_kpis["customer_measure_mean"] = {
                "name": "Customer Satisfaction (Mean)",
                "value": round(mean_csat, 2),
                "unit": "CSAT %",
                "is_estimated": False,
                "formula": "Mean(Customer Measure)",
                "description": "Average satisfaction rating or CSAT index.",
                "interpretation": f"Customer satisfaction average is {mean_csat:.1f}%."
            }
    # 9. WAIT TIME / QUEUE DELAY
    wait_col = role_to_col.get("wait_time")
    if wait_col:
        s_wait = pd.to_numeric(df[wait_col], errors="coerce").dropna()
        if len(s_wait) > 0:
            med_wait = float(s_wait.median())
            mean_wait = float(s_wait.mean())
            summary_kpis["wait_time_median"] = {
                "name": "Wait Time / Delay (Median)",
                "value": round(med_wait, 2),
                "unit": "Minutes / Days",
                "is_estimated": False,
                "formula": f"Median({wait_col})",
                "description": "50th percentile customer wait time or queue delay.",
                "interpretation": f"Median wait duration is {med_wait:.1f} units (mean {mean_wait:.1f})."
            }
            active_kpi_keys.append("wait_time_median")

    # 10. CUSTOM RATIO (NUMERATOR / DENOMINATOR)
    num_col = role_to_col.get("numerator")
    den_col = role_to_col.get("denominator")
    if num_col and den_col:
        s_num = pd.to_numeric(df[num_col], errors="coerce")
        s_den = pd.to_numeric(df[den_col], errors="coerce")
        calc_df["custom_ratio"] = safe_divide(s_num, s_den)
        tot_num = float(s_num.sum())
        tot_den = float(s_den.sum())
        agg_ratio = safe_divide(tot_num, tot_den)
        summary_kpis["custom_ratio"] = {
            "name": f"{num_col} / {den_col} Ratio",
            "value": round(agg_ratio, 2) if not np.isnan(agg_ratio) else None,
            "unit": "Ratio",
            "is_estimated": False,
            "formula": f"Sum({num_col}) / Sum({den_col})",
            "description": f"Normalised aggregate ratio of {num_col} to {den_col}.",
            "interpretation": f"Calculated ratio is {agg_ratio:.2f}. Interpret against the organisation's agreed benchmark."
        }
        active_kpi_keys.append("custom_ratio")

    # 11. OTHER MEASURE
    other_col = role_to_col.get("other_measure")
    if other_col:
        s_oth = pd.to_numeric(df[other_col], errors="coerce").dropna()
        if len(s_oth) > 0:
            mean_oth = float(s_oth.mean())
            summary_kpis["other_measure_mean"] = {
                "name": f"{other_col} (Mean)",
                "value": round(mean_oth, 2),
                "unit": "Units",
                "is_estimated": False,
                "formula": f"Mean({other_col})",
                "description": f"Average recorded value for {other_col}.",
                "interpretation": f"Mean value is {mean_oth:.2f}. Interpret against operational baseline."
            }
            active_kpi_keys.append("other_measure_mean")
            
    return {
        "calculated_df": calc_df,
        "summary_kpis": summary_kpis,
        "active_kpi_keys": active_kpi_keys,
        "role_to_col": role_to_col,
        "target_direction": target_direction
    }


def calculate_kpi_summary(
    df: pd.DataFrame,
    confirmed_mappings: Optional[Dict[str, str]] = None,
    target_directions: Optional[Dict[str, str]] = None,
    mappings: Optional[Dict[str, str]] = None,
    target_direction: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate normalized KPI summary dictionary."""
    map_dict = confirmed_mappings if confirmed_mappings is not None else (mappings or {})
    if not map_dict:
        return {}
        
    tgt_dir = target_direction or "higher_is_better"
    if target_directions:
        for d in target_directions.values():
            if d:
                tgt_dir = d
                break
                
    res = calculate_kpis(df, map_dict, tgt_dir)
    raw_kpis = res.get("summary_kpis", {})
    kpis = {}
    
    for k, v in raw_kpis.items():
        kpis[k] = {
            "display_name": v.get("name", k.replace("_", " ").title()),
            "actual": v.get("value"),
            "unit": v.get("unit", ""),
            "target": None,
            "variance_pct": None,
            "is_favorable": v.get("is_favorable"),
            "direction": v.get("target_direction", tgt_dir),
            "commentary": v.get("interpretation", ""),
            "formula": v.get("formula", "")
        }
        
    # Also enrich per numeric mapped column
    for col, role in map_dict.items():
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            col_dir = (target_directions or {}).get(col, "higher_is_better")
            mean_val = float(df[col].mean())
            tgt_col = None
            for t_col, t_role in map_dict.items():
                if t_role == "target" and t_col in df.columns:
                    tgt_col = t_col
                    break
            
            if col not in kpis:
                var_eval = None
                tgt_val = float(df[tgt_col].mean()) if tgt_col and tgt_col != col else None
                if tgt_val is not None:
                    var_eval = evaluate_target_variance(mean_val, tgt_val, col_dir)
                
                kpis[col] = {
                    "display_name": col.replace("_", " ").title(),
                    "actual": round(mean_val, 2),
                    "unit": "",
                    "target": round(tgt_val, 2) if tgt_val is not None else None,
                    "variance_pct": var_eval["variance_pct"] if var_eval else None,
                    "is_favorable": var_eval["is_favorable"] if var_eval else None,
                    "direction": col_dir,
                    "commentary": var_eval["commentary"] if var_eval else "",
                    "formula": f"Mean({col})"
                }
    return kpis


def calculate_utilisation(df: pd.DataFrame, volume_col: Optional[str] = None, fte_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates operational output per FTE with safe zero-handling and transparent commentary.
    """
    if df is None or volume_col is None or fte_col is None:
        return {
            "available": False,
            "reason": "Capacity analysis omitted: Required Volume or FTE column mapping not available.",
            "mean_ratio": 0.0,
            "commentary": "FTE capacity analysis not applicable for active dataset configuration."
        }
    if volume_col not in df.columns or fte_col not in df.columns:
        return {
            "available": False,
            "reason": f"Capacity analysis omitted: Specified columns ({volume_col}, {fte_col}) not present in dataset.",
            "mean_ratio": 0.0,
            "commentary": "FTE capacity analysis not applicable."
        }
    s_vol = pd.to_numeric(df[volume_col], errors="coerce").fillna(0)
    s_fte = pd.to_numeric(df[fte_col], errors="coerce").fillna(0)
    
    tot_vol = float(s_vol.sum())
    tot_fte = float(s_fte.sum())
    
    if tot_fte <= 0:
        return {
            "available": False,
            "reason": "Capacity analysis omitted: Total recorded FTE is zero or unavailable.",
            "mean_ratio": 0.0,
            "commentary": "Cannot evaluate output per FTE due to zero total denominator."
        }
    ratio = tot_vol / tot_fte
    return {
        "available": True,
        "total_volume": tot_vol,
        "total_fte": tot_fte,
        "mean_ratio": round(ratio, 2),
        "commentary": f"Mean throughput of {ratio:,.1f} units per FTE across active observation periods."
    }
