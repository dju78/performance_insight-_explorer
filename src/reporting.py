"""Reporting & Export Engine for Performance Insight Explorer.
Generates comprehensive multi-tab Excel summary workbooks and CSV analytical tables.
"""
import datetime
import os
from typing import Dict, Any, List, Optional
import pandas as pd


def generate_excel_summary(
    output_filepath: str,
    raw_df: pd.DataFrame,
    profile_info: Dict[str, Any],
    qa_report: Dict[str, Any],
    kpi_results: Dict[str, Any],
    trend_df: Optional[pd.DataFrame],
    comp_df: Optional[pd.DataFrame],
    insights: List[Dict[str, Any]],
    recommendations: Dict[str, List[Dict[str, str]]],
    assumptions_df: pd.DataFrame,
    limitations_df: pd.DataFrame,
    audit_df: pd.DataFrame
) -> str:
    """Build a professionally formatted, multi-worksheet Excel summary workbook."""
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True) if os.path.dirname(output_filepath) else None
    
    with pd.ExcelWriter(output_filepath, engine="openpyxl") as writer:
        # 1. Executive Summary Tab
        summary_rows = [
            {"Item": "Project Name", "Value": "Performance Insight Explorer"},
            {"Item": "Author", "Value": "DARAMOLA OMOYELE"},
            {"Item": "Generated Date", "Value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"Item": "Source File", "Value": profile_info.get("filename", "N/A")},
            {"Item": "Active Worksheet", "Value": profile_info.get("sheet_name", "N/A")},
            {"Item": "Total Records", "Value": profile_info.get("row_count", 0)},
            {"Item": "Total Columns", "Value": profile_info.get("column_count", 0)},
            {"Item": "Data Health Score", "Value": f"{qa_report.get('health_score', 100):.1f} / 100"},
            {"Item": "Critical Issues", "Value": qa_report.get("critical_count", 0)},
            {"Item": "Warning Issues", "Value": qa_report.get("warning_count", 0)}
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Executive_Summary", index=False)
        
        # 2. Data Quality Tab
        issues = qa_report.get("issues", [])
        if issues:
            qa_rows = []
            for iss in issues:
                qa_rows.append({
                    "Issue_ID": iss.get("issue_id"),
                    "Dimension": iss.get("dimension"),
                    "Severity": iss.get("severity"),
                    "Title": iss.get("title"),
                    "Field": iss.get("field"),
                    "Affected_Count": iss.get("affected_count"),
                    "Affected_Pct": iss.get("affected_pct"),
                    "Description": iss.get("description"),
                    "Action": iss.get("recommended_action"),
                    "Status": iss.get("status")
                })
            pd.DataFrame(qa_rows).to_excel(writer, sheet_name="Data_Quality_Audit", index=False)
            
        # 3. KPI Summary Tab
        kpis = kpi_results.get("summary_kpis", {})
        if kpis:
            kpi_rows = []
            for k, v in kpis.items():
                kpi_rows.append({
                    "Metric_Key": k,
                    "Name": v.get("name"),
                    "Value": v.get("value"),
                    "Unit": v.get("unit"),
                    "Is_Estimated": v.get("is_estimated"),
                    "Formula": v.get("formula"),
                    "Description": v.get("description"),
                    "Interpretation": v.get("interpretation")
                })
            pd.DataFrame(kpi_rows).to_excel(writer, sheet_name="Headline_KPIs", index=False)
            
        # 4. Trend Analysis Tab
        if trend_df is not None and len(trend_df) > 0:
            trend_df.to_excel(writer, sheet_name="Trend_Analysis", index=False)
            
        # 5. Group Comparison Tab
        if comp_df is not None and len(comp_df) > 0:
            comp_df.to_excel(writer, sheet_name="Group_Comparisons", index=False)
            
        # 6. Structured Insights Tab
        if insights:
            ins_rows = []
            for ins in insights:
                ins_rows.append({
                    "ID": ins.get("insight_id"),
                    "Category": ins.get("category"),
                    "Finding": ins.get("finding"),
                    "Evidence": ins.get("evidence"),
                    "Interpretation": ins.get("interpretation"),
                    "Business_Implication": ins.get("business_implication"),
                    "Recommendation": ins.get("recommendation"),
                    "Limitation": ins.get("limitation"),
                    "Traceable_Metric": ins.get("traceable_metric")
                })
            pd.DataFrame(ins_rows).to_excel(writer, sheet_name="Insights", index=False)
            
        # 7. Assumptions & Limitations Tab
        if not assumptions_df.empty:
            assumptions_df.to_excel(writer, sheet_name="Assumptions_Register", index=False)
        if not limitations_df.empty:
            limitations_df.to_excel(writer, sheet_name="Limitations_Register", index=False)
            
        # 8. Audit Trail Tab
        if not audit_df.empty:
            audit_df.to_excel(writer, sheet_name="Audit_Trail", index=False)
            
    return output_filepath
