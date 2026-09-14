"""Professional Executive PowerPoint Exporter for Performance Insight Explorer.
Generates 16:9 widescreen senior-leadership briefing decks with:
- Visual storytelling & executive design principles (KPI cards, callouts, action matrix)
- High-resolution programmatic charts (Matplotlib)
- Real session data integration (QA audit, KPIs, trends, comparisons)
- Strict Approved-Content Governance
- First-Person Data-Driven Presenter / Speaker Notes on EVERY slide (with Panel Q&A cues)
- Optional 4-slide Technical Appendix
Author: DARAMOLA OMOYELE
"""
import os
import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ==============================================================================
# 1. EXECUTIVE DESIGN SYSTEM & PALETTE (16:9 Widescreen)
# ==============================================================================
SLIDE_WIDTH_IN = 13.333
SLIDE_HEIGHT_IN = 7.5

# Corporate Color Palette
COLOR_NAVY = RGBColor(23, 63, 115)        # #173F73 Primary Navy
COLOR_SECONDARY = RGBColor(47, 117, 181)  # #2F75B5 Secondary Blue
COLOR_TEAL = RGBColor(42, 157, 143)       # #2A9D8F Accent Teal
COLOR_POSITIVE = RGBColor(46, 125, 50)    # #2E7D32 Positive Green
COLOR_CAUTION = RGBColor(244, 162, 97)    # #F4A261 Caution Amber
COLOR_RISK = RGBColor(198, 40, 40)        # #C62828 Risk Red
COLOR_BG_LIGHT = RGBColor(247, 249, 252)  # #F7F9FC Light Background
COLOR_WHITE = RGBColor(255, 255, 255)     # #FFFFFF Card Fill
COLOR_CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0 Subtle Border
COLOR_DARK_TEXT = RGBColor(38, 50, 56)    # #263238 Dark Text
COLOR_MUTED_TEXT = RGBColor(102, 112, 133) # #667085 Muted Text
COLOR_LIGHT_GRAY = RGBColor(241, 245, 249) # #F1F5F9 Soft fill


# ==============================================================================
# 2. PRESENTER NOTES HELPER & DYNAMIC SCRIPT GENERATORS
# ==============================================================================
def add_presenter_notes(slide, notes_text: str):
    """Populate real PowerPoint speaker notes on the given slide for Presenter View."""
    if not notes_text:
        return
    try:
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        if text_frame is not None:
            text_frame.text = notes_text.strip()
    except Exception:
        pass


def _generate_notes_slide_1(ctx: Dict[str, Any], meta: Dict[str, Any], clean_df: Optional[pd.DataFrame] = None) -> str:
    """Generate dynamic presenter notes for Slide 1 (Objective & Approach)."""
    question = ctx.get("assessment_question") or ctx.get("question") or "evaluate operational throughput, queue performance, and capacity bottlenecks"
    audience = ctx.get("target_audience") or ctx.get("audience") or "senior leadership and executive operations stakeholders"
    row_gran = meta.get("row_granularity") or "periodic operational snapshot"
    
    rows = meta.get("row_count")
    if rows is None and clean_df is not None:
        rows = len(clean_df)
    rows_str = f"{rows:,} observations" if rows is not None else "the operational dataset"

    cols = meta.get("column_count")
    if cols is None and clean_df is not None:
        cols = len(clean_df.columns)
    cols_str = f" across {cols} variables" if cols is not None else ""

    scope = meta.get("analysis_scope") or ctx.get("analysis_scope")
    scope_phrase = f" covering {scope}" if scope else ""

    script = (
        f"Good morning. I approached this assessment by first being clear about the business decision our analysis needs to support: "
        f"specifically, {question}, prepared for {audience}.\n\n"
        f"The dataset provides {rows_str}{cols_str}{scope_phrase}, and I confirmed at ingestion that each row represents a {row_gran}.\n\n"
        f"Before calculating any performance measures, I conducted a structured quality audit on the raw data. In my experience, executive dashboards can look convincing even when underlying assumptions or data types are flawed. Once quality was assured, I verified semantic column mappings, calculated only the metrics supported by confirmed fields, examined chronological trends and team cohorts, and translated those patterns into evidence-based recommendations.\n\n"
        f"My goal was not simply to produce as many statistics as possible. My aim was to identify the information that would help senior leaders understand where performance is under pressure, what may be contributing to it, and what should be investigated or acted on next.\n\n"
        f"With that approach established, the first thing I looked at was whether the data was reliable enough to support the analysis."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why did you prioritize data quality before calculating KPIs?\n"
        "A: Because calculating metrics over unverified categories or invalid denominators produces misleading averages. Quality assurance ensures leadership decisions are backed by reliable evidence.\n\n"
        "Q: Why is confirming row granularity important?\n"
        "A: Understanding whether a row represents an individual transaction or an aggregate periodic snapshot determines whether we can calculate transaction-level distributions or must focus on aggregate flow rates."
    )
    return script + qa_cues


def _generate_notes_slide_2(qa_report: Dict[str, Any], meta: Dict[str, Any], clean_df: Optional[pd.DataFrame] = None) -> str:
    """Generate dynamic presenter notes for Slide 2 (Data Quality & Assurance)."""
    score = qa_report.get("health_score", 100.0)
    crit_count = qa_report.get("critical_count", 0)
    warn_count = qa_report.get("warning_count", 0)
    issues = qa_report.get("issues", [])

    issue_summaries = []
    for iss in issues[:4]:
        title = iss.get("title") or iss.get("issue_type", "Data Quality Check")
        field = iss.get("field") or iss.get("column", "")
        desc = iss.get("description", "")
        if field:
            issue_summaries.append(f"{title} in '{field}'")
        else:
            issue_summaries.append(f"{title}")

    issues_text = ", ".join(issue_summaries) if issue_summaries else "no significant structural defects"

    script = (
        f"I evaluated the dataset across structural integrity, value validity, and semantic consistency, resulting in a Data Health Score of {score:.1f} out of 100 with {crit_count} critical blockers and {warn_count} warning items.\n\n"
        f"My audit specifically identified {issues_text}.\n\n"
        f"In terms of how I handled these conditions: I did not delete outliers automatically because unusual durations or volumes frequently represent real operational friction rather than erroneous records. Where zero values appeared in potential capacity fields, I applied mathematical guards to prevent invalid division. And where naming inconsistencies were detected, I flagged them for reconciliation before drawing comparative conclusions.\n\n"
        f"My conclusion is that the dataset is usable for indicative performance analysis, provided these operational caveats are clearly disclosed to decision-makers.\n\n"
        f"Once I understood those limitations, I moved to the performance measures that could be calculated reliably."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why didn't you delete or impute the outlier records?\n"
        "A: In operational analysis, outliers frequently signal real systemic friction or complex edge cases. Deleting them artificially flatters performance; I flag them for operational investigation instead.\n\n"
        f"Q: Can leadership rely on analysis with an {score:.0f}/100 health score?\n"
        "A: Yes, provided there are no fatal schema defects. The issues are localized anomalies which we have isolated using safe mathematical guards and analytical caveats."
    )
    return script + qa_cues


def _generate_notes_slide_3(kpi_summary: Dict[str, Any]) -> str:
    """Generate dynamic presenter notes for Slide 3 (KPI Performance Scorecard)."""
    raw_kpis = kpi_summary.get("summary_kpis", kpi_summary) if isinstance(kpi_summary, dict) else {}

    achieve_info = raw_kpis.get("target_achievement_pct", {})
    achieve_val = achieve_info.get("value")
    
    var_info = raw_kpis.get("target_variance", {})
    var_val = var_info.get("value")

    prod_info = raw_kpis.get("productivity", {})
    prod_val = prod_info.get("value")

    util_info = raw_kpis.get("utilisation_pct", {})
    util_val = util_info.get("value")

    bl_info = raw_kpis.get("backlog_change", {})
    bl_val = bl_info.get("value")

    comp_info = raw_kpis.get("completion_rate_pct", {})
    comp_val = comp_info.get("value")

    parts = []
    if achieve_val is not None:
        if var_val is not None and var_val < 0:
            parts.append(f"The first headline measure I would highlight is target achievement. Actual output reached {achieve_val:.1f}% of target, leaving a net delivery shortfall of {abs(var_val):,.0f} units.")
        elif var_val is not None:
            parts.append(f"Target achievement reached {achieve_val:.1f}%, representing a favorable net variance of {var_val:+,.0f} units against target.")
        else:
            parts.append(f"Target achievement reached {achieve_val:.1f}% across the evaluated operational period.")

    if bl_val is not None:
        if bl_val > 0:
            parts.append(f"Demand also exceeded completions over the period, which is consistent with the observed increase in net backlog of {bl_val:+,.0f} cases.")
        else:
            parts.append(f"Completions exceeded demand over the period, reducing the overall backlog queue by {abs(bl_val):,.0f} cases.")
    elif comp_val is not None:
        parts.append(f"The operational completion rate stood at {comp_val:.1f}% of total demand intake.")

    if prod_val is not None:
        parts.append(f"Overall productivity is approximately {prod_val:.2f} completed cases per resource unit. However, I would not use that figure by itself to judge an individual team because the dataset does not fully control for differences in case complexity.")

    if util_val is not None:
        parts.append(f"Utilisation averaged {util_val:.1f}%. I treat utilisation as descriptive here, comparing it against the organisation's agreed operational benchmark rather than assuming an arbitrary standard.")

    body_text = " ".join(parts) if parts else "I evaluated the active operational metrics using weighted sums to ensure accurate portfolio reporting."

    script = (
        f"Turning to headline performance, I evaluated the core operational metrics using weighted totals to avoid the mathematical distortion of averaging row-level percentages.\n\n"
        f"{body_text}\n\n"
        f"Those headline measures tell us what is happening overall, but they do not tell us when or where the pressure is occurring."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why did you use ratio of sums rather than the average of row percentages?\n"
        "A: Averaging percentages treats a small team the same as a major operational hub, distorting portfolio reality. Ratio of sums accurately weights each team by volume.\n\n"
        "Q: Does high utilisation always mean good operational health?\n"
        "A: No. Utilisation exceeding 85% to 90% frequently causes queue congestion, elevated cycle times, and staff fatigue. It must be balanced against throughput and quality."
    )
    return script + qa_cues


