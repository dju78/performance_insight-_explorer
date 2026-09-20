"""Test suite for the simplified 4-section performance analysis workflow.
Covers:
1. End-to-end execution of run_full_performance_analysis
2. User objective and multi-line specific questions parsing
3. Metric, date, and cohort aggregation
4. Target achievement calculation
5. Findings and recommendations generation tied to user objective
6. Export pack construction
"""
import pytest
import numpy as np
import pandas as pd

from modules.analysis.orchestrator import run_full_performance_analysis
from modules.reporting.export_builder import (
    build_excel_evidence_pack,
    build_powerpoint_presentation,
    build_executive_pdf
)


@pytest.fixture
def sample_performance_df():
    """Generate realistic operational dataset with dates, cohorts, and metrics."""
    np.random.seed(42)
    n = 60
    dates = pd.date_range("2024-01-01", periods=12, freq="ME")
    cohorts = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta"]
    
    records = []
    for i in range(n):
        records.append({
            "record_id": f"REC-{i:04d}",
            "period_date": dates[i % len(dates)],
            "team_name": cohorts[i % len(cohorts)],
            "response_time_min": float(np.random.normal(20, 5)),
            "case_volume": int(np.random.randint(50, 200)),
            "escalation_count": int(np.random.randint(0, 15))
        })
    return pd.DataFrame(records)


def test_run_full_performance_analysis_basic(sample_performance_df):
    """Verify run_full_performance_analysis executes smoothly and populates all summary sections."""
    df = sample_performance_df
    res = run_full_performance_analysis(
        df=df,
        objective_text="Identify why customer response times are increasing and compare team performance",
        specific_questions="Which teams are slowest?\nAre times worsening over time?",
        date_col="period_date",
        metric_col="response_time_min",
        group_col="team_name",
        target_val=18.0
    )

    assert "summary" in res
    assert "main_result" in res["summary"]
    assert "strongest_area" in res["summary"]
    assert "weakest_area" in res["summary"]
    assert "target_achievement" in res["summary"]
    
    assert res["target_achievement_pct"] is not None
    assert len(res["specific_questions"]) == 2
    assert not res["spc_df"].empty
    assert not res["comparison_results"]["groups_table"].empty
    assert len(res["findings"]) > 0
    assert len(res["recommendations"]) > 0


def test_orchestrator_handles_empty_and_edge_cases():
    """Verify orchestrator handles empty data and missing parameters gracefully."""
    res_empty = run_full_performance_analysis(None)
    assert "error" in res_empty

    # Non-existent columns
    df = pd.DataFrame({"a": [1, 2, 3]})
    res_bad = run_full_performance_analysis(df, date_col="missing_date", metric_col="missing_metric")
    assert "summary" in res_bad
    assert res_bad["spc_df"].empty


def test_export_hub_generation(sample_performance_df):
    """Verify Excel, PowerPoint, and PDF export builders succeed with orchestrator outputs."""
    df = sample_performance_df
    res = run_full_performance_analysis(
        df=df,
        objective_text="Executive Performance Review",
        date_col="period_date",
        metric_col="response_time_min",
        group_col="team_name",
        target_val=20.0
    )

    # 1. Excel Pack
    excel_bytes = build_excel_evidence_pack(
        clean_df=df,
        kpi_definitions=[],
        quality_issues=res["qa_report"].get("issues", []),
        evidence_insights=res["findings"],
        recommendation_items=res["recommendations"],
        action_items=[],
        audit_log_entries=[],
        project_state={"project_name": "Test Project"}
    )
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 500

    # 2. PowerPoint
    pptx_bytes = build_powerpoint_presentation(
        project_state={"project_name": "Test Project"},
        kpi_summary={"Metric": "response_time_min"},
        trend_summary=res["spc_df"],
        comparison_summary=res["comparison_results"],
        evidence_insights=res["findings"],
        recommendations=res["recommendations"]
    )
    assert isinstance(pptx_bytes, bytes)
    assert len(pptx_bytes) > 1000

    # 3. PDF
    pdf_bytes = build_executive_pdf(
        project_state={"project_name": "Test Project"},
        kpi_summary={"Metric": "response_time_min"},
        quality_score=res["health_score"],
        insights=res["findings"],
        recommendations=res["recommendations"]
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
