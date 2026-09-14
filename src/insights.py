"""Insight Engine for Performance Insight Explorer.
Generates structured, traceable insight cards following the required 6-part contract:
Finding -> Evidence -> Interpretation -> Business Implication -> Recommendation -> Limitation.
Respects Target Directionality (Higher is Better, Lower is Better, Neutral).
"""
from typing import Dict, Any, List, Optional
import pandas as pd


def generate_insights(
    kpi_results: Dict[str, Any],
    qa_report: Dict[str, Any],
    trend_results: Optional[Dict[str, Any]] = None,
    comp_results: Optional[Dict[str, Any]] = None,
    root_cause_results: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Generate structured, defensible insight cards based on verified calculations."""
    insights: List[Dict[str, Any]] = []
    summary_kpis = kpi_results.get("summary_kpis", {})
    target_direction = kpi_results.get("target_direction", "higher_is_better")
    insight_idx = 1
    
    # 1. Target Achievement Insight (Direction-Aware)
    if "target_achievement_pct" in summary_kpis:
        kpi_data = summary_kpis["target_achievement_pct"]
        achieve = kpi_data.get("value")
        var = summary_kpis.get("target_variance", {}).get("value", 0)
        
        if achieve is not None:
            if target_direction == "lower_is_better":
                is_meeting = (achieve <= 100.0)
                status_text = "meeting/beating operational threshold (lower is better)" if is_meeting else "exceeding threshold cap (unfavorable variance)"
                imp_text = "Turnaround/cost levels are controlled within threshold standard." if is_meeting else "Excess duration/costs increase delivery backlog and operational expense."
            elif target_direction == "higher_is_better":
                is_meeting = (achieve >= 100.0)
                status_text = "meeting/exceeding target benchmark" if is_meeting else "trailing benchmark output"
                imp_text = "Capacity headroom exists to absorb volume surges." if is_meeting else "Output deficit creates delivery backlog and customer SLA breach risks."
            else:
                status_text = "recording reference baseline"
                imp_text = "Establishes baseline performance across the operational cycle."
                
            direction_text = f"+{var:,.2f}" if var >= 0 else f"{var:,.2f}"
            
            insights.append({
                "insight_id": f"INS-{insight_idx:03d}",
                "category": "Target Performance",
                "finding": f"Overall operational achievement stands at {achieve:.1f}%, {status_text}.",
                "evidence": f"Total actual output vs target produces a net variance of {direction_text} units ({achieve:.1f}% achievement under {target_direction.replace('_', ' ')}).",
                "interpretation": kpi_data.get("interpretation", "Delivery evaluated relative to benchmark targets."),
                "business_implication": imp_text,
                "recommendation": "Review segment variance distribution and align capacity with demand profile.",
                "limitation": f"Assumes benchmark targets are uniformly calibrated under '{target_direction.replace('_', ' ')}' standard.",
                "traceable_metric": f"Target Achievement % ({kpi_data.get('formula')})",
                "status": "accepted"
            })
            insight_idx += 1
            
    # 2. Backlog & Queue Dynamics Insight
    if "backlog_change" in summary_kpis:
        bl_chg = summary_kpis["backlog_change"]["value"]
        if bl_chg is not None:
            is_growth = bl_chg > 0
            insights.append({
                "insight_id": f"INS-{insight_idx:03d}",
                "category": "Backlog & Capacity",
                "finding": f"Work-in-progress queue has {'grown' if is_growth else 'reduced'} by {abs(bl_chg):,.0f} cases across the observed timeline.",
                "evidence": f"Observed closing backlog minus opening backlog results in a net movement of {bl_chg:+,.0f} cases.",
                "interpretation": f"Flow balance indicates {'inflow demand exceeding clearance rate' if is_growth else 'operational clearances outpacing new intake'}.",
                "business_implication": f"{'Prolonged queue expansion increases turnaround times and breaches statutory SLAs' if is_growth else 'Queue reduction stabilizes turnaround times and improves customer experience'}.",
                "recommendation": "Implement dynamic work rebalancing and monitor weekly intake flow rate.",
                "limitation": "Excludes case aging distribution within the backlog queue unless individual case dates are provided.",
                "traceable_metric": "Backlog Change (Closing Backlog - Opening Backlog)",
                "status": "accepted"
            })
            insight_idx += 1
            
    # 3. Estimated Net Flow Pressure (When Backlog is Missing)
    elif "estimated_net_flow" in summary_kpis:
        net_flow = summary_kpis["estimated_net_flow"]["value"]
        comp_rate = summary_kpis.get("completion_rate_pct", {}).get("value", 100.0)
        if net_flow is not None:
            insights.append({
                "insight_id": f"INS-{insight_idx:03d}",
                "category": "Demand Flow",
                "finding": f"Estimated net intake pressure stands at {net_flow:+,.0f} cases (Completion Rate: {comp_rate:.1f}%).",
                "evidence": f"Total cases received minus completed produces an estimated flow pressure of {net_flow:+,.0f} units.",
                "interpretation": "ESTIMATED MEASURE: Inflow demand exceeds completed output, creating potential latent backlog accumulation.",
                "business_implication": "Unresolved demand volume can lead to customer escalation and delayed resolutions.",
                "recommendation": "Investigate intake queue and establish formal work-in-progress backlog tracking.",
                "limitation": "ESTIMATED: Calculated from period totals; does not track individual case cohort lifecycles.",
                "traceable_metric": "Estimated Net Flow Pressure (Received - Completed)",
                "status": "accepted"
            })
            insight_idx += 1
            
    # 4. Productivity & Utilisation
    if "productivity" in summary_kpis:
        prod_val = summary_kpis["productivity"]["value"]
        util_val = summary_kpis.get("utilisation_pct", {}).get("value")
        util_clause = f" with active staff utilisation of {util_val:.1f}%" if util_val is not None else ""
        
        insights.append({
            "insight_id": f"INS-{insight_idx:03d}",
            "category": "Operational Efficiency",
            "finding": f"Operational throughput averages {prod_val:.1f} completed cases per staff resource{util_clause}.",
            "evidence": f"Productivity ratio: {prod_val:.2f} completions/FTE." + (f" Utilisation: {util_val:.1f}%." if util_val else ""),
            "interpretation": "Reflects baseline workforce delivery rate under current operating workflows and case complexity mix.",
            "business_implication": "Variations in productivity directly influence staffing requirements and cost per case processed.",
            "recommendation": "Conduct comparative workflow analysis across teams to identify best practices and training opportunities.",
            "limitation": "Does not adjust for differing case complexity, staff tenure, or system downtime.",
            "traceable_metric": "Productivity (Total Completed / Mean FTE)",
            "status": "accepted"
        })
        insight_idx += 1
        
    # 5. Segment Variation / Outlier Teams
    if comp_results and "comparison_df" in comp_results and not comp_results.get("error"):
        comp_df = comp_results["comparison_df"]
        if len(comp_df) >= 2:
            top_grp = comp_df.iloc[0]
            bot_grp = comp_df.iloc[-1]
            diff_ratio = (top_grp["mean"] / bot_grp["mean"]) if bot_grp["mean"] > 0 else 1.0
            
            insights.append({
                "insight_id": f"INS-{insight_idx:03d}",
                "category": "Group Comparisons",
                "finding": f"Performance varies across groups, led by '{top_grp['group']}' while '{bot_grp['group']}' records the lowest throughput.",
                "evidence": f"'{top_grp['group']}' achieved mean of {top_grp['mean']:.1f} vs '{bot_grp['group']}' at {bot_grp['mean']:.1f} ({diff_ratio:.1f}x variance).",
                "interpretation": "Inter-group performance spread may reflect localized demand surges, staffing experience, or distinct case mixtures.",
                "business_implication": "Unbalanced group performance creates service delivery bottlenecks and inconsistent customer turnaround.",
                "recommendation": "Investigate underlying operational drivers between top and lower quartile groups before redistributing workload.",
                "limitation": "Group comparisons do not establish causal fault; case complexity differences must be reviewed.",
                "traceable_metric": f"Group Comparison ({comp_results.get('group_col')} by {comp_results.get('metric_col')})",
                "status": "accepted"
            })
            insight_idx += 1
            
    # 6. Data Quality & Measurement Governance
    crit_count = qa_report.get("critical_count", 0)
    health_score = qa_report.get("health_score", 100.0)
    if crit_count > 0:
        insights.append({
            "insight_id": f"INS-{insight_idx:03d}",
            "category": "Data Governance",
            "finding": f"Data Quality scan identified {crit_count} Critical issue(s) affecting analytical certainty (Health Score: {health_score:.1f}/100).",
            "evidence": f"Detected anomalies in data validity, missing values, or inventory reconciliation checks.",
            "interpretation": "Data hygiene gaps create risks of false precision in metric reporting and distorted performance comparisons.",
            "business_implication": "Operational decisions based on unverified reporting data risk misallocating resource capacity.",
            "recommendation": "Improve reporting controls, resolve source system reconciliation discrepancies, and validate input captures.",
            "limitation": "Quality engine flags structural and statistical anomalies; domain context is required to verify operational root causes.",
            "traceable_metric": "Data Quality Audit Scan",
            "status": "accepted"
        })
        insight_idx += 1
        
    return insights


from src.metrics import calculate_kpis, TargetDirection


def generate_rule_based_insights(
    df: pd.DataFrame,
    mappings: Dict[str, str],
    target_directions: Optional[Dict[str, str]] = None,
    granularity: str = "Case / record"
) -> List[Dict[str, Any]]:
    """Helper that computes KPIs and generates structured insight cards with status tracking."""
    if df is None or not mappings:
        return []
        
    primary_dir = "higher_is_better"
    if target_directions:
        for d in target_directions.values():
            if d:
                primary_dir = d
                break
                
    kpi_res = calculate_kpis(df, mappings, target_direction=primary_dir)
    raw_insights = generate_insights(kpi_res, qa_report={})
    
    formatted_insights = []
    for item in raw_insights:
        formatted_insights.append({
            "id": item.get("insight_id", f"ins_{len(formatted_insights)+1}"),
            "title": f"{item.get('category', 'Diagnostic')} - {item.get('finding', '')[:40]}...",
            "category": item.get("category", "General"),
            "finding": item.get("finding", ""),
            "evidence": item.get("evidence", ""),
            "interpretation": item.get("interpretation", ""),
            "business_implication": item.get("business_implication", ""),
            "recommendation": item.get("recommendation", ""),
            "limitation": item.get("limitation", ""),
            "severity": "high" if "shortfall" in item.get("finding", "").lower() or "exceeding" in item.get("finding", "").lower() else "medium",
            "status": "approved"
        })
        
    # If no rule triggered, add a standard baseline insight
    if not formatted_insights and len(df) > 0:
        formatted_insights.append({
            "id": "ins_base_001",
            "title": "Baseline Data Distribution Profile",
            "category": "Data Profile",
            "finding": f"Dataset contains {len(df):,} operational {granularity.lower()} entries across {len(df.columns)} mapped/unmapped attributes.",
            "evidence": f"Total records: {len(df):,}.",
            "interpretation": "Baseline volume ready for detailed drilldown.",
            "business_implication": "Enables performance monitoring and cohort benchmarking.",
            "recommendation": "Track throughput trends and SLA variance over time.",
            "limitation": f"Analysis unit established as: 1 row = {granularity}.",
            "severity": "info",
            "status": "approved"
        })
        
    return formatted_insights
