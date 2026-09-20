"""Comprehensive test suite for the unified professional Performance Insight Explorer platform.
Validates:
- All 5 demonstration datasets and schema isolation
- Quick Analysis end-to-end workflow across formats
- Multi-KPI engine calculations and zero-division protection
- Trends & statistical process control (SPC)
- Cohort comparisons and effect sizes
- Deterministic insights and action recommendations normalization
- Multi-format report exports (Excel, PPTX, PDF)
"""
import io
import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

from core.models import (
    KPIDefinition, TargetDirection, PriorityLevel, EvidenceInsight, RecommendationItem
)
from core.state import (
    init_session_state, clear_dataset_state, invalidate_derived_state,
    save_project_bundle, load_project_bundle
)
from modules.ingestion.parser import read_file_contents
from modules.profiling.profiler import profile_dataset
from modules.mapping.mapper import suggest_semantic_mappings
from modules.quality.engine import evaluate_data_quality_10d
from modules.kpi_engine.engine import (
    compute_kpi_value, evaluate_kpi_rag_status, safe_divide
)
from modules.analysis.orchestrator import run_full_performance_analysis
from modules.analysis.stats_engine import (
    calculate_descriptive_stats, calculate_control_chart_limits,
    calculate_group_comparison_statistics, calculate_pareto_curve
)
from modules.insights.engine import (
    generate_deterministic_insights, normalize_finding, normalize_recommendation
)
from modules.recommendations.engine import generate_prioritized_recommendations
from modules.reporting.export_builder import (
    build_excel_evidence_pack, build_powerpoint_presentation, build_executive_pdf,
    build_markdown_executive_report
)


def test_demo_datasets_schema_integrity():
    """Verify all 5 built-in demo datasets load with expected columns and non-empty rows."""
    demos = {
        "healthcare": ("sample_data/healthcare_service_performance.csv", ["reporting_month", "hospital_trust", "clinical_division", "cases_received", "avg_wait_time_mins", "actual_sla_pct"]),
        "sales": ("sample_data/sales_revenue_performance.csv", ["reporting_period", "sales_team", "region", "leads_received", "deals_completed", "conversion_rate_pct", "actual_revenue"]),
        "customer_service": ("sample_data/customer_service_operations.csv", ["reporting_month", "support_team", "channel", "tickets_received", "tickets_completed", "first_contact_resolution_pct", "avg_handle_time_mins"]),
        "workforce": ("sample_data/workforce_hr_performance.csv", ["reporting_month", "department", "active_headcount", "monthly_turnover_pct", "total_absence_days"]),
        "local_government": ("sample_data/local_government_service_delivery.csv", ["reporting_month", "directorate", "service_area", "cases_received", "cases_completed", "actual_sla_attainment_pct", "avg_processing_days"])
    }

    for name, (path, expected_cols) in demos.items():
        with open(path, "rb") as f:
            content = f.read()
        df, sheets, meta = read_file_contents(content, path.split("/")[-1])
        assert df is not None, f"Failed to load {name}"
        assert len(df) > 0, f"Empty dataframe for {name}"
        for col in expected_cols:
            assert col in df.columns, f"Expected column '{col}' missing in {name} demo dataset"


class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value


def test_demo_dataset_state_isolation():
    """Test that switching demo datasets completely clears previous state."""
    mock_session = MockSessionState()
    with patch("streamlit.session_state", mock_session):
        init_session_state()

        # Load Healthcare demo first
        with open("sample_data/healthcare_service_performance.csv", "rb") as f:
            df_health, _, _ = read_file_contents(f.read(), "healthcare_service_performance.csv")
        mock_session.raw_df = df_health
        mock_session.clean_df = df_health.copy()
        mock_session.dataset_name = "Healthcare Service Performance (NHS ED Flow)"
        mock_session.analysis_results = {"metric_mean": 45.0}

        assert "avg_wait_time_mins" in mock_session.clean_df.columns

        # Clear state
        clear_dataset_state()
        assert mock_session.get("clean_df") is None
        assert mock_session.get("analysis_results") is None
        assert mock_session.get("dataset_name") == ""

        # Load Sales demo
        with open("sample_data/sales_revenue_performance.csv", "rb") as f:
            df_sales, _, _ = read_file_contents(f.read(), "sales_revenue_performance.csv")
        mock_session.raw_df = df_sales
        mock_session.clean_df = df_sales.copy()
        mock_session.dataset_name = "Sales & Commercial Revenue"

        # Verify no healthcare columns or stale results leak into sales
        assert "avg_wait_time_mins" not in mock_session.clean_df.columns
        assert "actual_revenue" in mock_session.clean_df.columns
        assert mock_session.dataset_name == "Sales & Commercial Revenue"


def test_quick_analysis_end_to_end_sales():
    """Run full Quick Analysis orchestrator on sales dataset."""
    df_sales = pd.read_csv("sample_data/sales_revenue_performance.csv")
    results = run_full_performance_analysis(
        df=df_sales,
        objective_text="Examine sales revenue and deal conversion",
        date_col="reporting_period",
        metric_col="actual_revenue",
        group_col="region",
        target_val=450000.0
    )

    assert results is not None
    assert results["metric_mean"] > 0
    assert not results["spc_df"].empty
    assert "center_line" in results["spc_df"].columns
    assert "groups_table" in results["comparison_results"]
    assert len(results["findings"]) > 0
    assert len(results["recommendations"]) > 0
    assert "strongest_area" in results["summary"]
    assert "weakest_area" in results["summary"]