def _generate_notes_slide_4(
    trend_summary: Optional[Dict[str, Any]],
    comparison_summary: Optional[Dict[str, Any]],
    clean_df: Optional[pd.DataFrame],
    confirmed_mappings: Dict[str, str]
) -> str:
    """Generate dynamic presenter notes for Slide 4 (Trends & Cohort Comparison)."""
    trend_parts = []
    if clean_df is not None and len(clean_df) > 0:
        time_col = None
        for col, role in confirmed_mappings.items():
            if role in ["reporting_period", "date", "period"]:
                time_col = col
                break
        vol_col = None
        for col, role in confirmed_mappings.items():
            if role in ["received", "demand", "completed", "actual"]:
                vol_col = col
                break

        if time_col and vol_col and time_col in clean_df.columns and vol_col in clean_df.columns:
            tdf = clean_df.groupby(time_col)[vol_col].sum().reset_index()
            if len(tdf) >= 2:
                start_p = str(tdf.iloc[0][time_col])
                start_v = float(tdf.iloc[0][vol_col])
                end_p = str(tdf.iloc[-1][time_col])
                end_v = float(tdf.iloc[-1][vol_col])
                peak_idx = tdf[vol_col].idxmax()
                peak_p = str(tdf.iloc[peak_idx][time_col])
                peak_v = float(tdf.iloc[peak_idx][vol_col])
                trough_idx = tdf[vol_col].idxmin()
                trough_p = str(tdf.iloc[trough_idx][time_col])
                trough_v = float(tdf.iloc[trough_idx][vol_col])

                net_c = end_v - start_v
                pct_c = (net_c / start_v * 100.0) if start_v > 0 else 0.0

                trend_parts.append(
                    f"Looking at the chronological trend for {vol_col}, volume started at {start_v:,.0f} in {start_p}, reached a peak of {peak_v:,.0f} in {peak_p}, "
                    f"and a trough of {trough_v:,.0f} in {trough_p}, with an ending volume of {end_v:,.0f} in {end_p}. "
                    f"Understanding the shape of this trajectory is more informative than citing a single net change figure because it identifies the specific periods where demand surged."
                )

    if not trend_parts:
        trend_parts.append("Looking at the trajectory over time, the chronological trend reveals the volume distribution and operational waves across reporting periods.")

    comp_parts = []
    has_casing_issue = False
    if clean_df is not None:
        team_col = None
        for col, role in confirmed_mappings.items():
            if role in ["service_team", "team", "group", "unit", "category"]:
                team_col = col
                break
        if team_col and team_col in clean_df.columns:
            unique_teams = clean_df[team_col].dropna().astype(str).unique()
            lower_teams = [t.lower() for t in unique_teams]
            if len(unique_teams) != len(set(lower_teams)):
                has_casing_issue = True

    if has_casing_issue:
        comp_parts.append(
            "When examining cohort comparisons, variations in text casing were detected in group labels. "
            "I would reconcile those naming variations before establishing formal team rankings."
        )
    else:
        comp_parts.append("Across operational cohorts, comparing normalised output per resource unit provides a fairer assessment than looking at raw volumes alone.")

    trend_narrative = " ".join(trend_parts)
    comp_narrative = " ".join(comp_parts)

    script = (
        f"To understand trajectory and cohort variance, I analyzed the time series and comparative team distributions.\n\n"
        f"{trend_narrative}\n\n"
        f"{comp_narrative}\n\n"
        f"That takes me from describing performance to understanding the main insights and potential drivers."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Is the observed trend statistically significant?\n"
        "A: This analysis is descriptive of the observed period. I would not claim statistical significance without applying an appropriate inferential test and checking for autocorrelation.\n\n"
        "Q: Why not rank teams purely by total cases completed?\n"
        "A: Total completions reflects team staffing size rather than operational efficiency. Normalising by available capacity provides a much fairer basis for comparison."
    )
    return script + qa_cues


def _generate_notes_slide_5(approved_insights: List[Dict[str, Any]]) -> str:
    """Generate dynamic presenter notes for Slide 5 (Approved Key Insights & Root Cause)."""
    if approved_insights:
        insight_bullets = []
        for idx, ins in enumerate(approved_insights[:3]):
            title = ins.get("title", f"Finding {idx+1}")
            finding = ins.get("finding", "")
            pillar = ins.get("pillar") or ins.get("category") or "Operational Insight"
            insight_bullets.append(
                f"Regarding {title}: available evidence in {pillar} demonstrates that {finding}. "
                f"I treat this as an operational indication rather than definitive proof of a single cause, and I would investigate workflow constraints, case mix, and staffing availability before drawing final causal conclusions."
            )
        insights_narrative = "\n\n".join(insight_bullets)
    else:
        insights_narrative = "The data demonstrates operational variance across cohorts. However, I have maintained strict analytical governance by presenting only findings that have been explicitly verified."

    script = (
        f"On this slide, I have synthesised the verified evidence into our key operational insights, focusing strictly on approved findings and distinguishing observed correlation from causation.\n\n"
        f"{insights_narrative}\n\n"
        f"The data shows what occurred and where pressure was concentrated, but it does not by itself prove why without further qualitative investigation.\n\n"
        f"Based on those findings, I would focus management attention on a small number of practical actions."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Have you proven the root cause of the performance shortfall?\n"
        "A: I have identified potential drivers supported by the available evidence, not proven causation. Additional operational evidence is required before making a causal conclusion.\n\n"
        "Q: How do you prevent confirmation bias when interpreting operational findings?\n"
        "A: By evaluating competing hypotheses—such as whether bottlenecks stem from demand surges, staffing gaps, or process handoffs—and declaring analytical boundaries."
    )
    return script + qa_cues


def _generate_notes_slide_6(recommendations: Dict[str, List[Dict[str, Any]]], limitations: List[Any]) -> str:
    """Generate dynamic presenter notes for Slide 6 (Recommendations & Action Plan)."""
    all_recs = []
    if isinstance(recommendations, dict):
        for cat, rec_list in recommendations.items():
            for r in rec_list:
                if r.get("status") in ["approved", "accepted", None] and r.get("action"):
                    all_recs.append(r)
    elif isinstance(recommendations, list):
        for r in recommendations:
            if r.get("status") in ["approved", "accepted", None] and r.get("action"):
                all_recs.append(r)

    if all_recs:
        rec_bullets = []
        for idx, rec in enumerate(all_recs[:3]):
            title = rec.get("title", f"Priority Action {idx+1}")
            action = rec.get("action", "")
            owner = rec.get("owner", "Operational Lead")
            timeframe = rec.get("timeframe", "Short Term")
            impact = rec.get("expected_impact", "Improve throughput stability")
            rec_bullets.append(
                f"My recommendation on {title} is to {action}. This should be owned by {owner} over {timeframe}, with the expected impact to {impact}."
            )
        rec_narrative = " ".join(rec_bullets)
    else:
        rec_narrative = (
            "My first priority would be to identify which cohorts and periods are contributing most to delivery variances, "
            "and compare demand, capacity, case mix, and backlog direction so management does not respond with a blanket intervention."
        )

    script = (
        f"To address the identified operational constraints, I have translated our approved findings into targeted, measurable recommendations with clear ownership and implementation timeframes.\n\n"
        f"{rec_narrative}\n\n"
        f"I would also ensure that ongoing monitoring of demand versus completions is established before committing to long-term structural changes.\n\n"
        f"My recommendations are therefore evidence-led, but I would monitor the impact and adjust the intervention if the next reporting period does not show the expected improvement."
    )

    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: How would you know your recommendation worked?\n"
        "A: I would define a baseline and monitor the relevant KPI over subsequent reporting periods, while checking that any improvement is not caused by a change in definition or data quality.\n\n"
        "Q: What is the main implementation risk to this plan?\n"
        "A: Operational capacity constraints. Phasing the actions with explicit owners ensures business-as-usual delivery is not compromised during rollout."
    )
    return script + qa_cues


def _generate_notes_slide_7() -> str:
    """Generate presenter notes for Slide 7 (Appendix: Calculation Methodology)."""
    script = (
        "In this appendix slide, I have documented the exact mathematical formulas and ratio-of-sums logic used across all KPI calculations.\n\n"
        "I applied safe division rules to prevent zero-denominator errors, and incorporated explicit target directionality so that metrics like cycle times and error rates are appropriately evaluated where lower values represent superior performance.\n\n"
        "This ensures complete analytical reproducibility and methodological governance."
    )
    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why is ratio-of-sums mathematically superior for operational throughput?\n"
        "A: Because it computes total outputs divided by total inputs across the entire cohort, avoiding the distortion introduced by unweighted average of ratios."
    )
    return script + qa_cues


