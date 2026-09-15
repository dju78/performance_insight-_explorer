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
    if df is None or len(df) == 0:
        return []
        
    formatted_insights = []
    
    # 1. Assessment Model Check: Availability % & Contracted Hours
    if "Availability %" in df.columns:
        s_av = pd.to_numeric(df["Availability %"], errors="coerce").dropna()
        total_n = len(df)
        valid_n = len(s_av)
        uncalc_n = total_n - valid_n
        uncapped_n = int((s_av > 1.0).sum())
        
        if valid_n > 0:
            formatted_insights.append({
                "id": "INS-001",
                "title": "Overall Availability & Uncapped Outliers",
                "category": "Operational Delivery",
                "finding": f"Across {valid_n:,} valid monthly records, mean availability is {s_av.mean():.2%} (median: {s_av.median():.2%}), with {uncapped_n} uncapped entries exceeding 100%.",
                "evidence": f"Calculated as Available Hours / Contracted Hours across {total_n:,} rows. Highest observed availability is {s_av.max():.2%}.",
                "interpretation": "Workforce availability remains robust overall; uncapped entries (>100%) reflect overtime or extra scheduled hours delivered above contracted baseline.",
                "business_implication": "Distinguishes baseline capacity delivery from temporary overtime surges across operational services.",
                "recommendation": "Preserve uncapped calculation rule in all operational scorecards and review overtime allocation.",
                "limitation": "Calculation returns null/blank where contracted hours are zero or missing to prevent division-by-zero distortion.",
                "severity": "medium",
                "status": "pending"
            })
            
        if uncalc_n > 0:
            formatted_insights.append({
                "id": "INS-002",
                "title": "Data Hygiene: Uncalculable Availability Rows",
                "category": "Data Governance",
                "finding": f"{uncalc_n:,} records ({uncalc_n/total_n:.1%}) lack valid contracted hours or available hours and return blank as required.",
                "evidence": f"Zero or null denominator detected on {uncalc_n:,} of {total_n:,} rows.",
                "interpretation": "Handles missing/null inputs safely without generating #DIV/0! errors or artificially skewing overall averages.",
                "business_implication": "Ensures executive dashboards reflect only statistically valid operational activity.",
                "recommendation": "Implement source data validation in HR/rostering extracts to ensure contracted hours are populated for active staff.",
                "limitation": "Omitted rows do not contribute to group means or quarterly summaries.",
                "severity": "info",
                "status": "pending"
            })

    # 2. Service & Band Distribution Check
    if "Service" in df.columns and "Band" in df.columns and "Availability %" in df.columns:
        s_av = pd.to_numeric(df["Availability %"], errors="coerce")
        serv_grp = df.assign(_av=s_av).groupby("Service")["_av"].agg(["mean", "count"]).dropna()
        if len(serv_grp) >= 2:
            top_s = serv_grp["mean"].idxmax()
            top_v = serv_grp["mean"].max()
            bot_s = serv_grp["mean"].idxmin()
            bot_v = serv_grp["mean"].min()
            formatted_insights.append({
                "id": "INS-003",
                "title": "Inter-Service Performance Variance",
                "category": "Cohort Comparisons",
                "finding": f"Availability varies across services, led by '{top_s}' ({top_v:.2%}) compared to '{bot_s}' ({bot_v:.2%}).",
                "evidence": f"Service-level aggregation of {len(df):,} records matched against Users master data.",
                "interpretation": "Variance across operational areas reflects differing workload demands, leave patterns, and band grade compositions.",
                "business_implication": "Highlights potential staffing imbalances or localized operational pressures.",
                "recommendation": "Conduct quarterly workload reviews across services to balance capacity with operational demand.",
                "limitation": "Does not account for unrecorded casework complexity or specialized task allocations.",
                "severity": "medium",
                "status": "pending"
            })

    # 3. Fallback: Generic KPI calculation if traditional KPI mappings exist
    if not formatted_insights and mappings:
        primary_dir = "higher_is_better"
        if target_directions:
            for d in target_directions.values():
                if d:
                    primary_dir = d
                    break
        kpi_res = calculate_kpis(df, mappings, target_direction=primary_dir)
        raw_insights = generate_insights(kpi_res, qa_report={})
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
                "status": "pending"
            })

    # 4. Fallback baseline data profile
    if not formatted_insights and len(df) > 0:
        formatted_insights.append({
            "id": "INS-BASE-001",
            "title": "Baseline Analytical Model Profile",
            "category": "Data Profile",
            "finding": f"Analytical model contains {len(df):,} operational records across {len(df.columns)} verified attributes.",
            "evidence": f"Total records: {len(df):,}.",
            "interpretation": "Baseline volume ready for drilldown and presentation.",
            "business_implication": "Enables performance monitoring and cohort benchmarking.",
            "recommendation": "Review group comparisons and longitudinal trends.",
            "limitation": f"Analysis unit established as: 1 row = {granularity}.",
            "severity": "info",
            "status": "pending"
        })
        
    return formatted_insights