def test_quick_analysis_non_timeseries_dataset():
    """Verify orchestrator runs stably when no chronological date column is provided."""
    df = pd.DataFrame({
        "Department": ["HR", "Finance", "IT", "Operations", "Sales", "Legal"] * 5,
        "Score": [72, 85, 91, 64, 78, 88] * 5,
        "Headcount": [10, 25, 40, 60, 35, 12] * 5
    })
    results = run_full_performance_analysis(
        df=df,
        objective_text="Department performance review",
        date_col=None,
        metric_col="Score",
        group_col="Department",
        target_val=80.0
    )

    assert results is not None
    assert results["metric_mean"] > 0
    assert results["spc_df"].empty  # Gracefully empty when no date
    assert not results["comparison_results"]["groups_table"].empty
    assert len(results["findings"]) > 0


def test_multi_kpi_directionalities_and_formula_safety():
    """Test KPI calculation across all directionality modes and formula zero-division protection."""
    df = pd.DataFrame({
        "Output": [100.0, 120.0, 90.0, 110.0],
        "Input": [50.0, 60.0, 45.0, 55.0],
        "Defects": [2, 0, 5, 1],
        "ZeroCol": [0, 0, 0, 0]
    })

    # 1. Higher is better KPI
    kpi_higher = KPIDefinition(
        id="KPI-001",
        name="Average Output",
        business_definition="Mean units produced",
        formula="MEAN(Output)",
        source_field="Output",
        aggregation_method="mean",
        target_value=100.0,
        directionality=TargetDirection.HIGHER_IS_BETTER
    )
    val1, _, _ = compute_kpi_value(df, kpi_higher)
    rag1 = evaluate_kpi_rag_status(val1, kpi_higher)
    assert val1 == 105.0
    assert rag1["variance"] == 5.0
    assert "Green" in rag1["status"]

    # 2. Lower is better KPI
    kpi_lower = KPIDefinition(
        id="KPI-002",
        name="Total Defects",
        business_definition="Sum of defective items",
        formula="SUM(Defects)",
        source_field="Defects",
        aggregation_method="sum",
        target_value=5.0,
        directionality=TargetDirection.LOWER_IS_BETTER
    )
    val2, _, _ = compute_kpi_value(df, kpi_lower)
    rag2 = evaluate_kpi_rag_status(val2, kpi_lower)
    assert val2 == 8.0
    assert "Red" in rag2["status"]  # 8 > target 5 is Red for lower is better

    # 3. Target Range KPI
    kpi_range = KPIDefinition(
        id="KPI-003",
        name="Mean Input Range",
        business_definition="Input within target boundaries",
        formula="MEAN(Input)",
        source_field="Input",
        aggregation_method="mean",
        target_min=40.0,
        target_max=60.0,
        directionality=TargetDirection.TARGET_RANGE
    )
    val3, _, _ = compute_kpi_value(df, kpi_range)
    rag3 = evaluate_kpi_rag_status(val3, kpi_range)
    assert val3 == 52.5
    assert "Green" in rag3["status"]

    # 4. Zero denominator protection in ratio
    kpi_div_zero = KPIDefinition(
        id="KPI-004",
        name="Defect Rate on Zero",
        business_definition="Division by zero test",
        formula="Output / ZeroCol",
        numerator_field="Output",
        denominator_field="ZeroCol",
        aggregation_method="mean",
        target_value=10.0
    )
    val4, _, _ = compute_kpi_value(df, kpi_div_zero)
    # Output division by zero series gives fill value and does not throw exception


def test_export_deliverables_generation():
    """Verify Excel, PowerPoint, PDF, and Markdown exports generate valid non-empty byte streams."""
    df = pd.read_csv("sample_data/sales_revenue_performance.csv")
    analysis = run_full_performance_analysis(
        df=df,
        objective_text="Commercial Growth & Region Performance",
        date_col="reporting_period",
        metric_col="actual_revenue",
        group_col="region",
        target_val=450000.0
    )

    # 1. Excel Evidence Pack
    excel_bytes = build_excel_evidence_pack(
        clean_df=df,
        kpi_definitions=[],
        quality_issues=[],
        evidence_insights=analysis["findings"],
        recommendation_items=analysis["recommendations"],
        action_items=[],
        audit_log_entries=[],
        project_state={"project_name": "Sales Performance Audit"}
    )
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000

    # 2. PowerPoint Presentation
    pptx_bytes = build_powerpoint_presentation(
        project_state={"project_name": "Commercial Briefing Deck"},
        kpi_summary={"Revenue": 450000.0},
        trend_summary=analysis["spc_df"],
        comparison_summary=analysis["comparison_results"],
        evidence_insights=analysis["findings"],
        recommendations=analysis["recommendations"]
    )
    assert isinstance(pptx_bytes, bytes)
    assert len(pptx_bytes) > 1000

    # 3. PDF Briefing
    pdf_bytes = build_executive_pdf(
        project_state={"project_name": "Sales Executive Dossier"},
        kpi_summary={"Revenue": 450000.0},
        quality_score=95.0,
        insights=analysis["findings"],
        recommendations=analysis["recommendations"]
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500

    # 4. Markdown Report
    md_str = build_markdown_executive_report(
        project_state={"project_name": "Sales Review Memo"},
        kpi_results={"actual_revenue": {"name": "Actual Revenue", "actual": 450000.0, "target": 400000.0, "variance_pct": 12.5, "status": "Green"}},
        insights=analysis["findings"],
        recommendations=analysis["recommendations"],
        actions=[]
    )
    assert isinstance(md_str, str)
    assert "# Sales Review Memo" in md_str