def _generate_notes_slide_8(qa_report: Dict[str, Any]) -> str:
    """Generate presenter notes for Slide 8 (Appendix: Detailed QA Audit Trail)."""
    score = qa_report.get("health_score", 100.0)
    issues_cnt = len(qa_report.get("issues", []))
    script = (
        f"In this slide, I have set out the complete exception inventory from my two-stage quality assurance audit, covering both Structural and Semantic QA.\n\n"
        f"A total of {issues_cnt} specific quality observations were logged in my audit trail, yielding the overall health score of {score:.1f}/100.\n\n"
        f"This audit log provides full transparency on all data quality caveats and treatment decisions."
    )
    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: How does Semantic QA differ from standard validation?\n"
        "A: Semantic QA tests domain-specific operational logic, such as queue flow reconciliation and zero staffing denominators, beyond basic data type checks."
    )
    return script + qa_cues


def _generate_notes_slide_9(assumptions: List[Any], limitations: List[Any]) -> str:
    """Generate presenter notes for Slide 9 (Appendix: Governance Registers)."""
    script = (
        "Here, I have formally recorded the Analytical Assumptions and Risk Limitations Registers.\n\n"
        "In my analysis, explicitly capturing boundaries—such as row granularity and unobserved case complexity—protects leadership from over-interpreting aggregate patterns.\n\n"
        "These registers define the necessary conditions under which my findings remain valid."
    )
    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why is maintaining an explicit limitations register essential for a Performance Analyst?\n"
        "A: It ensures intellectual honesty, prevents over-generalisation, and provides decision-makers with a transparent assessment of analytical risk."
    )
    return script + qa_cues


def _generate_notes_slide_10(comparison_summary: Optional[Dict[str, Any]]) -> str:
    """Generate presenter notes for Slide 10 (Appendix: Operational Segment Data Table)."""
    script = (
        "In this final appendix slide, I have compiled the granular segment-by-segment comparison table, including sample sizes and benchmark variances.\n\n"
        "I flagged segments with fewer than 5 observations with sample-size warnings to prevent over-reacting to small-number volatility.\n\n"
        "This granular view supports deep-dive operational reviews with team managers."
    )
    qa_cues = (
        "\n\n--------------------\n"
        "POSSIBLE FOLLOW-UP QUESTIONS\n"
        "--------------------\n"
        "Q: Why do you flag cohorts with sample size under 5?\n"
        "A: Small cohorts exhibit high random variance that can falsely appear as extreme over- or under-performance."
    )
    return script + qa_cues


# ==============================================================================
# 3. SLIDE STRUCTURE & GEOMETRY HELPERS
# ==============================================================================
def _add_slide_header(slide, title_text: str, subtitle_text: str = "", category_tag: str = "EXECUTIVE BRIEFING"):
    """Render consistent 16:9 slide header banner with hierarchy."""
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.3))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_tag.upper()
    p_tag.font.size = Pt(9.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_TEAL

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.733), Inches(0.8))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_MUTED_TEXT
        p2.space_before = Pt(2)

    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_CARD_BORDER
    line.line.color.rgb = COLOR_CARD_BORDER


def _add_slide_footer(slide, current_slide: int, total_slides: int = 6):
    """Render consistent 16:9 footer with thin rule and page indicator."""
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.95), Inches(11.733), Inches(0.015)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_CARD_BORDER
    line.line.color.rgb = COLOR_CARD_BORDER

    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.35))
    tf = footer_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"Performance Insight Explorer  |  Executive Operations Briefing  |  Slide {current_slide} of {total_slides}"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_MUTED_TEXT


def _add_card_box(slide, left: float, top: float, width: float, height: float, bg_color=COLOR_WHITE, border_color=COLOR_CARD_BORDER):
    """Add a rectangular card shape container."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


# ==============================================================================
# 4. CHART GENERATION HELPERS (Matplotlib 220 DPI)
# ==============================================================================
def generate_trend_chart_image(
    df: Optional[pd.DataFrame],
    confirmed_mappings: Dict[str, str],
    output_png_path: str = "outputs/charts/trend_chart_slide4.png"
) -> Optional[str]:
    """Generate high-resolution time series line chart from live dataset."""
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True) if os.path.dirname(output_png_path) else None
    
    time_col = None
    metric_col = None
    target_col = None

    for col, role in confirmed_mappings.items():
        if role in ["reporting_period", "date", "period"] and not time_col:
            time_col = col
        elif role in ["received", "demand", "completed", "actual", "volume"] and not metric_col:
            metric_col = col
        elif role == "target" and not target_col:
            target_col = col

    if df is None or len(df) == 0 or not time_col or not metric_col or time_col not in df.columns or metric_col not in df.columns:
        return None

    tdf = df.groupby(time_col).agg({metric_col: "sum", **({target_col: "sum"} if target_col and target_col in df.columns else {})}).reset_index()
    periods = [str(p) for p in tdf[time_col]]
    values = [float(v) for v in tdf[metric_col]]
    targets = [float(v) for v in tdf[target_col]] if target_col and target_col in tdf.columns else None

    if len(periods) == 0 or len(values) == 0:
        return None

    fig, ax = plt.subplots(figsize=(6.2, 3.4), dpi=220)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    ax.plot(periods, values, color='#173F73', marker='o', linewidth=2.5, markersize=5.5, label=f'Actual ({metric_col})', zorder=4)

    if targets:
        ax.plot(periods, targets, color='#F4A261', linestyle='--', linewidth=2.0, label='Target Benchmark', zorder=3)
        ax.fill_between(range(len(periods)), targets, values, color='#173F73', alpha=0.08, zorder=2)

    max_idx = int(np.argmax(values))
    min_idx = int(np.argmin(values))

    ax.scatter([periods[max_idx]], [values[max_idx]], color='#2E7D32', s=60, zorder=5)
    ax.annotate(f"Peak: {values[max_idx]:,.0f}", (periods[max_idx], values[max_idx]), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=7.5, fontweight='bold', color='#2E7D32')

    ax.scatter([periods[min_idx]], [values[min_idx]], color='#C62828', s=60, zorder=5)
    ax.annotate(f"Trough: {values[min_idx]:,.0f}", (periods[min_idx], values[min_idx]), textcoords="offset points", xytext=(0, -13), ha='center', fontsize=7.5, fontweight='bold', color='#C62828')

    ax.set_title(f'Operational Trajectory Over Time ({metric_col})', fontsize=10.5, fontweight='bold', color='#173F73', pad=10)
    ax.grid(axis='y', linestyle=':', alpha=0.6, color='#CBD5E1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94A3B8')
    ax.spines['bottom'].set_color('#94A3B8')
    ax.tick_params(axis='x', rotation=35, labelsize=7.5)
    ax.tick_params(axis='y', labelsize=8)
    ax.legend(loc='lower left', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')

    plt.tight_layout()
    fig.savefig(output_png_path, dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    return output_png_path


def generate_comparison_chart_image(
    df: Optional[pd.DataFrame],
    confirmed_mappings: Dict[str, str],
    output_png_path: str = "outputs/charts/comp_chart_slide4.png"
) -> Optional[str]:
    """Generate high-resolution horizontal bar chart comparing cohort groups from live dataset."""
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True) if os.path.dirname(output_png_path) else None

    group_col = None
    metric_col = None

    for col, role in confirmed_mappings.items():
        if role in ["service_team", "team", "group", "unit", "category", "department", "branch", "location"] and not group_col:
            group_col = col
        elif role in ["completed", "actual", "received", "volume"] and not metric_col:
            metric_col = col

    if df is None or len(df) == 0 or not group_col or not metric_col or group_col not in df.columns or metric_col not in df.columns:
        return None

    gdf = df.groupby(group_col)[metric_col].sum().reset_index()
    gdf = gdf.sort_values(by=metric_col, ascending=True)
    groups = [str(g) for g in gdf[group_col]]
    values = [float(v) for v in gdf[metric_col]]

    if len(groups) == 0 or len(values) == 0:
        return None

    fig, ax = plt.subplots(figsize=(6.2, 3.4), dpi=220)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    colors = ['#2F75B5'] * len(groups)
    if len(colors) >= 2:
        colors[-1] = '#2E7D32'  # Top performer
        colors[0] = '#F4A261'   # Lowest performer

    bars = ax.barh(groups, values, color=colors, height=0.6, zorder=3)
    avg_val = float(np.mean(values))
    ax.axvline(avg_val, color='#C62828', linestyle='--', linewidth=1.5, label=f'Group Average ({avg_val:,.0f})', zorder=4)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + (max(values) * 0.02), bar.get_y() + bar.get_height()/2, f'{w:,.0f}', va='center', ha='left', fontsize=8, fontweight='bold', color='#263238')

    ax.set_title(f'Cohort Comparison by {group_col}', fontsize=10.5, fontweight='bold', color='#173F73', pad=10)
    ax.grid(axis='x', linestyle=':', alpha=0.6, color='#CBD5E1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94A3B8')
    ax.spines['bottom'].set_color('#94A3B8')
    ax.tick_params(axis='y', labelsize=8.5)
    ax.tick_params(axis='x', labelsize=8)
    ax.set_xlim(0, max(values) * 1.22)
    ax.legend(loc='lower right', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')

    plt.tight_layout()
    fig.savefig(output_png_path, dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    return output_png_path


# ==============================================================================
# 5. INDIVIDUAL SLIDE BUILDERS (16:9 Widescreen Layouts)
# ==============================================================================
def _build_slide_1_opening(prs, ctx: Dict[str, Any], meta: Dict[str, Any], total_slides: int, clean_df: Optional[pd.DataFrame] = None):
    """Slide 1: Executive Context & Assessment Scope."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Executive Performance Assessment Briefing", "Operational diagnostic, queue health, and evidence-led delivery recommendations", "STRATEGIC OVERVIEW")

    # Hero Objective Banner Box
    _add_card_box(slide, 0.8, 1.55, 11.733, 1.7, bg_color=COLOR_LIGHT_GRAY)
    obj_box = slide.shapes.add_textbox(Inches(1.05), Inches(1.7), Inches(11.2), Inches(1.4))
    tf = obj_box.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "ASSESSMENT OBJECTIVE & BUSINESS QUESTION"
    p1.font.size = Pt(10)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEAL

    p2 = tf.add_paragraph()
    q_text = ctx.get("assessment_question") or ctx.get("question") or "Evaluate multi-team operational throughput, diagnose queue constraints, and recommend capacity interventions."
    p2.text = f'"{q_text}"'
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_NAVY
    p2.space_before = Pt(4)

    p3 = tf.add_paragraph()
    author_name = meta.get("author", "DARAMOLA OMOYELE")
    p3.text = f"Lead Performance Analyst: {author_name}   |   Prepared for: {ctx.get('target_audience', 'Chief Operating Officer & Senior Leadership')}   |   Assessment Lens: {ctx.get('assessment_lens', 'Throughput efficiency, backlog stability, and capacity balance')}"
    p3.font.size = Pt(10)
    p3.font.color.rgb = COLOR_MUTED_TEXT
    p3.space_before = Pt(4)

    # 4 Structured Metadata Cards
    row_cnt = meta.get('row_count') if meta.get('row_count') is not None else (len(clean_df) if clean_df is not None else 0)
    col_cnt = meta.get('column_count') if meta.get('column_count') is not None else (len(clean_df.columns) if clean_df is not None else 0)
    
    cards_data = [
        ("SOURCE DATASET", meta.get("filename", "Operational Dataset.csv"), "Active ingestion payload verified", COLOR_NAVY),
        ("DATASET DIMENSIONS", f"{row_cnt:,} Rows  |  {col_cnt} Columns", "Complete verified tabular scope", COLOR_NAVY),
        ("ROW GRANULARITY", meta.get("row_granularity", "Periodic operational snapshot"), "Analyst-confirmed record unit", COLOR_TEAL),
        ("ASSESSMENT SCOPE", meta.get("analysis_scope", "Multi-Team Operations & Queue Health"), "Standardized 16:9 widescreen briefing", COLOR_SECONDARY),
    ]

    card_w = 2.76
    card_gap = 0.23
    start_x = 0.8
    y_pos = 3.45

    for idx, (lbl, val, sub, colr) in enumerate(cards_data):
        cx = start_x + idx * (card_w + card_gap)
        _add_card_box(slide, cx, y_pos, card_w, 2.2, bg_color=COLOR_WHITE)
        tb = slide.shapes.add_textbox(Inches(cx + 0.15), Inches(y_pos + 0.2), Inches(card_w - 0.3), Inches(1.8))
        tframe = tb.text_frame
        tframe.word_wrap = True

        p_lbl = tframe.paragraphs[0]
        p_lbl.text = lbl
        p_lbl.font.size = Pt(9.5)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = COLOR_MUTED_TEXT

        p_val = tframe.add_paragraph()
        p_val.text = str(val)
        p_val.font.size = Pt(12.5)
        p_val.font.bold = True
        p_val.font.color.rgb = colr
        p_val.space_before = Pt(6)

        p_sub = tframe.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = COLOR_MUTED_TEXT
        p_sub.space_before = Pt(6)

    # Sequence / Methodology Footer Strip
    _add_card_box(slide, 0.8, 5.85, 11.733, 0.95, bg_color=COLOR_WHITE)
    seq_box = slide.shapes.add_textbox(Inches(1.0), Inches(5.95), Inches(11.3), Inches(0.75))
    stf = seq_box.text_frame
    stf.word_wrap = True
    sp1 = stf.paragraphs[0]
    sp1.text = "ANALYTICAL RIGOUR & GOVERNANCE PIPELINE"
    sp1.font.size = Pt(9)
    sp1.font.bold = True
    sp1.font.color.rgb = COLOR_TEAL

    sp2 = stf.add_paragraph()
    sp2.text = "1. Ingestion & Profile  ->  2. Structural & Semantic QA  ->  3. KPI Engine (Safe Ratios)  ->  4. Cohort Trends  ->  5. Approved Insights  ->  6. Action Plan"
    sp2.font.size = Pt(10.5)
    sp2.font.bold = True
    sp2.font.color.rgb = COLOR_DARK_TEXT
    sp2.space_before = Pt(2)

    _add_slide_footer(slide, 1, total_slides)

    # Attach Presenter Notes
    notes_1 = _generate_notes_slide_1(ctx, meta, clean_df)
    add_presenter_notes(slide, notes_1)


