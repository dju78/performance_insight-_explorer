"""Comprehensive unit & structural verification tests for 16:9 executive PowerPoint exporter."""
import os
import pytest
import pandas as pd
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from src.powerpoint import generate_powerpoint_presentation, generate_interview_powerpoint
from src.export import generate_powerpoint_deck


def test_powerpoint_widescreen_16_9_dimensions(tmp_path):
    """Verify generated presentation is strictly 16:9 widescreen (13.333 x 7.5 inches)."""
    out_file = str(tmp_path / "deck_16x9.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15, "row_granularity": "Periodic snapshot"}
    qa = {"critical_count": 0, "warning_count": 1, "health_score": 85.0, "issues": []}
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary={},
        trend_summary=None,
        comparison_summary=None,
        insights=[],
        recommendations={},
        limitations=[],
        assumptions=[],
        assessment_context={"question": "Test Question", "audience": "Senior Leadership"},
        include_appendix=False
    )
    
    prs = Presentation(path)
    assert round(prs.slide_width.inches, 2) == 13.33
    assert round(prs.slide_height.inches, 2) == 7.50
    assert len(prs.slides) == 6


def test_powerpoint_chart_images_on_slide_4(tmp_path):
    """Verify Slide 4 contains embedded picture shapes for time trends and cohort comparisons."""
    out_file = str(tmp_path / "deck_charts.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15}
    qa = {"critical_count": 0, "warning_count": 0, "health_score": 100.0, "issues": []}
    
    df = pd.DataFrame({
        "Period": ["2025-01", "2025-02", "2025-03", "2025-04"],
        "Team": ["East", "West", "North", "South"],
        "Volume": [100, 150, 120, 180]
    })
    mappings = {"Period": "period", "Team": "group", "Volume": "completed"}
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary={},
        trend_summary=None,
        comparison_summary=None,
        insights=[],
        recommendations={},
        limitations=[],
        assumptions=[],
        clean_df=df,
        confirmed_mappings=mappings
    )
    
    prs = Presentation(path)
    slide4 = prs.slides[3] # Slide 4 (0-indexed 3)
    
    # Check that picture shapes exist on slide 4
    pictures = [s for s in slide4.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert len(pictures) >= 2, f"Expected at least 2 embedded chart pictures on Slide 4, found {len(pictures)}"


def test_powerpoint_kpi_cards_and_diagnostic_slide_3(tmp_path):
    """Verify Slide 3 contains live KPI numbers and does not show 'No calculated KPIs available'."""
    out_file = str(tmp_path / "deck_kpi.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15}
    qa = {"critical_count": 0, "warning_count": 0, "health_score": 100.0, "issues": []}
    
    kpis = {
        "summary_kpis": {
            "target_achievement_pct": {"name": "Target Achievement", "value": 92.7, "unit": "%"},
            "productivity": {"name": "Productivity", "value": 14.72, "unit": "cases/FTE-period"},
            "utilisation_pct": {"name": "Utilisation", "value": 85.8, "unit": "%"},
            "backlog_change": {"name": "Backlog Change", "value": 785.0, "unit": "cases"}
        }
    }
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary=kpis,
        trend_summary=None,
        comparison_summary=None,
        insights=[],
        recommendations={},
        limitations=[],
        assumptions=[]
    )
    
    prs = Presentation(path)
    slide3 = prs.slides[2] # Slide 3
    slide3_text = " ".join([s.text_frame.text for s in slide3.shapes if s.has_text_frame])
    
    assert "No calculated KPIs available" not in slide3_text
    assert "92.7%" in slide3_text
    assert "14.72" in slide3_text
    assert "85.8%" in slide3_text
    assert "+785" in slide3_text or "785" in slide3_text
    assert "Executive Performance Diagnostic" in slide3_text


def test_powerpoint_approved_only_insights_slide_5(tmp_path):
    """Verify Slide 5 strictly includes approved insights and avoids unreviewed/pending ones."""
    out_file = str(tmp_path / "deck_insights.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15}
    qa = {"critical_count": 0, "warning_count": 0, "health_score": 100.0, "issues": []}
    
    insights = [
        {"id": "INS-1", "category": "Target", "title": "Approved Insight Title", "finding": "Confirmed target gap.", "status": "approved"},
        {"id": "INS-2", "category": "Capacity", "title": "Pending Unverified Finding", "finding": "Unverified assertion.", "status": "pending"}
    ]
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary={},
        trend_summary=None,
        comparison_summary=None,
        insights=insights,
        recommendations={},
        limitations=[],
        assumptions=[]
    )
    
    prs = Presentation(path)
    slide5 = prs.slides[4] # Slide 5
    slide5_text = " ".join([s.text_frame.text for s in slide5.shapes if s.has_text_frame])
    
    assert "Approved Insight Title" in slide5_text
    assert "Pending Unverified Finding" not in slide5_text


def test_powerpoint_action_table_and_limitations_slide_6(tmp_path):
    """Verify Slide 6 contains the structured action matrix table and analytical limitations."""
    out_file = str(tmp_path / "deck_actions.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15}
    qa = {"critical_count": 0, "warning_count": 0, "health_score": 100.0, "issues": []}
    
    recs = {
        "Act": [{"title": "Rebalance Queue", "action": "Deploy buffer intake capacity.", "owner": "Operations Lead", "timeline": "Immediate", "expected_impact": "Stabilized delivery"}],
        "Investigate": [{"title": "Review Case Mix", "action": "Analyze high complexity cases.", "owner": "Analyst", "timeline": "1-2 Weeks", "expected_impact": "Root causes"}],
        "Monitor": [],
        "Improve Reporting": []
    }
    limits = ["1 missing target observation handled non-parametrically."]
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary={},
        trend_summary=None,
        comparison_summary=None,
        insights=[],
        recommendations=recs,
        limitations=limits,
        assumptions=[]
    )
    
    prs = Presentation(path)
    slide6 = prs.slides[5] # Slide 6
    
    # Verify table existence
    tables = [s.table for s in slide6.shapes if s.has_table]
    assert len(tables) == 1
    table = tables[0]
    assert len(table.columns) == 5
    
    slide6_text = " ".join([s.text_frame.text for s in slide6.shapes if s.has_text_frame])
    assert "Key Analytical Limitations" in slide6_text
    assert "1 missing target observation" in slide6_text


def test_powerpoint_appendix_extension_10_slides(tmp_path):
    """Verify include_appendix=True generates a 10-slide extended technical presentation."""
    out_file = str(tmp_path / "deck_appendix.pptx")
    meta = {"filename": "test.csv", "row_count": 60, "column_count": 15}
    qa = {"critical_count": 1, "warning_count": 1, "health_score": 85.0, "issues": [{"severity": "CRITICAL", "field": "FTE", "description": "Zero denominator"}]}
    
    path = generate_powerpoint_presentation(
        output_filepath=out_file,
        project_metadata=meta,
        qa_report=qa,
        kpi_summary={},
        trend_summary=None,
        comparison_summary=None,
        insights=[],
        recommendations={},
        limitations=["Limitation 1"],
        assumptions=["Assumption 1"],
        include_appendix=True
    )
    
    prs = Presentation(path)
    assert len(prs.slides) == 10
    
    # Check Appendix slide titles
    slide7_text = " ".join([s.text_frame.text for s in prs.slides[6].shapes if s.has_text_frame])
    slide8_text = " ".join([s.text_frame.text for s in prs.slides[7].shapes if s.has_text_frame])
    slide9_text = " ".join([s.text_frame.text for s in prs.slides[8].shapes if s.has_text_frame])
    slide10_text = " ".join([s.text_frame.text for s in prs.slides[9].shapes if s.has_text_frame])
    
    assert "Appendix 1: Analytical Methodology & KPI Formulas" in slide7_text
    assert "Appendix 2: Quality Assurance & Anomaly Ledger" in slide8_text
    assert "Appendix 3: Governance Registers" in slide9_text
    assert "Appendix 4: Operational Segment Comparison Table" in slide10_text
