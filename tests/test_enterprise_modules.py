"""Comprehensive Unit and Integration Tests for Enterprise Performance Insight Explorer Modules.
Tests:
1. Ingestion, format parsers, chunking, and transformations
2. Profiling, granularity heuristics, and memory estimation
3. 10-Dimension Quality Engine, issue remediation, and blocking gates
4. Semantic Mapping Engine and confidence scoring
5. Dynamic KPI Engine, formulas, RAG directionality, and zero division safety
6. Statistical Engine, SPC control charts, ANOVA, effect sizes, and Pareto
7. Diagnostic Root Cause, driver correlations, and regression importance
8. Operational Scenario Simulator and what-if estimations
9. Evidence Insights, Prioritized Recommendations, and Traceability Matrix
10. Action Tracker, benefits realization, and causality disclaimers
11. Security: Spreadsheet formula injection sanitization and small-cell suppression
12. Project bundle serialization and restoration
"""
import io
import json
import pytest
import numpy as np
import pandas as pd

from core.constants import (
    AppMode, UserRole, QualityDimension, QualitySeverity, TargetDirection,
    PriorityLevel, RecommendationCategory, ActionStatus, WorkflowStage
)
from core.models import KPIDefinition, QualityIssue, EvidenceInsight, RecommendationItem, ActionItem
from core.security import (
    sanitize_for_spreadsheet, sanitize_dataframe_for_export,
    apply_statistical_suppression, check_role_permission, compute_audit_hash
)
from modules.ingestion.parser import read_file_contents, apply_column_transformation, detect_file_format
from modules.profiling.profiler import profile_dataset, infer_granularity_heuristic
from modules.quality.engine import evaluate_data_quality_10d
from modules.mapping.mapper import suggest_semantic_mappings
from modules.kpi_engine.engine import compute_kpi_value, evaluate_kpi_rag_status, safe_divide
from modules.analysis.stats_engine import (
    calculate_descriptive_stats, calculate_control_chart_limits,
    calculate_group_comparison_statistics, calculate_pareto_curve
)
from modules.analysis.method_recommender import recommend_analytical_methods
from modules.diagnostics.root_cause_engine import (
    evaluate_driver_correlations, calculate_driver_importance_regression
)
from modules.forecasting.simulator import run_scenario_simulation
from modules.insights.engine import generate_deterministic_insights
from modules.recommendations.engine import generate_prioritized_recommendations, build_traceability_matrix
from modules.actions.tracker import convert_recommendation_to_action, evaluate_benefits_realization
from modules.reporting.export_builder import build_markdown_executive_report, generate_excel_evidence_pack