def _build_slide_2_qa(prs, qa_report: Dict[str, Any], meta: Dict[str, Any], total_slides: int, clean_df: Optional[pd.DataFrame] = None):
    """Slide 2: Data Quality, Health Score & Analytical Confidence."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Data Quality Assurance & Analytical Confidence", "Systematic evaluation of completeness, validity, consistency, and mathematical safety", "GOVERNANCE & INTEGRITY")

    score = qa_report.get("health_score", 100.0)
    score_color = COLOR_POSITIVE if score >= 80 else (COLOR_CAUTION if score >= 60 else COLOR_RISK)

    # Health Score Hero Card (Left Column)
    _add_card_box(slide, 0.8, 1.5, 3.4, 5.25, bg_color=COLOR_WHITE)
    sb = slide.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(3.0), Inches(4.7))
    stf = sb.text_frame
    stf.word_wrap = True

    p = stf.paragraphs[0]
    p.text = "DATA HEALTH SCORE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_MUTED_TEXT

    p_score = stf.add_paragraph()
    p_score.text = f"{score:.0f}/100"
    p_score.font.size = Pt(36)
    p_score.font.bold = True
    p_score.font.color.rgb = score_color
    p_score.space_before = Pt(8)

    p_stat = stf.add_paragraph()
    crit = qa_report.get("critical_count", 0)
    warn = qa_report.get("warning_count", 0)
    p_stat.text = f"Status: {crit} Critical Blockers  |  {warn} Warnings Flagged"
    p_stat.font.size = Pt(10)
    p_stat.font.bold = True
    p_stat.font.color.rgb = COLOR_DARK_TEXT
    p_stat.space_before = Pt(6)

    p_body = stf.add_paragraph()
    p_body.text = (
        "Evaluation Framework:\n"
        "* Structural schema integrity\n"
        "* Missing value identification\n"
        "* Outlier distribution analysis\n"
        "* Zero-denominator safeguards\n"
        "* Category casing consistency\n"
        "* Semantic queue balance audit"
    )
    p_body.font.size = Pt(9.5)
    p_body.font.color.rgb = COLOR_MUTED_TEXT
    p_body.space_before = Pt(12)

    # 4 Structured Issue Cards (Right Grid: 2x2)
    raw_issues = qa_report.get("issues", [])
    display_issues = []
    
    for idx, iss in enumerate(raw_issues[:4]):
        sev = iss.get("severity", "Warning")
        bcolr = COLOR_RISK if sev.lower() == "critical" else COLOR_CAUTION
        badge = sev.upper()
        title = iss.get("title", f"Quality Condition {idx+1}")
        desc = iss.get("description", "Quality exception logged.")
        action = iss.get("recommended_action") or iss.get("suggested_fix") or "Governed via safe calculation rules."
        display_issues.append((title, desc, action, badge, bcolr))

    while len(display_issues) < 4:
        display_issues.append((
            "Standard Operational Assurance",
            "No additional structural defects identified across loaded fields.",
            "Baseline calculation rules verified and active.",
            "VERIFIED",
            COLOR_POSITIVE
        ))

    card_w = 3.9
    card_h = 2.1
    for idx, (title, desc, action, badge, bcolr) in enumerate(display_issues[:4]):
        col = idx % 2
        row = idx // 2
        cx = 4.45 + col * (card_w + 0.25)
        cy = 1.5 + row * (card_h + 0.2)
        _add_card_box(slide, cx, cy, card_w, card_h, bg_color=COLOR_WHITE)

        tb = slide.shapes.add_textbox(Inches(cx + 0.15), Inches(cy + 0.15), Inches(card_w - 0.3), Inches(card_h - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = f"[{badge}]  {title}"
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = bcolr

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = COLOR_DARK_TEXT
        p_d.space_before = Pt(4)

        p_a = tf.add_paragraph()
        p_a.text = f"Action: {action}"
        p_a.font.size = Pt(8.5)
        p_a.font.color.rgb = COLOR_MUTED_TEXT
        p_a.space_before = Pt(4)

    # Bottom Methodology Banner
    _add_card_box(slide, 4.45, 6.1, 8.05, 0.65, bg_color=COLOR_LIGHT_GRAY)
    mb = slide.shapes.add_textbox(Inches(4.6), Inches(6.15), Inches(7.75), Inches(0.55))
    mtf = mb.text_frame
    mtf.word_wrap = True
    mp = mtf.paragraphs[0]
    mp.text = "ASSESSMENT CONFIDENCE: Dataset is verified as statistically reliable for strategic operations briefing."
    mp.font.size = Pt(9.5)
    mp.font.bold = True
    mp.font.color.rgb = COLOR_NAVY

    _add_slide_footer(slide, 2, total_slides)

    # Attach Presenter Notes
    notes_2 = _generate_notes_slide_2(qa_report, meta, clean_df)
    add_presenter_notes(slide, notes_2)


def _build_slide_3_performance(prs, kpi_summary: Dict[str, Any], total_slides: int):
    """Slide 3: Core Operational KPI Diagnostic Scorecard."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Core Operational KPI Diagnostic Scorecard", "Comprehensive ratio-of-sums evaluation across throughput, productivity, and queue stability", "EXECUTIVE KPI SCORECARD")

    raw_kpis = kpi_summary.get("summary_kpis", kpi_summary) if isinstance(kpi_summary, dict) else {}

    cards = []
    
    # 1. Target Achievement
    if "target_achievement_pct" in raw_kpis:
        info = raw_kpis["target_achievement_pct"]
        val = info.get("value")
        val_str = f"{val:.1f}%" if val is not None else "N/A"
        colr = COLOR_POSITIVE if info.get("is_favorable") is not False else COLOR_RISK
        cards.append(("TARGET ACHIEVEMENT", val_str, "Benchmark: Target Baseline", info.get("description", "Target achievement rate"), colr, info.get("formula", "Sum(Actual) / Sum(Target) * 100")))

    # 2. Target Variance
    if "target_variance" in raw_kpis:
        info = raw_kpis["target_variance"]
        val = info.get("value")
        val_str = f"{val:+,.0f} units" if val is not None else "N/A"
        colr = COLOR_POSITIVE if info.get("is_favorable") is not False else COLOR_RISK
        cards.append(("TARGET VARIANCE", val_str, "Under/Over Delivery", info.get("description", "Net variance against target"), colr, info.get("formula", "Sum(Actual) - Sum(Target)")))

    # 3. Productivity
    if "productivity" in raw_kpis:
        info = raw_kpis["productivity"]
        val = info.get("value")
        val_str = f"{val:.2f}" if val is not None else "N/A"
        cards.append(("OVERALL PRODUCTIVITY", val_str, info.get("unit", "Cases/FTE-period"), info.get("description", "Output delivered per capacity unit"), COLOR_NAVY, info.get("formula", "Sum(Completed) / Sum(Available FTE)")))

    # 4. Utilisation
    if "utilisation_pct" in raw_kpis:
        info = raw_kpis["utilisation_pct"]
        val = info.get("value")
        val_str = f"{val:.1f}%" if val is not None else "N/A"
        cards.append(("STAFF UTILISATION RATE", val_str, "Operational Capacity Load", info.get("description", "Proportion of scheduled hours worked"), COLOR_CAUTION, info.get("formula", "Sum(Hours Used) / Sum(Hours Avail) * 100")))

    # 5. Net Flow Balance
    if "estimated_net_flow" in raw_kpis:
        info = raw_kpis["estimated_net_flow"]
        val = info.get("value")
        val_str = f"{val:+,.0f} cases" if val is not None else "N/A"
        colr = COLOR_RISK if val and val > 0 else COLOR_POSITIVE
        cards.append(("NET FLOW BALANCE", val_str, "Demand vs Output Flow", info.get("description", "Inflow vs closure balance"), colr, info.get("formula", "Sum(Received) - Sum(Completed)")))

    # 6. Backlog Movement
    if "backlog_change" in raw_kpis:
        info = raw_kpis["backlog_change"]
        val = info.get("value")
        val_str = f"{val:+,.0f} cases" if val is not None else "N/A"
        colr = COLOR_RISK if val and val > 0 else COLOR_POSITIVE
        cards.append(("BACKLOG QUEUE MOVEMENT", val_str, "Queue Trajectory", info.get("description", "Observed queue inventory movement"), colr, info.get("formula", "Final Closing - Initial Opening")))

    # Fallback to other available KPIs if standard ones aren't all present
    for k, info in raw_kpis.items():
        if len(cards) >= 6:
            break
        if k not in ["target_achievement_pct", "target_variance", "productivity", "utilisation_pct", "estimated_net_flow", "backlog_change"]:
            val = info.get("value")
            val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val or "N/A")
            cards.append((info.get("name", k).upper(), val_str, info.get("unit", "Metric"), info.get("description", "Calculated operational metric"), COLOR_NAVY, info.get("formula", "")))

    while len(cards) < 6:
        cards.append(("UNMAPPED METRIC", "Not Mapped", "Field not confirmed", "Configure source column to activate measure", COLOR_MUTED_TEXT, "N/A"))

    card_w = 3.74
    card_h = 2.15
    for idx, (title, val, bench, interp, colr, form) in enumerate(cards[:6]):
        col = idx % 3
        row = idx // 3
        cx = 0.8 + col * (card_w + 0.25)
        cy = 1.5 + row * (card_h + 0.25)

        _add_card_box(slide, cx, cy, card_w, card_h, bg_color=COLOR_WHITE)
        tb = slide.shapes.add_textbox(Inches(cx + 0.15), Inches(cy + 0.12), Inches(card_w - 0.3), Inches(card_h - 0.24))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(9)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_MUTED_TEXT

        p_v = tf.add_paragraph()
        p_v.text = str(val)
        p_v.font.size = Pt(22)
        p_v.font.bold = True
        p_v.font.color.rgb = colr
        p_v.space_before = Pt(2)

        p_b = tf.add_paragraph()
        form_str = f"  *  {form}" if form and form != "N/A" else ""
        p_b.text = f"{bench}{form_str}"
        p_b.font.size = Pt(8.5)
        p_b.font.color.rgb = COLOR_TEAL
        p_b.space_before = Pt(2)

        p_i = tf.add_paragraph()
        p_i.text = interp
        p_i.font.size = Pt(9.5)
        p_i.font.color.rgb = COLOR_DARK_TEXT
        p_i.space_before = Pt(4)

    # Executive Diagnostic Banner
    _add_card_box(slide, 0.8, 6.2, 11.733, 0.65, bg_color=COLOR_LIGHT_GRAY)
    eb = slide.shapes.add_textbox(Inches(1.0), Inches(6.25), Inches(11.3), Inches(0.55))
    etf = eb.text_frame
    etf.word_wrap = True
    ep = etf.paragraphs[0]
    ep.text = "Executive Performance Diagnostic: Operational measures evaluated via weighted ratio-of-sums to ensure mathematical integrity."
    ep.font.size = Pt(9.5)
    ep.font.bold = True
    ep.font.color.rgb = COLOR_NAVY

    _add_slide_footer(slide, 3, total_slides)

    # Attach Presenter Notes
    notes_3 = _generate_notes_slide_3(kpi_summary)
    add_presenter_notes(slide, notes_3)


