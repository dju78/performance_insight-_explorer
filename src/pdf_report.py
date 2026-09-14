"""PDF Report Generation Engine for Performance Insight Explorer.
Generates publication-ready A4 executive briefs, operational memos, and technical audit reports using ReportLab Platypus.
"""
import os
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Palette
C_PRIMARY = colors.HexColor("#1E3A8A")     # Deep Navy
C_SECONDARY = colors.HexColor("#0284C7")   # Sky Blue
C_DARK = colors.HexColor("#1F2937")        # Charcoal
C_LIGHT_BG = colors.HexColor("#F3F4F6")    # Light Gray
C_WARN = colors.HexColor("#D97706")        # Amber
C_CRIT = colors.HexColor("#DC2626")        # Red
C_MUTED = colors.HexColor("#6B7280")       # Slate


class NumberedCanvas(canvas.Canvas):
    """Canvas that enables two-pass 'Page X of Y' dynamic footers and headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        # Top rule and header
        self.setFont("Helvetica", 8)
        self.setFillColor(C_MUTED)
        self.drawString(40, 810, "Performance Insight Explorer — Operational Analytics Report")
        self.drawRightString(555, 810, datetime.datetime.now().strftime("%d %B %Y"))
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(40, 804, 555, 804)
        
        # Bottom rule and footer
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, "Author: DARAMOLA OMOYELE | Performance Insight Explorer")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 32, page_text)
        self.restoreState()


def generate_pdf_document(
    output_filepath: str,
    payload: Dict[str, Any],
    audience: str = "Senior Leadership"
) -> str:
    """Build audience-adapted A4 PDF document."""
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True) if os.path.dirname(output_filepath) else None
    
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=C_PRIMARY,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=C_MUTED,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=C_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=C_DARK,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=C_DARK
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=C_DARK
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    story = []
    
    ctx = payload.get("assessment_context", {})
    q_text = ctx.get("question") or "Operational Performance & Capacity Analysis"
    aud_text = audience or ctx.get("audience", "Senior Leadership")
    notes_text = ctx.get("analyst_notes", "")
    
    # 1. Header Title & Metadata Banner
    story.append(Paragraph("Performance Insight Explorer", title_style))
    story.append(Paragraph(f"Executive Operational Briefing | Target Audience: <b>{aud_text}</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceBefore=0, spaceAfter=10))
    
    # Context Box Table
    meta_table_data = [
        [
            Paragraph("<b>Assessment Objective:</b>", table_header),
            Paragraph(q_text, ParagraphStyle('H1w', parent=table_cell, textColor=colors.white))
        ],
        [
            Paragraph("<b>Dataset & Scope:</b>", table_cell),
            Paragraph(f"<b>File:</b> {payload.get('filename', 'N/A')} | <b>Sheet:</b> {payload.get('active_sheet', 'N/A')} | <b>Volume:</b> {payload.get('row_count', 0):,} rows × {payload.get('column_count', 0)} columns", table_cell)
        ],
        [
            Paragraph("<b>Unit of Analysis:</b>", table_cell),
            Paragraph(f"1 Row = <b>{payload.get('row_granularity', 'Not Confirmed')}</b> | <b>Fingerprint:</b> <code>{payload.get('dataset_fingerprint', 'N/A')}</code>", table_cell)
        ]
    ]
    if notes_text:
        meta_table_data.append([
            Paragraph("<b>Analyst Context:</b>", table_cell),
            Paragraph(notes_text, table_cell)
        ])
        
    t_meta = Table(meta_table_data, colWidths=[120, 395])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), C_PRIMARY),
        ('BACKGROUND', (0, 1), (-1, -1), C_LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))
    
    # 2. Data Quality & Integrity Section
    story.append(Paragraph("1. Data Quality & Verification Audit", h1_style))
    qa = payload.get("qa_report", {})
    score = qa.get("health_score", 100.0)
    crit = qa.get("critical_count", 0)
    warn = qa.get("warning_count", 0)
    
    qa_summary_text = (
        f"The dataset underwent automated two-stage quality scanning (Structural Data Hygiene & Semantic Business Logic). "
        f"<b>Overall Data Health Score: {score:.1f} / 100</b> ({crit} Critical blockers, {warn} Warnings). "
        "Original source observations are preserved without destructive alteration."
    )
    story.append(Paragraph(qa_summary_text, body_style))
    
    qa_issues = qa.get("issues", [])
    if qa_issues:
        qa_rows = [[
            Paragraph("<b>ID</b>", table_header),
            Paragraph("<b>Severity</b>", table_header),
            Paragraph("<b>Dimension / Field</b>", table_header),
            Paragraph("<b>Description & Verification Context</b>", table_header)
        ]]
        for iss in qa_issues[:6]:
            sev_color = C_CRIT if iss.get("severity") == "Critical" else (C_WARN if iss.get("severity") == "Warning" else C_MUTED)
            qa_rows.append([
                Paragraph(str(iss.get("issue_id", "QA")), table_cell),
                Paragraph(f"<b>{iss.get('severity', 'Info')}</b>", ParagraphStyle('Sev', parent=table_cell, textColor=sev_color)),
                Paragraph(f"{iss.get('dimension', 'General')}<br/><i>{iss.get('field', 'All')}</i>", table_cell),
                Paragraph(f"{iss.get('description', '')}", table_cell)
            ])
        t_qa = Table(qa_rows, colWidths=[45, 55, 115, 300])
        t_qa.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LIGHT_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(t_qa)
    else:
        story.append(Paragraph("✅ <i>No data quality exceptions or anomalies detected. All structural checks passed cleanly.</i>", callout_style))
    story.append(Spacer(1, 10))
    
    # 3. Performance Overview & Headline KPIs
    story.append(Paragraph("2. Operational Performance & Headline KPIs", h1_style))
    kpi_dict = payload.get("kpi_results", {}).get("summary_kpis", {})
    if kpi_dict:
        kpi_rows = [[
            Paragraph("<b>Key Performance Indicator</b>", table_header),
            Paragraph("<b>Observed Result</b>", table_header),
            Paragraph("<b>Formula & Governing Interpretation</b>", table_header)
        ]]
        for k_key, k_val in kpi_dict.items():
            val_str = f"{k_val.get('value'):,.2f} {k_val.get('unit', '')}" if k_val.get('value') is not None else "N/A"
            est_tag = " <font color='#D97706'>[EST]</font>" if k_val.get('is_estimated') else ""
            kpi_rows.append([
                Paragraph(f"<b>{k_val.get('name', k_key)}</b>{est_tag}", table_cell),
                Paragraph(f"<b>{val_str}</b>", table_cell),
                Paragraph(f"<code>{k_val.get('formula', 'Formula N/A')}</code><br/>{k_val.get('interpretation', '')}", table_cell)
            ])
        t_kpi = Table(kpi_rows, colWidths=[130, 95, 290])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LIGHT_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(t_kpi)
    else:
        story.append(Paragraph("<i>No calculated KPIs available for this dataset mapping.</i>", callout_style))
    story.append(Spacer(1, 10))
    
    # 4. Trend Dynamics & Segment Comparisons
    story.append(Paragraph("3. Trends & Operational Segment Comparisons", h1_style))
    tr = payload.get("trend_summary")
    cmp = payload.get("comparison_summary")
    
    trend_text = []
    if tr and not tr.get("error"):
        trend_text.append(
            f"<b>Time-Series Trajectory ({tr.get('trajectory_class', 'Observed')}):</b> "
            f"Metric <code>{tr.get('metric_name', 'Value')}</code> recorded a net change of <b>{tr.get('net_change', 0):+,.2f} ({tr.get('net_pct_change', 0):+,.1f}%)</b> across {tr.get('period_count', 0)} periods. "
            f"Peak observed at <b>{tr.get('peak', {}).get('period', 'N/A')}</b> ({tr.get('peak', {}).get('value', 0):,.2f}); trough at <b>{tr.get('trough', {}).get('period', 'N/A')}</b> ({tr.get('trough', {}).get('value', 0):,.2f})."
        )
    else:
        trend_text.append("<i>Trend analysis was not executed or not applicable for this dataset.</i>")
        
    if cmp and not cmp.get("error"):
        var_spread = f"{cmp.get('variance_ratio'):.2f}x" if cmp.get("variance_ratio") else "N/A"
        trend_text.append(
            f"<b>Operational Cohort Comparison ({cmp.get('group_col', 'Segment')}):</b> "
            f"Ranked {cmp.get('group_count', 0)} operational units on <code>{cmp.get('metric_col', 'Metric')}</code> (Agg: {cmp.get('aggregation', 'sum')}). "
            f"Top unit: <b>{cmp.get('top_group', 'N/A')}</b> ({cmp.get('top_value', 0):,.2f}); Lowest unit: <b>{cmp.get('bottom_group', 'N/A')}</b> ({cmp.get('bottom_value', 0):,.2f}). "
            f"Variance spread (Max / Min): <b>{var_spread}</b>."
        )
        if cmp.get("small_sample_groups"):
            trend_text.append(f"⚠️ <i>Small-sample caution: Units {cmp['small_sample_groups']} contain &lt;5 records.</i>")
    else:
        trend_text.append("<i>Group comparison was not executed or not applicable for this dataset.</i>")
        
    for tt in trend_text:
        story.append(Paragraph(tt, body_style))
    story.append(Spacer(1, 10))
    
    # 5. Analyst-Approved Insights (Strict Governance)
    story.append(Paragraph("4. Analyst-Approved Operational Insights", h1_style))
    insights = payload.get("approved_insights", [])
    if insights:
        ins_rows = [[
            Paragraph("<b>Category / Metric</b>", table_header),
            Paragraph("<b>Validated Finding</b>", table_header),
            Paragraph("<b>Underlying Evidence & Business Implication</b>", table_header)
        ]]
        for ins in insights[:5]:
            title_part = f"<b>{ins.get('title')}</b><br/>" if ins.get('title') else ""
            finding_text = f"{title_part}{ins.get('finding', '')}"
            ins_rows.append([
                Paragraph(f"<b>{ins.get('category', ins.get('pillar', 'Finding'))}</b><br/><i>{ins.get('traceable_metric', '')}</i>", table_cell),
                Paragraph(finding_text, table_cell),
                Paragraph(f"<b>Evidence:</b> {ins.get('evidence', '')}<br/><b>Implication:</b> {ins.get('business_implication', '')}", table_cell)
            ])
        t_ins = Table(ins_rows, colWidths=[110, 165, 240])
        t_ins.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LIGHT_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(t_ins)
    else:
        story.append(Paragraph("<i>No analyst-approved findings available. (Unreviewed/pending findings excluded in accordance with analytical governance).</i>", callout_style))
    story.append(Spacer(1, 10))
    
    # 6. Action Plan & Governed Recommendations
    story.append(Paragraph("5. Recommendations & Operational Action Plan", h1_style))
    recs_by_cat = payload.get("recommendations_by_category", {})
    has_any_recs = any(len(v) > 0 for v in recs_by_cat.values())
    
    if has_any_recs:
        rec_rows = [[
            Paragraph("<b>Category</b>", table_header),
            Paragraph("<b>Action Title & Description</b>", table_header),
            Paragraph("<b>Owner / Horizon</b>", table_header),
            Paragraph("<b>Expected Impact & Rationale</b>", table_header)
        ]]
        for cat in ["Act", "Investigate", "Monitor", "Improve Reporting"]:
            for r in recs_by_cat.get(cat, []):
                rec_rows.append([
                    Paragraph(f"<b>{cat}</b>", table_cell),
                    Paragraph(f"<b>{r.get('title', '')}</b><br/>{r.get('action', r.get('recommendation', ''))}", table_cell),
                    Paragraph(f"<b>Owner:</b> {r.get('owner', 'Operations Lead')}<br/><b>Timeline:</b> {r.get('timeline', 'Immediate')}", table_cell),
                    Paragraph(f"{r.get('expected_impact', 'Analyst-monitored improvement')}<br/><i>Based on {r.get('linked_insight_id', 'Approved Finding')}</i>", table_cell)
                ])
        t_rec = Table(rec_rows, colWidths=[65, 185, 105, 160])
        t_rec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LIGHT_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(t_rec)
    else:
        story.append(Paragraph("<i>No analyst-approved recommendations available. Approve findings on Page 08 to generate evidence-backed actions.</i>", callout_style))
    story.append(Spacer(1, 10))
    
    # 7. Assumptions & Limitations Governance Registers
    story.append(Paragraph("6. Governance Registers: Assumptions & Limitations", h1_style))
    assump = payload.get("assumptions", [])
    limits = payload.get("limitations", [])
    
    reg_text = []
    if assump:
        reg_text.append("<b>Operational Assumptions:</b>")
        for a in assump[:3]:
            if isinstance(a, dict):
                reg_text.append(f"  • <b>{a.get('area', 'General')}:</b> {a.get('assumption', a.get('description', ''))}")
            else:
                reg_text.append(f"  • {str(a)}")
    else:
        reg_text.append("<b>Operational Assumptions:</b> Standard continuous service operations assumed.")
        
    if limits:
        reg_text.append("<b>Methodological Limitations & Mitigations:</b>")
        for l in limits[:3]:
            if isinstance(l, dict):
                reg_text.append(f"  • <b>{l.get('area', 'Scope')}:</b> {l.get('limitation', l.get('description', ''))} <i>(Mitigation: {l.get('mitigation', 'Analyst review')})</i>")
            else:
                reg_text.append(f"  • {str(l)}")
    else:
        reg_text.append("<b>Methodological Limitations:</b> No critical analytical limitations recorded.")
        
    for rt in reg_text:
        story.append(Paragraph(rt, body_style))
        
    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_filepath

def generate_pdf_report(
    payload_or_filepath: Any,
    payload: Optional[Dict[str, Any]] = None,
    audience: str = "Senior Leadership",
    output_filepath: Optional[str] = None
) -> bytes:
    """
    Flexible wrapper for PDF generation. Accepts (payload) or (filepath, payload).
    Returns raw PDF bytes for downloads and test validation.
    """
    if isinstance(payload_or_filepath, dict):
        p = payload_or_filepath
        out_path = output_filepath or "exports/assessment_executive_report.pdf"
    else:
        out_path = payload_or_filepath
        p = payload or {}
        
    generate_pdf_document(out_path, p, audience=audience)
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            return f.read()
    return b""