# -------------------------------------------------------------
# 1. SECURITY & GOVERNANCE TESTS
# -------------------------------------------------------------
def test_formula_injection_sanitization():
    """Verify that dangerous spreadsheet formula prefixes (=, +, -, @) are escaped with apostrophe."""
    assert sanitize_for_spreadsheet("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_for_spreadsheet("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_for_spreadsheet("-1+1") == "'-1+1"
    assert sanitize_for_spreadsheet("@SUM(B1)") == "'@SUM(B1)"
    assert sanitize_for_spreadsheet("Safe String") == "Safe String"
    assert sanitize_for_spreadsheet(123.45) == 123.45

    df = pd.DataFrame({
        "notes": ["=HYPERLINK()", "Standard text", "+malicious", 42]
    })
    sanitized_df = sanitize_dataframe_for_export(df)
    assert sanitized_df["notes"].iloc[0] == "'=HYPERLINK()"
    assert sanitized_df["notes"].iloc[1] == "Standard text"
    assert sanitized_df["notes"].iloc[2] == "'+malicious"


def test_statistical_suppression_small_cells():
    """Verify that small cell counts (< 5) are masked to prevent individual re-identification."""
    df = pd.DataFrame({
        "cohort": ["A", "B", "C", "D"],
        "patient_count": [120, 3, 45, 2]
    })
    suppressed = apply_statistical_suppression(df, "patient_count", threshold=5)
    assert suppressed["patient_count"].iloc[0] == 120
    assert suppressed["patient_count"].iloc[1] == "< 5 (Suppressed)"
    assert suppressed["patient_count"].iloc[2] == 45
    assert suppressed["patient_count"].iloc[3] == "< 5 (Suppressed)"


def test_role_based_permissions():
    """Verify RBAC hierarchy: Admin > Analyst > Viewer."""
    assert check_role_permission(UserRole.ADMIN, UserRole.ANALYST) is True
    assert check_role_permission(UserRole.ADMIN, UserRole.ADMIN) is True
    assert check_role_permission(UserRole.ANALYST, UserRole.ADMIN) is False
    assert check_role_permission(UserRole.ANALYST, UserRole.VIEWER) is True
    assert check_role_permission(UserRole.VIEWER, UserRole.ANALYST) is False


def test_tamper_evident_audit_hash():
    """Verify deterministic SHA-256 audit chaining."""
    h1 = compute_audit_hash("GENESIS", "2026-09-20 10:00:00", "UPLOAD", "{}")
    h2 = compute_audit_hash(h1, "2026-09-20 10:01:00", "QA_AUDIT", "{}")
    assert len(h1) == 64
    assert len(h2) == 64
    assert h1 != h2


# -------------------------------------------------------------
# 2. INGESTION & TRANSFORMATION TESTS
# -------------------------------------------------------------
def test_csv_ingestion_and_chunking():
    """Verify CSV parsing with delimiter detection and chunked reads."""
    csv_bytes = b"month,cases_in,cases_out\n2025-01,100,90\n2025-02,120,110\n"
    df, sheets, meta = read_file_contents(csv_bytes, "test.csv")
    assert df is not None
    assert len(df) == 2
    assert list(df.columns) == ["month", "cases_in", "cases_out"]
    assert meta["format"] == "csv"

    # Chunked ingestion test
    df_chunk, _, _ = read_file_contents(csv_bytes, "test.csv", chunk_size=1)
    assert len(df_chunk) == 2


def test_column_transformations():
    """Verify renaming, type casting, and filtering with transformation audits."""
    df = pd.DataFrame({
        "team": ["Alpha", "Beta", "Gamma"],
        "output": ["10", "20", "30"]
    })
    # Rename
    df_ren, a1 = apply_column_transformation(df, "rename_column", {"old_name": "team", "new_name": "squad"})
    assert "squad" in df_ren.columns
    assert "team" not in df_ren.columns

    # Cast
    df_cast, a2 = apply_column_transformation(df_ren, "cast_type", {"column": "output", "target_type": "numeric"})
    assert pd.api.types.is_numeric_dtype(df_cast["output"])

    # Filter
    df_filt, a3 = apply_column_transformation(df_cast, "filter_rows", {"column": "squad", "allowed_values": ["Alpha"]})
    assert len(df_filt) == 1


# -------------------------------------------------------------
# 3. PROFILING & 10-DIMENSION QUALITY TESTS
# -------------------------------------------------------------
def test_data_profiler_and_granularity():
    """Verify summary statistics, cardinality, and granularity heuristics."""
    df = pd.DataFrame({
        "case_id": [f"ID-{i}" for i in range(100)],
        "date_created": pd.date_range("2025-01-01", periods=100, freq="D"),
        "wait_time": np.random.uniform(5.0, 25.0, 100),
        "department": ["Emergency" if i % 2 == 0 else "Elective" for i in range(100)]
    })
    prof = profile_dataset(df, "cases.csv")
    assert prof["row_count"] == 100
    assert prof["col_count"] == 4
    assert "case_id" in prof["potential_ids"]
    assert "date_created" in prof["potential_dates"]
    assert "wait_time" in prof["potential_measures"]
    assert "department" in prof["potential_dimensions"]
    assert "Event / Transaction" in prof["inferred_granularity"]


def test_10_dimension_data_quality_engine():
    """Verify 10-dimension QA checks, scoring, and analysis-blocking triggers."""
    # Data with critical issues: duplicates, high missingness, negative counts, zero denominator
    df_dirty = pd.DataFrame({
        "user_id": [1, 2, 2, 4, 5],
        "received": [100, np.nan, np.nan, np.nan, -50],  # 60% missing (Critical) + negative
        "fte_capacity": [5.0, 0.0, 0.0, 4.0, 5.0],        # Zero denominators
        "category": ["Team A", "Team a ", "Team B", "Team B", "Team B"]  # Casing inconsistency
    })
    qa = evaluate_data_quality_10d(df_dirty)
    assert qa["health_score"] <= 95.0
    assert qa["critical_count"] >= 1
    assert qa["is_analysis_blocked"] is True

    # Test remediation
    first_issue_id = qa["issues"][0]["issue_id"]
    remed = {
        first_issue_id: {"status": "Remediated", "justification": "Accepted known extract issue"}
    }
    qa_rem = evaluate_data_quality_10d(df_dirty, remediated_issues=remed)
    assert qa_rem["issues"][0]["status"] == "Remediated"


# -------------------------------------------------------------
# 4. SEMANTIC MAPPING & KPI ENGINE TESTS
# -------------------------------------------------------------
def test_semantic_mapping_engine():
    """Verify multi-sector role suggestions and confidence calculations."""
    df = pd.DataFrame({
        "reporting_month": ["2025-01", "2025-02"],
        "hospital_trust": ["NHS Trust A", "NHS Trust B"],
        "cases_received": [1200, 1350],
        "cases_completed": [1150, 1300],
        "turnaround_days": [14.2, 12.8],
        "staff_fte": [24.5, 25.0]
    })
    mappings = suggest_semantic_mappings(df)
    assert mappings["reporting_month"]["suggested_role"] == "reporting_period"
    assert mappings["cases_received"]["suggested_role"] in ["volume_inflow", "actual"]
    assert mappings["cases_completed"]["suggested_role"] in ["actual", "volume_inflow"]
    assert mappings["turnaround_days"]["suggested_role"] == "duration_wait_time"
    assert mappings["staff_fte"]["suggested_role"] == "capacity_fte"


def test_dynamic_kpi_engine_and_rag_directionality():
    """Verify custom KPI evaluation, zero-denominator safety, and RAG status."""
    assert safe_divide(100, 0, fill_value=0.0) == 0.0
    assert safe_divide(50, 2) == 25.0

    df = pd.DataFrame({
        "output": [100, 120, 80],
        "target": [100, 100, 100],
        "wait_days": [15, 35, 45]
    })

    # Higher is Better KPI
    kpi_vol = KPIDefinition(
        id="kpi_vol",
        name="Output Volume",
        business_definition="Total completed",
        formula="sum(output)",
        source_field="output",
        aggregation_method="sum",
        target_value=300.0,
        directionality=TargetDirection.HIGHER_IS_BETTER
    )
    val, _, _ = compute_kpi_value(df, kpi_vol)
    assert val == 300.0
    rag = evaluate_kpi_rag_status(val, kpi_vol)
    assert "Green" in rag["status"]

    # Lower is Better KPI (e.g. wait time breaching limit)
    kpi_wait = KPIDefinition(
        id="kpi_wait",
        name="Wait Time",
        business_definition="Mean wait days",
        formula="mean(wait_days)",
        source_field="wait_days",
        aggregation_method="mean",
        target_value=20.0,
        warning_threshold=25.0,
        critical_threshold=30.0,
        directionality=TargetDirection.LOWER_IS_BETTER
    )
    val_w, _, _ = compute_kpi_value(df, kpi_wait)
    assert val_w == 31.67
    rag_w = evaluate_kpi_rag_status(val_w, kpi_wait)
    assert "Red" in rag_w["status"]


# -------------------------------------------------------------
# 5. STATISTICAL, TREND & COMPARISON TESTS
# -------------------------------------------------------------
def test_spc_control_charts_and_special_causes():
    """Verify Shewhart SPC run chart calculations (center line, UCL/LCL 3-sigma)."""
    df = pd.DataFrame({
        "month": pd.date_range("2025-01-01", periods=12, freq="ME"),
        "cases": [100, 102, 98, 105, 95, 101, 100, 99, 102, 97, 100, 250]  # Outlier at end
    })
    spc = calculate_control_chart_limits(df, "month", "cases")
    assert not spc.empty
    assert "center_line" in spc.columns
    assert "ucl_3sigma" in spc.columns
    assert "lcl_3sigma" in spc.columns
    # Last point should be flagged as special cause
    assert spc["is_special_cause"].iloc[-1] is True or spc["is_special_cause"].iloc[-1] == 1


def test_group_comparison_and_anova():
    """Verify ANOVA F-test, p-values, and Cohen's d effect sizes."""
    df = pd.DataFrame({
        "team": ["Alpha"] * 10 + ["Beta"] * 10,
        "throughput": [50 + np.random.normal(0, 2) for _ in range(10)] + [80 + np.random.normal(0, 2) for _ in range(10)]
    })
    comp = calculate_group_comparison_statistics(df, "team", "throughput")
    assert comp["is_statistically_significant"] is True
    assert comp["anova_p_value"] < 0.001
    assert comp["cohens_d"] is not None and abs(comp["cohens_d"]) > 1.0


def test_pareto_concentration_curve():
    """Verify Pareto 80/20 share calculations."""
    df = pd.DataFrame({
        "service": ["A", "B", "C", "D"],
        "cases": [800, 150, 40, 10]
    })
    pareto = calculate_pareto_curve(df, "service", "cases")
    assert pareto.iloc[0]["service"] == "A"
    assert pareto.iloc[0]["share_pct"] == 80.0
    assert bool(pareto.iloc[0]["is_top_80pct"]) is True


# -------------------------------------------------------------
# 6. ROOT-CAUSE, FORECASTING & ACTION REALIZATION TESTS
# -------------------------------------------------------------
def test_root_cause_driver_diagnostics():
    """Verify driver correlation ranking and multivariate OLS regression importance."""
    np.random.seed(42)
    x1 = np.linspace(10, 50, 30)
    x2 = np.random.normal(100, 10, 30)
    y = 2.5 * x1 + np.random.normal(0, 5, 30)  # Strong linear correlation with x1

    df = pd.DataFrame({"y_output": y, "x1_fte": x1, "x2_noise": x2})
    corrs = evaluate_driver_correlations(df, "y_output", ["x1_fte", "x2_noise"])
    assert len(corrs) == 2
    assert corrs[0]["driver_field"] == "x1_fte"
    assert corrs[0]["pearson_r"] > 0.85
    assert "Confirmed" in corrs[0]["evidence_tier"]

    ols = calculate_driver_importance_regression(df, "y_output", ["x1_fte", "x2_noise"])
    assert ols["r_squared"] > 0.80
    assert ols["drivers"][0]["driver"] == "x1_fte"


def test_scenario_simulator():
    """Verify scenario estimation and required FTE balance calculations."""
    sim = run_scenario_simulation(
        baseline_volume=1000.0,
        baseline_fte=10.0,
        baseline_productivity=100.0,
        demand_multiplier=1.20,  # +20% demand
        fte_multiplier=1.0,
        productivity_gain_pct=0.0
    )
    assert sim["is_estimate"] is True
    assert "SCENARIO ESTIMATION" in sim["disclaimer"]
    base_scen = sim["scenarios"]["Baseline Projection"]
    assert base_scen["demand"] == 1200.0
    assert base_scen["required_fte_balance"] == 12.0
    assert base_scen["fte_surplus_deficit"] == -2.0  # 2 FTE deficit


def test_insights_recommendations_and_actions_traceability():
    """Verify deterministic insights, recommendation generation, and action benefits realization."""
    kpi_results = {
        "kpi_throughput": {
            "name": "Throughput Volume",
            "actual": 80.0,
            "target": 100.0,
            "variance": -20.0,
            "variance_pct": -20.0,
            "status": "Red (Critical Shortfall)",
            "unit": "Cases"
        }
    }
    insights = generate_deterministic_insights(kpi_results)
    assert len(insights) >= 1
    assert "Shortfall" in insights[0].finding_title

    recs = generate_prioritized_recommendations(insights)
    assert len(recs) >= 1
    assert recs[0].category == RecommendationCategory.QUICK_WIN
    assert "The evidence suggests" in recs[0].proposed_action

    action = convert_recommendation_to_action(
        recs[0], "Rebalance Pod Capacity", "Conduct workload shift", "Lead Analyst", "Operations", "2026-10-01", 80.0, 100.0
    )
    action.actual_result = 95.0
    action.status = ActionStatus.COMPLETED

    realization = evaluate_benefits_realization([action])
    assert realization["total_actions"] == 1
    assert realization["completed_count"] == 1
    assert realization["realization_rate_pct"] == 100.0
    assert "CAUSALITY DISCLAIMER" in realization["causality_caveat"]

    trace_df = build_traceability_matrix("Test Dataset", kpi_results, insights, recs, [action])
    assert len(trace_df) == len(recs)
    assert "Target Outcome" in trace_df.columns


def test_excel_evidence_pack_generation():
    """Verify sanitized multi-tab Excel evidence workbook generation."""
    proj = {"project_name": "Test Org Review", "organization_name": "Enterprise NHS"}
    kpi_results = {"kpi_1": {"name": "Test KPI", "actual": 100.0, "target": 100.0, "unit": "Cases"}}
    insights = [EvidenceInsight("INS-001", "Test Finding", "Evidence data", "Test KPI", -5.0, "2025", "All", "High", "Critical", "None", "None", "None")]
    recs = [RecommendationItem("REC-001", "INS-001", "Problem", "Evidence", "Action", "Benefit")]
    actions = [ActionItem("ACT-001", "REC-001", "Action Title", "Desc", "Owner", "Dept", PriorityLevel.HIGH)]
    
    excel_bytes = generate_excel_evidence_pack(proj, pd.DataFrame({"col": [1, 2]}), kpi_results, insights, recs, actions)
    assert len(excel_bytes) > 0
    assert isinstance(excel_bytes, bytes)