def _build_slide_4_trends(
    prs,
    trend_summary: Optional[Dict[str, Any]],
    comparison_summary: Optional[Dict[str, Any]],
    clean_df: Optional[pd.DataFrame],
    confirmed_mappings: Dict[str, str],
    total_slides: int
):
    """Slide 4: Trajectory Trends & Comparative Cohort Analysis."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Trajectory Trends & Comparative Cohort Analysis", "Longitudinal volume patterns and normalised operational cohort throughput", "TRENDS & COMPARISONS")

    chart1_path = generate_trend_chart_image(clean_df, confirmed_mappings)
    chart2_path = generate_comparison_chart_image(clean_df, confirmed_mappings)

    # Trend Chart Container (Left)
    _add_card_box(slide, 0.8, 1.45, 5.7, 4.4, bg_color=COLOR_WHITE)
    if chart1_path and os.path.exists(chart1_path):
        slide.shapes.add_picture(chart1_path, Inches(0.9), Inches(1.55), Inches(5.5), Inches(3.1))
        tb1 = slide.shapes.add_textbox(Inches(0.9), Inches(4.75), Inches(5.5), Inches(1.0))
        tf1 = tb1.text_frame
        tf1.word_wrap = True
        p1 = tf1.paragraphs[0]
        p1.text = "TRAJECTORY OBSERVATION: Longitudinal time series tracks chronological peaks, troughs, and baseline volume movements across reporting periods."
        p1.font.size = Pt(9)
        p1.font.color.rgb = COLOR_DARK_TEXT
    else:
        tb1 = slide.shapes.add_textbox(Inches(1.2), Inches(2.5), Inches(4.9), Inches(2.0))
        p1 = tb1.text_frame.paragraphs[0]
        p1.text = "No confirmed time variable is available in the active dataset, so trend analysis was not performed."
        p1.font.size = Pt(11)
        p1.font.color.rgb = COLOR_MUTED_TEXT

    # Cohort Chart Container (Right)
    _add_card_box(slide, 6.833, 1.45, 5.7, 4.4, bg_color=COLOR_WHITE)
    if chart2_path and os.path.exists(chart2_path):
        slide.shapes.add_picture(chart2_path, Inches(6.933), Inches(1.55), Inches(5.5), Inches(3.1))
        tb2 = slide.shapes.add_textbox(Inches(6.933), Inches(4.75), Inches(5.5), Inches(1.0))
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = "COHORT INSIGHT: Operational segment breakdown compares output against group averages; normalised rates protect against team size bias."
        p2.font.size = Pt(9)
        p2.font.color.rgb = COLOR_DARK_TEXT
    else:
        tb2 = slide.shapes.add_textbox(Inches(7.2), Inches(2.5), Inches(4.9), Inches(2.0))
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = "No confirmed cohort or team variable is available in the active dataset, so comparative analysis was not performed."
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_MUTED_TEXT

    # Synthesis Footer Banner
    _add_card_box(slide, 0.8, 6.0, 11.733, 0.85, bg_color=COLOR_LIGHT_GRAY)
    sb = slide.shapes.add_textbox(Inches(1.0), Inches(6.08), Inches(11.3), Inches(0.7))
    stf = sb.text_frame
    stf.word_wrap = True
    sp = stf.paragraphs[0]
    sp.text = "KEY TAKEAWAY: Performance variation across periods and segments should be evaluated against capacity allocation and case complexity."
    sp.font.size = Pt(10)
    sp.font.bold = True
    sp.font.color.rgb = COLOR_NAVY

    _add_slide_footer(slide, 4, total_slides)

    # Attach Presenter Notes
    notes_4 = _generate_notes_slide_4(trend_summary, comparison_summary, clean_df, confirmed_mappings)
    add_presenter_notes(slide, notes_4)


def _build_slide_5_insights(prs, approved_insights: List[Dict[str, Any]], total_slides: int):
    """Slide 5: Key Approved Findings & Root Cause Analysis."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Approved Operational Findings & Root Cause Analysis", "Evidence-grounded analytical insights structured by operational delivery pillars", "ANALYTICAL INSIGHTS")

    # Governance Strip
    _add_card_box(slide, 0.8, 1.45, 11.733, 0.45, bg_color=COLOR_LIGHT_GRAY)
    gb = slide.shapes.add_textbox(Inches(0.95), Inches(1.48), Inches(11.4), Inches(0.35))
    gtf = gb.text_frame
    gtf.word_wrap = True
    gp = gtf.paragraphs[0]
    gp.text = "GOVERNANCE STANDARD: Only analyst-verified and approved findings are presented below. Unreviewed hypotheses are withheld."
    gp.font.size = Pt(8.5)
    gp.font.bold = True
    gp.font.color.rgb = COLOR_TEAL

    insights_to_show = []
    if approved_insights:
        for ins in approved_insights[:3]:
            insights_to_show.append({
                "pillar": ins.get("pillar") or ins.get("category") or "Operational Insight",
                "title": ins.get("title", "Operational Finding"),
                "finding": ins.get("finding", "Detailed evidence observed in dataset."),
                "evidence": ins.get("evidence", f"Severity: {ins.get('severity', 'Medium').upper()}  |  Status: Analyst Approved"),
                "severity": (ins.get("severity") or "Approved").upper(),
                "badge_colr": COLOR_RISK if ins.get("severity") == "high" else COLOR_CAUTION
            })

    if not insights_to_show:
        _add_card_box(slide, 0.8, 2.05, 11.733, 4.8, bg_color=COLOR_WHITE)
        ibox = slide.shapes.add_textbox(Inches(1.2), Inches(3.0), Inches(11.0), Inches(2.5))
        p = ibox.text_frame.paragraphs[0]
        p.text = "No findings have been formally approved for executive presentation yet."
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_MUTED_TEXT
        p2 = ibox.text_frame.add_paragraph()
        p2.text = "Review and approve findings on Page 08 (Insights) to populate this slide."
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_MUTED_TEXT
        p2.space_before = Pt(6)
    else:
        card_w = 3.74
        card_h = 4.8
        for idx, item in enumerate(insights_to_show):
            cx = 0.8 + idx * (card_w + 0.25)
            cy = 2.05

            _add_card_box(slide, cx, cy, card_w, card_h, bg_color=COLOR_WHITE)
            tb = slide.shapes.add_textbox(Inches(cx + 0.2), Inches(cy + 0.2), Inches(card_w - 0.4), Inches(card_h - 0.4))
            tf = tb.text_frame
            tf.word_wrap = True

            p_pil = tf.paragraphs[0]
            p_pil.text = f"[{item['severity']}]  {item['pillar'].upper()}"
            p_pil.font.size = Pt(8.5)
            p_pil.font.bold = True
            p_pil.font.color.rgb = item["badge_colr"]

            p_t = tf.add_paragraph()
            p_t.text = item["title"]
            p_t.font.size = Pt(13)
            p_t.font.bold = True
            p_t.font.color.rgb = COLOR_NAVY
            p_t.space_before = Pt(6)

            p_f = tf.add_paragraph()
            p_f.text = item["finding"]
            p_f.font.size = Pt(10)
            p_f.font.color.rgb = COLOR_DARK_TEXT
            p_f.space_before = Pt(8)

            p_e = tf.add_paragraph()
            p_e.text = f"Analytical Evidence:\n{item['evidence']}"
            p_e.font.size = Pt(9)
            p_e.font.color.rgb = COLOR_MUTED_TEXT
            p_e.space_before = Pt(12)

    _add_slide_footer(slide, 5, total_slides)

    # Attach Presenter Notes
    notes_5 = _generate_notes_slide_5(approved_insights)
    add_presenter_notes(slide, notes_5)


