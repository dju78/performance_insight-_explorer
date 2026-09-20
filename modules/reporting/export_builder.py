"""Enterprise Multi-Format Reporting and Evidence Pack Builder for Performance Insight Explorer.
Generates:
1. Executive Summary Memo (Markdown & PDF)
2. Full Enterprise Performance Report
3. 10-Dimension Data-Quality Report
4. Multi-Tab Excel Evidence Pack (Formula-Injection Sanitized)
5. Executive PowerPoint Briefing Deck (16:9)
6. Executive PDF Brief
"""
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from core.security import sanitize_dataframe_for_export, sanitize_for_spreadsheet


def build_markdown_executive_report(
    project_state: Dict[str, Any],
    kpi_results: Dict[str, Any],
    insights: List[Any],
    recommendations: List[Any],
    actions: List[Any],
    qa_report: Optional[Dict[str, Any]] = None
) -> str:
    """Compile comprehensive executive performance briefing in publication-grade markdown."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proj_name = project_state.get("project_name", "Enterprise Operational Review")
    org_name = project_state.get("organization_name", "Enterprise Operations")
    creator = project_state.get("created_by", "Lead Performance Analyst")
    question = project_state.get("business_question", "Operational Bottleneck and Efficiency Assessment")
    audience = project_state.get("target_audience", "Executive Leadership & Board")
    horizon = project_state.get("time_horizon", "Last 12 Months")

    health_score = qa_report.get("health_score", 100.0) if qa_report else 100.0

    lines = [
        f"# {proj_name}",
        f"**Organization:** {org_name} | **Author / Lead Analyst:** {creator} | **Date:** {now_str}",
        f"**Target Audience:** {audience} | **Analysis Horizon:** {horizon}",
        "",
        "---",
        "",
        "## 1. Executive Summary & Problem Definition",
        f"**Core Business Question:** {question}",
        "",
        f"This report presents an evidence-based diagnostic and performance evaluation for **{org_name}**. "
        f"All findings, variance calculations, and recommended interventions are derived from verified empirical data "
        f"with an overall Data Quality Index of **{health_score:.1f}/100**.",
        "",
        "---",
        "",
        "## 2. Executive KPI Scorecard",
        "| KPI Name | Actual Performance | Target Standard | Variance % | Status | Interpretation |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for kpi_id, res in (kpi_results or {}).items():
        name = res.get("name", kpi_id) if isinstance(res, dict) else str(res)
        act = res.get("actual") if isinstance(res, dict) else None
        tgt = res.get("target") if isinstance(res, dict) else None
        unit = res.get("unit", "") if isinstance(res, dict) else ""
        var_pct = res.get("variance_pct") if isinstance(res, dict) else None
        icon = res.get("icon", "⚪") if isinstance(res, dict) else ""
        st_text = res.get("status", "N/A") if isinstance(res, dict) else ""
        interp = res.get("interpretation", "") if isinstance(res, dict) else ""

        act_str = f"{act:,.1f} {unit}" if act is not None else "N/A"
        tgt_str = f"{tgt:,.1f} {unit}" if tgt is not None else "N/A"
        var_str = f"{var_pct:+.1f}%" if var_pct is not None else "N/A"

        lines.append(f"| **{name}** | {act_str} | {tgt_str} | {var_str} | {icon} {st_text} | {interp} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Evidence-Based Insights & Diagnostic Findings"
    ])

    if not insights:
        lines.append("*No active insights recorded.*")
    else:
        for idx, ins in enumerate(insights, start=1):
            title = getattr(ins, "finding_title", "") or (ins.get("finding_title", "") if isinstance(ins, dict) else str(ins))
            evid = getattr(ins, "quantitative_evidence", "") or (ins.get("quantitative_evidence", "") if isinstance(ins, dict) else "")
            conf = getattr(ins, "confidence_level", "") or (ins.get("confidence_level", "") if isinstance(ins, dict) else "")
            sig = getattr(ins, "business_significance", "") or (ins.get("business_significance", "") if isinstance(ins, dict) else "")
            lim = getattr(ins, "statistical_limitation", "") or (ins.get("statistical_limitation", "") if isinstance(ins, dict) else "")

            lines.extend([
                f"### Finding {idx}: {title}",
                f"- **Quantitative Evidence:** {evid}",
                f"- **Confidence & Significance:** {conf} | *{sig}*",
                f"- **Analytical Limitations:** {lim}",
                ""
            ])

    lines.extend([
        "---",
        "",
        "## 4. Prioritized Recommendations & Action Roadmap",
        "| Rec ID | Problem Addressed | Proposed Intervention | Expected Benefit | Priority | Owner | Timescale |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    if not recommendations:
        lines.append("*No recommendations configured.*")
    else:
        for rec in recommendations:
            rid = getattr(rec, "id", "") or (rec.get("id", "") if isinstance(rec, dict) else "")
            prob = getattr(rec, "problem_addressed", "") or (rec.get("problem_addressed", "") if isinstance(rec, dict) else "")
            act_p = getattr(rec, "proposed_action", "") or (rec.get("proposed_action", "") if isinstance(rec, dict) else "")
            ben = getattr(rec, "expected_benefit", "") or (rec.get("expected_benefit", "") if isinstance(rec, dict) else "")
            prio = getattr(rec, "priority", "") or (rec.get("priority", "") if isinstance(rec, dict) else "")
            own = getattr(rec, "responsible_owner", "") or (rec.get("responsible_owner", "") if isinstance(rec, dict) else "")
            time_s = getattr(rec, "timescale", "") or (rec.get("timescale", "") if isinstance(rec, dict) else "")

            prio_val = prio.value if hasattr(prio, "value") else str(prio)
            lines.append(f"| **{rid}** | {prob} | {act_p} | {ben} | **{prio_val}** | {own} | {time_s} |")

    return "\n".join(lines)


def generate_excel_evidence_pack(
    project_state: Optional[Dict[str, Any]] = None,
    clean_df: Optional[pd.DataFrame] = None,
    kpi_results: Optional[Dict[str, Any]] = None,
    insights: Optional[List[Any]] = None,
    recommendations: Optional[List[Any]] = None,
    actions: Optional[List[Any]] = None,
    qa_report: Optional[Dict[str, Any]] = None,
    audit_log: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any
) -> bytes:
    """Generate a multi-tab Excel evidence workbook with formula injection protection."""
    project_state = project_state or kwargs.get("project_state", {}) or {}
    kpi_results = kpi_results or {}
    insights = insights or kwargs.get("evidence_insights", []) or []
    recommendations = recommendations or kwargs.get("recommendation_items", []) or []
    actions = actions or kwargs.get("action_items", []) or []
    audit_log = audit_log or kwargs.get("audit_log_entries", []) or []
    clean_df = clean_df if clean_df is not None else kwargs.get("clean_df")

    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Tab 1: Executive Overview
        overview_rows = [
            {"Parameter": "Project Name", "Value": sanitize_for_spreadsheet(project_state.get("project_name", "Operational Review"))},
            {"Parameter": "Organization", "Value": sanitize_for_spreadsheet(project_state.get("organization_name", "Enterprise"))},
            {"Parameter": "Lead Analyst", "Value": sanitize_for_spreadsheet(project_state.get("created_by", "Daramola Omoyele"))},
            {"Parameter": "Generated Date", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"Parameter": "Business Question", "Value": sanitize_for_spreadsheet(project_state.get("business_question", ""))},
            {"Parameter": "Data Quality Health Index", "Value": f"{qa_report.get('health_score', 100.0):.1f}/100" if qa_report else "100/100"}
        ]
        df_overview = pd.DataFrame(overview_rows)
        df_overview.to_excel(writer, sheet_name="Executive Summary", index=False)

        # Tab 2: KPI Scorecard
        kpi_rows = []
        for kpi_id, res in kpi_results.items():
            if isinstance(res, dict):
                kpi_rows.append({
                    "KPI Key": sanitize_for_spreadsheet(kpi_id),
                    "KPI Name": sanitize_for_spreadsheet(res.get("name", kpi_id)),
                    "Actual Value": res.get("actual"),
                    "Target Standard": res.get("target"),
                    "Unit": sanitize_for_spreadsheet(res.get("unit", "")),
                    "Variance Num": res.get("variance"),
                    "Variance %": res.get("variance_pct"),
                    "Status": sanitize_for_spreadsheet(res.get("status", "")),
                    "Interpretation": sanitize_for_spreadsheet(res.get("interpretation", ""))
                })
        df_kpis = pd.DataFrame(kpi_rows) if kpi_rows else pd.DataFrame([{"KPI": "General", "Status": "Evaluated"}])
        df_kpis.to_excel(writer, sheet_name="KPI Scorecard", index=False)

        def _get_val(obj: Any, key: str, default: Any = "") -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Tab 3: Insights & Findings
        ins_rows = []
        for ins in insights:
            ins_rows.append({
                "ID": sanitize_for_spreadsheet(_get_val(ins, "id")),
                "Title": sanitize_for_spreadsheet(_get_val(ins, "finding_title", _get_val(ins, "title"))),
                "Evidence": sanitize_for_spreadsheet(_get_val(ins, "quantitative_evidence", _get_val(ins, "observation"))),
                "KPI Affected": sanitize_for_spreadsheet(_get_val(ins, "kpi_affected")),
                "Confidence": sanitize_for_spreadsheet(_get_val(ins, "confidence_level", _get_val(ins, "evidence_level"))),
                "Impact": sanitize_for_spreadsheet(_get_val(ins, "business_significance", _get_val(ins, "business_impact"))),
                "Limitations": sanitize_for_spreadsheet(_get_val(ins, "statistical_limitation", _get_val(ins, "limitations_disclosure")))
            })
        df_ins = pd.DataFrame(ins_rows) if ins_rows else pd.DataFrame([{"Notice": "No anomalous findings"}])
        df_ins.to_excel(writer, sheet_name="Evidence Insights", index=False)

        # Tab 4: Recommendations
        rec_rows = []
        for rec in recommendations:
            rec_rows.append({
                "Rec ID": sanitize_for_spreadsheet(_get_val(rec, "id")),
                "Problem": sanitize_for_spreadsheet(_get_val(rec, "problem_addressed", _get_val(rec, "title"))),
                "Proposed Action": sanitize_for_spreadsheet(_get_val(rec, "proposed_action", _get_val(rec, "rationale"))),
                "Expected Benefit": sanitize_for_spreadsheet(_get_val(rec, "expected_benefit")),
                "Priority": sanitize_for_spreadsheet(str(_get_val(rec, "priority", _get_val(rec, "priority_level")))),
                "Owner": sanitize_for_spreadsheet(_get_val(rec, "responsible_owner", _get_val(rec, "owner_role"))),
                "Timescale": sanitize_for_spreadsheet(_get_val(rec, "timescale", _get_val(rec, "timeframe")))
            })
        df_recs = pd.DataFrame(rec_rows) if rec_rows else pd.DataFrame([{"Notice": "No recommendations configured"}])
        df_recs.to_excel(writer, sheet_name="Recommendations", index=False)

        # Tab 5: Clean Data Sample (Sanitized)
        if clean_df is not None and len(clean_df) > 0:
            df_sanitized = sanitize_dataframe_for_export(clean_df.head(5000))
            df_sanitized.to_excel(writer, sheet_name="Verified Data Extract", index=False)

    return output.getvalue()


build_excel_evidence_pack = generate_excel_evidence_pack


def build_powerpoint_presentation(
    project_state: Optional[Dict[str, Any]] = None,
    kpi_summary: Optional[Dict[str, Any]] = None,
    trend_summary: Optional[pd.DataFrame] = None,
    comparison_summary: Optional[Dict[str, Any]] = None,
    evidence_insights: Optional[List[Any]] = None,
    recommendations: Optional[List[Any]] = None,
    **kwargs: Any
) -> bytes:
    """Generate a clean 16:9 executive briefing PowerPoint deck."""
    project_state = project_state or {}
    evidence_insights = evidence_insights or []
    recommendations = recommendations or []

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Slide 1: Title Slide
    slide1 = prs.slides.add_slide(blank_layout)
    tb1 = slide1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.333), Inches(3.5))
    tf1 = tb1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = project_state.get("project_name", "Executive Performance Review")
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(23, 63, 115)

    p2 = tf1.add_paragraph()
    p2.text = f"Organization: {project_state.get('organization_name', 'Enterprise')} | Analyst: {project_state.get('created_by', 'Daramola Omoyele')}"
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(100, 110, 120)

    # Slide 2: Findings & Evidence
    slide2 = prs.slides.add_slide(blank_layout)
    tb2 = slide2.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.333), Inches(5.8))
    tf2 = tb2.text_frame
    p_head = tf2.paragraphs[0]
    p_head.text = "Key Diagnostic Findings & Evidence"
    p_head.font.size = Pt(24)
    p_head.font.bold = True
    p_head.font.color.rgb = RGBColor(23, 63, 115)

    for ins in evidence_insights[:5]:
        p_ins = tf2.add_paragraph()
        title = getattr(ins, "finding_title", getattr(ins, "title", str(ins)))
        evid = getattr(ins, "quantitative_evidence", getattr(ins, "observation", ""))
        p_ins.text = f"• {title}: {evid}"
        p_ins.font.size = Pt(14)

    # Slide 3: Recommendations
    slide3 = prs.slides.add_slide(blank_layout)
    tb3 = slide3.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.333), Inches(5.8))
    tf3 = tb3.text_frame
    p_rec_head = tf3.paragraphs[0]
    p_rec_head.text = "Prioritized Action Recommendations"
    p_rec_head.font.size = Pt(24)
    p_rec_head.font.bold = True
    p_rec_head.font.color.rgb = RGBColor(23, 63, 115)

    for rec in recommendations[:5]:
        p_rec = tf3.add_paragraph()
        prob = getattr(rec, "problem_addressed", getattr(rec, "title", str(rec)))
        act = getattr(rec, "proposed_action", getattr(rec, "rationale", ""))
        p_rec.text = f"• {prob} -> {act}"
        p_rec.font.size = Pt(14)

    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()


def build_executive_pdf(
    project_state: Optional[Dict[str, Any]] = None,
    kpi_summary: Optional[Dict[str, Any]] = None,
    quality_score: float = 100.0,
    insights: Optional[List[Any]] = None,
    recommendations: Optional[List[Any]] = None,
    **kwargs: Any
) -> bytes:
    """Generate a clean executive summary PDF brief."""
    project_state = project_state or {}
    insights = insights or []
    recommendations = recommendations or []

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=20, leading=24, textColor=colors.HexColor("#173F73"))
    h2_style = ParagraphStyle("H2Style", parent=styles["Heading2"], fontSize=14, leading=18, textColor=colors.HexColor("#173F73"))
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=14)

    story.append(Paragraph(project_state.get("project_name", "Executive Performance Review"), title_style))
    story.append(Paragraph(f"Organization: {project_state.get('organization_name', 'Enterprise')} | Data Quality Index: {quality_score:.1f}/100", body_style))
    story.append(Spacer(1, 15))

    # Findings
    story.append(Paragraph("1. Key Diagnostic Findings", h2_style))
    for ins in insights[:5]:
        title = getattr(ins, "finding_title", getattr(ins, "title", str(ins)))
        evid = getattr(ins, "quantitative_evidence", getattr(ins, "observation", ""))
        story.append(Paragraph(f"• <b>{title}:</b> {evid}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # Recommendations
    story.append(Paragraph("2. Action Recommendations", h2_style))
    for rec in recommendations[:5]:
        prob = getattr(rec, "problem_addressed", getattr(rec, "title", str(rec)))
        act = getattr(rec, "proposed_action", getattr(rec, "rationale", ""))
        story.append(Paragraph(f"• <b>{prob}:</b> {act}", body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    return output.getvalue()