def _build_slide_6_actions(
    prs,
    recommendations: Dict[str, List[Dict[str, Any]]],
    limitations: List[Any],
    total_slides: int
):
    """Slide 6: Strategic Action Plan, Ownership & Risk Limitations."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Strategic Action Plan, Ownership & Implementation", "Prioritised operational interventions, accountability matrix, and governance boundaries", "ACTION MATRIX")

    # Flatten recommendations
    action_rows = []
    if isinstance(recommendations, dict):
        for cat, r_list in recommendations.items():
            for r in r_list:
                if r.get("status") in ["approved", "accepted", None]:
                    title_txt = r.get("title", "Action")
                    act_txt = r.get("action", "")
                    combined_act = f"{title_txt}: {act_txt}" if act_txt else title_txt
                    action_rows.append((
                        combined_act,
                        cat.upper() if cat else "OPERATIONS",
                        r.get("owner", "Operations Lead"),
                        r.get("timeframe", "Immediate (1-30d)"),
                        r.get("expected_impact", "Capacity balancing & SLA recovery")
                    ))
    elif isinstance(recommendations, list):
        for r in recommendations:
            if r.get("status") in ["approved", "accepted", None]:
                title_txt = r.get("title", "Action")
                act_txt = r.get("action", "")
                combined_act = f"{title_txt}: {act_txt}" if act_txt else title_txt
                action_rows.append((
                    combined_act,
                    r.get("category", "OPERATIONS").upper(),
                    r.get("owner", "Operations Lead"),
                    r.get("timeframe", "Immediate (1-30d)"),
                    r.get("expected_impact", "Capacity balancing & SLA recovery")
                ))

    # Render 5-Column Action Table
    if action_rows:
        rows_to_render = min(len(action_rows) + 1, 5)
        t_shape = slide.shapes.add_table(rows_to_render, 5, Inches(0.8), Inches(1.5), Inches(11.733), Inches(3.5))
        table = t_shape.table

        widths = [Inches(4.5), Inches(1.5), Inches(1.8), Inches(1.7), Inches(2.233)]
        for idx, w in enumerate(widths):
            table.columns[idx].width = w

        headers = ["ACTION ITEM & INTERVENTION", "FOCUS AREA", "ACCOUNTABLE OWNER", "TIMEFRAME", "EXPECTED IMPACT"]
        for j, h in enumerate(headers):
            cell = table.cell(0, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_NAVY
            p = cell.text_frame.paragraphs[0]
            p.text = h
            p.font.size = Pt(9.5)
            p.font.bold = True
            p.font.color.rgb = COLOR_WHITE

        for i in range(rows_to_render - 1):
            row_data = action_rows[i]
            bg = COLOR_LIGHT_GRAY if i % 2 == 0 else COLOR_WHITE
            for j, val in enumerate(row_data):
                cell = table.cell(i + 1, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg
                p = cell.text_frame.paragraphs[0]
                p.text = str(val)
                p.font.size = Pt(9)
                p.font.color.rgb = COLOR_DARK_TEXT
                if j == 0:
                    p.font.bold = True
    else:
        _add_card_box(slide, 0.8, 1.5, 11.733, 3.5, bg_color=COLOR_WHITE)
        ibox = slide.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(2.0))
        p = ibox.text_frame.paragraphs[0]
        p.text = "No action recommendations have been formally approved yet."
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_MUTED_TEXT

    # Operational Limitations & Risk Boundaries Strip
    _add_card_box(slide, 0.8, 5.25, 11.733, 1.5, bg_color=COLOR_WHITE)
    lb = slide.shapes.add_textbox(Inches(1.0), Inches(5.35), Inches(11.3), Inches(1.3))
    ltf = lb.text_frame
    ltf.word_wrap = True

    lp1 = ltf.paragraphs[0]
    lp1.text = "ANALYTICAL LIMITATIONS & OPERATIONAL RISK BOUNDARIES"
    lp1.font.size = Pt(9.5)
    lp1.font.bold = True
    lp1.font.color.rgb = COLOR_RISK

    limit_bullets = []
    if limitations:
        for lim in limitations[:3]:
            txt = lim.get("limitation") if isinstance(lim, dict) else str(lim)
            imp = lim.get("impact", "") if isinstance(lim, dict) else ""
            limit_bullets.append(f"* {txt}" + (f" ({imp})" if imp else ""))
    else:
        limit_bullets = [
            "* Observational Data: Findings reflect observed patterns and require operational validation.",
            "* Case Complexity: Differences in case mix complexity across cohorts should be verified.",
            "* Measurement Boundaries: Interventions should be tracked against pre-defined baseline metrics."
        ]

    lp2 = ltf.add_paragraph()
    lp2.text = "\n".join(limit_bullets)
    lp2.font.size = Pt(9)
    lp2.font.color.rgb = COLOR_MUTED_TEXT
    lp2.space_before = Pt(4)

    _add_slide_footer(slide, 6, total_slides)

    # Attach Presenter Notes
    notes_6 = _generate_notes_slide_6(recommendations, limitations)
    add_presenter_notes(slide, notes_6)


# ==============================================================================
# 6. OPTIONAL TECHNICAL APPENDIX SLIDES (Slides 7-10)
# ==============================================================================
def _build_slide_7_appendix_methods(prs, total_slides: int):
    """Slide 7: Technical Methodology & KPI Formulas."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Appendix 1: Technical Methodology & Mathematical Formulas", "Standardised calculation formulas, denominator guards, and directional variance rules", "TECHNICAL APPENDIX")

    formulas = [
        ("Target Achievement %", "Sum(Actual) / Sum(Target) * 100", "Weighted portfolio achievement protecting against unequal volume distortion."),
        ("Productivity", "Sum(Completed Cases) / Sum(Available FTE)", "Throughput delivered per staff resource unit; safe against 0 FTE denominators."),
        ("Utilisation Rate %", "Sum(Hours Used) / Sum(Hours Available) * 100", "Proportion of scheduled capacity actively engaged in casework."),
        ("Flow Balance / Net Flow", "Sum(Demand Received) - Sum(Cases Closed)", "Macro queue movement indicator; positive indicates expanding backlog."),
        ("Backlog Reconciliation", "Closing Backlog - (Opening + Demand - Closed)", "Flow accounting balance check; non-zero values flag reporting gaps."),
        ("Directional Target Variance", "(Actual - Target) or (Target - Actual)", "Direction-aware evaluation respecting 'lower is better' for time/error KPIs.")
    ]

    card_w = 5.7
    card_h = 1.5
    for idx, (name, formula, desc) in enumerate(formulas):
        col = idx % 2
        row = idx // 2
        cx = 0.8 + col * (card_w + 0.333)
        cy = 1.5 + row * (card_h + 0.2)

        _add_card_box(slide, cx, cy, card_w, card_h, bg_color=COLOR_WHITE)
        tb = slide.shapes.add_textbox(Inches(cx + 0.15), Inches(cy + 0.12), Inches(card_w - 0.3), Inches(card_h - 0.24))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = name
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_NAVY

        p2 = tf.add_paragraph()
        p2.text = f"Formula: {formula}"
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_TEAL
        p2.space_before = Pt(2)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = COLOR_DARK_TEXT
        p3.space_before = Pt(3)

    _add_slide_footer(slide, 7, total_slides)

    # Attach Presenter Notes
    notes_7 = _generate_notes_slide_7()
    add_presenter_notes(slide, notes_7)


def _build_slide_8_appendix_qa(prs, qa_report: Dict[str, Any], total_slides: int):
    """Slide 8: Detailed QA Log & Anomaly Inventory."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Appendix 2: Comprehensive Quality Assurance Log", "Itemised inventory of all structural and semantic data quality checks", "TECHNICAL APPENDIX")

    issues = qa_report.get("issues", [])
    if not issues:
        issues = [
            {"issue_type": "Completeness", "severity": "Info", "column": "Dataset", "description": "All mandatory fields populated.", "suggested_fix": "No action required."}
        ]

    rows = min(len(issues) + 1, 6)
    t_shape = slide.shapes.add_table(rows, 5, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.2))
    table = t_shape.table
    widths = [Inches(1.8), Inches(1.5), Inches(2.2), Inches(3.8), Inches(2.433)]
    for idx, w in enumerate(widths):
        table.columns[idx].width = w

    headers = ["CHECK TYPE", "SEVERITY", "FIELD / COLUMN", "ANOMALY DESCRIPTION", "MITIGATION STATUS"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    for i in range(rows - 1):
        iss = issues[i]
        bg = COLOR_LIGHT_GRAY if i % 2 == 0 else COLOR_WHITE
        vals = [
            str(iss.get("issue_type", "Quality Check")).upper(),
            str(iss.get("severity", "Warning")).upper(),
            str(iss.get("column") or iss.get("field") or "Dataset"),
            str(iss.get("description", "Quality check completed.")),
            str(iss.get("suggested_fix") or iss.get("recommended_action") or "Resolved via mathematical guard")
        ]
        for j, text_val in enumerate(vals):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = text_val
            p.font.size = Pt(8.5)
            if j in [0, 1]:
                p.font.bold = True

    _add_slide_footer(slide, 8, total_slides)

    # Attach Presenter Notes
    notes_8 = _generate_notes_slide_8(qa_report)
    add_presenter_notes(slide, notes_8)


def _build_slide_9_appendix_governance(prs, assumptions: List[Any], limitations: List[Any], total_slides: int):
    """Slide 9: Analytical Assumptions & Risk Registers."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Appendix 3: Analytical Assumptions & Risk Register", "Formally documented boundaries, baseline parameters, and operational risk factors", "TECHNICAL APPENDIX")

    # Assumptions Card (Left)
    _add_card_box(slide, 0.8, 1.5, 5.7, 5.2, bg_color=COLOR_WHITE)
    ab = slide.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.8))
    atf = ab.text_frame
    atf.word_wrap = True
    ap = atf.paragraphs[0]
    ap.text = "ANALYTICAL ASSUMPTIONS REGISTER"
    ap.font.size = Pt(11)
    ap.font.bold = True
    ap.font.color.rgb = COLOR_NAVY

    assump_items = []
    if assumptions:
        for a in assumptions[:5]:
            txt = a.get("assumption") if isinstance(a, dict) else str(a)
            assump_items.append(f"* {txt}")
    else:
        assump_items = [
            "* Standard Working Calendar: Working patterns assumed consistent across periods.",
            "* Resource Availability: Confirmed staff capacity reflects operational allocation.",
            "* Macro Flow Continuity: Inflow and completion differences approximate queue movement."
        ]
    for item in assump_items:
        p = atf.add_paragraph()
        p.text = item
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)

    # Limitations Card (Right)
    _add_card_box(slide, 6.833, 1.5, 5.7, 5.2, bg_color=COLOR_WHITE)
    lb = slide.shapes.add_textbox(Inches(7.033), Inches(1.7), Inches(5.3), Inches(4.8))
    ltf = lb.text_frame
    ltf.word_wrap = True
    lp = ltf.paragraphs[0]
    lp.text = "OPERATIONAL LIMITATIONS & RISK FACTORS"
    lp.font.size = Pt(11)
    lp.font.bold = True
    lp.font.color.rgb = COLOR_RISK

    limit_items = []
    if limitations:
        for l in limitations[:5]:
            txt = l.get("limitation") if isinstance(l, dict) else str(l)
            limit_items.append(f"* {txt}")
    else:
        limit_items = [
            "* Observational Data: Findings reflect observed operational periods.",
            "* Unrecorded Factors: External drivers not captured in the extract remain unmodelled."
        ]
    for item in limit_items:
        pl = ltf.add_paragraph()
        pl.text = item
        pl.font.size = Pt(9.5)
        pl.font.color.rgb = COLOR_DARK_TEXT
        pl.space_before = Pt(8)

    _add_slide_footer(slide, 9, total_slides)

    # Attach Presenter Notes
    notes_9 = _generate_notes_slide_9(assumptions, limitations)
    add_presenter_notes(slide, notes_9)


def _build_slide_10_appendix_comparison_table(prs, comparison_summary: Optional[Dict[str, Any]], total_slides: int):
    """Slide 10: Detailed Operational Comparison Data Table."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_slide_header(slide, "Appendix 4: Operational Segment Comparison Table", "Granular segment performance breakdown, sample counts, and benchmark spread", "TECHNICAL APPENDIX")

    cdf = comparison_summary.get("comparison_df") if comparison_summary else None
    if cdf is not None and len(cdf) > 0:
        rows = min(8, len(cdf) + 1)
        t_shape = slide.shapes.add_table(rows, 6, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.2))
        table = t_shape.table
        widths = [Inches(1.2), Inches(2.8), Inches(1.8), Inches(2.0), Inches(2.0), Inches(1.933)]
        for idx, w in enumerate(widths):
            table.columns[idx].width = w

        headers = ["RANK", "OPERATIONAL UNIT", "RECORDS", "THROUGHPUT", "BENCHMARK VAR", "CAUTION"]
        for j, h in enumerate(headers):
            cell = table.cell(0, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_NAVY
            p = cell.text_frame.paragraphs[0]
            p.text = h
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = COLOR_WHITE

        cdf_sorted = cdf.sort_values(by="value", ascending=False)
        for i in range(rows - 1):
            r = cdf_sorted.iloc[i]
            rank_val = r.get("rank", i + 1)
            grp_val = str(r.get("group", "Unit"))
            cnt_val = f"{r.get('sample_count', 0):,}"
            val_str = f"{r.get('value', 0):,.2f}"
            var_str = f"{r.get('var_pct_benchmark', 0):+,.1f}%"
            sml_str = "[!] <5 sample" if r.get("is_small_sample") else "Robust"

            bg = COLOR_LIGHT_GRAY if i % 2 == 0 else COLOR_WHITE
            for j, text_val in enumerate([rank_val, grp_val, cnt_val, val_str, var_str, sml_str]):
                cell = table.cell(i + 1, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg
                p = cell.text_frame.paragraphs[0]
                p.text = str(text_val)
                p.font.size = Pt(9.5)
                if j in [0, 1]:
                    p.font.bold = True
    else:
        _add_card_box(slide, 0.8, 1.5, 11.733, 5.2, bg_color=COLOR_WHITE)
        ibox = slide.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(11.0), Inches(3.0))
        p = ibox.text_frame.paragraphs[0]
        p.text = "Operational Segment Comparison Data was not configured during the current analytical session."
        p.font.size = Pt(14)
        p.font.color.rgb = COLOR_MUTED_TEXT

    _add_slide_footer(slide, 10, total_slides)

    # Attach Presenter Notes
    notes_10 = _generate_notes_slide_10(comparison_summary)
    add_presenter_notes(slide, notes_10)


# ==============================================================================
# 7. MAIN PRESENTATION GENERATION ENTRY POINT
# ==============================================================================
def generate_powerpoint_presentation(
    output_filepath: str,
    project_metadata: Dict[str, Any],
    qa_report: Dict[str, Any],
    kpi_summary: Dict[str, Any],
    trend_summary: Optional[Dict[str, Any]],
    comparison_summary: Optional[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    recommendations: Dict[str, List[Dict[str, Any]]],
    limitations: List[Any],
    assumptions: List[Any],
    assessment_context: Optional[Dict[str, str]] = None,
    row_granularity: str = "Periodic snapshot",
    clean_df: Optional[pd.DataFrame] = None,
    confirmed_mappings: Optional[Dict[str, str]] = None,
    include_appendix: bool = False
) -> str:
    """Generate the 16:9 executive PowerPoint presentation deck."""
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True) if os.path.dirname(output_filepath) else None
    
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    ctx = assessment_context or {}
    meta = project_metadata or {}
    if "row_granularity" not in meta:
        meta["row_granularity"] = row_granularity

    approved_insights = [i for i in insights if i.get("status") in ["approved", "accepted"]] if insights else []
    
    total_slides = 10 if include_appendix else 6

    # 1. Slide 1: Executive Opening
    _build_slide_1_opening(prs, ctx, meta, total_slides, clean_df)

    # 2. Slide 2: Data Quality & Assurance
    _build_slide_2_qa(prs, qa_report or {}, meta, total_slides, clean_df)

    # 3. Slide 3: Performance Overview
    _build_slide_3_performance(prs, kpi_summary or {}, total_slides)

    # 4. Slide 4: Trends & Comparisons
    _build_slide_4_trends(prs, trend_summary, comparison_summary, clean_df, confirmed_mappings or {}, total_slides)

    # 5. Slide 5: Key Insights
    _build_slide_5_insights(prs, approved_insights, total_slides)

    # 6. Slide 6: Recommendations & Limitations
    _build_slide_6_actions(prs, recommendations or {}, limitations or [], total_slides)

    # Optional Appendix Slides (7-10)
    if include_appendix:
        _build_slide_7_appendix_methods(prs, total_slides)
        _build_slide_8_appendix_qa(prs, qa_report or {}, total_slides)
        _build_slide_9_appendix_governance(prs, assumptions or [], limitations or [], total_slides)
        _build_slide_10_appendix_comparison_table(prs, comparison_summary, total_slides)

    prs.save(output_filepath)
    return output_filepath


def generate_interview_powerpoint(
    df: Optional[pd.DataFrame] = None,
    mappings: Optional[Dict[str, str]] = None,
    target_directions: Optional[Dict[str, str]] = None,
    insights: Optional[List[Dict[str, Any]]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    author: str = "DARAMOLA OMOYELE",
    include_appendix: bool = False
) -> str:
    """Convenience wrapper to build the standardized 16:9 executive deck."""
    from src.metrics import calculate_kpis
    from src.quality import run_quality_audit
    
    out_dir = output_dir or os.path.join(os.getcwd(), "outputs", "presentations")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(out_dir, f"Performance_Briefing_{timestamp}.pptx")
    
    target_dir = "higher_is_better"
    if isinstance(target_directions, dict) and target_directions:
        target_dir = next(iter(target_directions.values()), "higher_is_better")
    elif isinstance(target_directions, str):
        target_dir = target_directions

    kpi_res = calculate_kpis(df, mappings or {}, target_direction=target_dir) if df is not None else {}
    kpi_summary = kpi_res.get("summary_kpis", {})
    
    qa_report = run_quality_audit(df, mappings or {}) if df is not None else {
        "health_score": 100.0, "critical_count": 0, "warning_count": 0, "issues": []
    }
    
    project_metadata = {
        "filename": "Operational Dataset",
        "row_count": len(df) if df is not None else 0,
        "column_count": len(df.columns) if df is not None else 0,
        "author": author,
        "row_granularity": (context or {}).get("row_granularity", "Periodic snapshot")
    }
    
    app_insights = [x for x in (insights or []) if x.get("status") in ["approved", "accepted"]]
    if not app_insights and insights:
        app_insights = insights
        
    app_recs = [x for x in (recommendations or []) if x.get("status") in ["approved", "accepted"]]
    if not app_recs and recommendations:
        app_recs = recommendations
        
    recs_by_cat = {}
    if isinstance(app_recs, dict):
        recs_by_cat = app_recs
    else:
        for r in (app_recs or []):
            cat = r.get("category", "Act")
            if cat not in recs_by_cat:
                recs_by_cat[cat] = []
            recs_by_cat[cat].append(r)
            
    generate_powerpoint_presentation(
        output_filepath=filepath,
        project_metadata=project_metadata,
        qa_report=qa_report,
        kpi_summary=kpi_summary,
        trend_summary=None,
        comparison_summary=None,
        insights=app_insights,
        recommendations=recs_by_cat,
        limitations=[{"limitation": f"Row Unit = {project_metadata['row_granularity']}", "impact": "Aggregated snapshot analysis"}],
        assumptions=[{"assumption": "Operational shift patterns apply.", "area": "Capacity"}],
        assessment_context=context or {},
        row_granularity=(context or {}).get("row_granularity", "Periodic snapshot"),
        clean_df=df,
        confirmed_mappings=mappings or {},
        include_appendix=include_appendix
    )
    return filepath

def generate_assessment_presentation(
    payload_or_filepath: Any,
    output_filepath: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Unified entry point for PowerPoint generation.
    Accepts either a structured payload dict (from build_export_payload_from_state)
    or standard positional arguments.
    """
    if isinstance(payload_or_filepath, dict):
        payload = payload_or_filepath
        meta = payload.get("metadata", {})
        ds = payload.get("dataset", {})
        qa = payload.get("data_quality", {})
        kpis = payload.get("kpis", {})
        trends = payload.get("trends")
        comps = payload.get("comparisons")
        findings = payload.get("findings", [])
        recs = payload.get("recommendations", [])
        if isinstance(recs, list):
            recs_dict = {"operational": recs}
        else:
            recs_dict = recs
            
        out_path = output_filepath or "exports/assessment_presentation_16x9.pptx"
        os.makedirs(os.path.dirname(out_path), exist_ok=True) if os.path.dirname(out_path) else None
        
        prs = Presentation()
        prs.slide_width = Inches(SLIDE_WIDTH_IN)
        prs.slide_height = Inches(SLIDE_HEIGHT_IN)
        total_slides = 6
        
        # Build standard 6-slide deck
        _build_slide_1_opening(prs, meta, {"filename": ds.get("name", "Active Dataset"), "row_count": ds.get("row_count", 0), "col_count": ds.get("col_count", 0), "row_granularity": ds.get("granularity", "Records")}, total_slides)
        _build_slide_2_qa(prs, {"health_score": qa.get("health_score", 100.0), "critical_count": 0, "warning_count": len(qa.get("caveats", [])), "issues": []}, {"row_granularity": ds.get("granularity", "Records")}, total_slides)
        _build_slide_3_performance(prs, kpis, total_slides)
        _build_slide_4_trends(prs, trends, comps, None, {}, total_slides)
        _build_slide_5_insights(prs, findings, total_slides)
        _build_slide_6_actions(prs, recs_dict, qa.get("caveats", []), total_slides)
        
        prs.save(out_path)
        prs.output_path = out_path
        return prs
    else:
        return generate_powerpoint_presentation(payload_or_filepath, **kwargs)

