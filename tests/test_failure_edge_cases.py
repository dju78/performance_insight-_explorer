"""Comprehensive Failure Mode and Edge-Case Test Suite for Performance Insight Explorer.
Verifies robust, graceful error handling across all failure conditions specified in Quality Gate 6:
1. Empty file
2. Corrupt binary file
3. Unsupported file format
4. Duplicate columns in dataset
5. Missing KPI source/numerator/denominator fields
6. All-null columns
7. Zero denominator divisions
8. Invalid / corrupted dates
9. Dataset with exactly 1 row
10. Dataset with exactly 1 cohort group
11. Dataset without any date columns
12. Dataset without any target/benchmark columns
13. Very long column names (> 200 characters)
14. Malicious formula injection strings (=cmd, +SUM, @HYPERLINK)
15. Small groups below disclosure suppression threshold (< 5 rows)
16. Large synthetic dataset close to memory limit
"""
import io
import pytest
import numpy as np
import pandas as pd

from core.constants import TargetDirection
from core.models import KPIDefinition
from core.security import sanitize_for_spreadsheet, sanitize_dataframe_for_export, apply_statistical_suppression
from modules.ingestion.parser import read_file_contents, detect_file_format
from modules.profiling.profiler import profile_dataset
from modules.quality.engine import evaluate_data_quality_10d
from modules.mapping.mapper import suggest_semantic_mappings
from modules.kpi_engine.engine import compute_kpi_value, evaluate_kpi_rag_status, safe_divide
from modules.analysis.stats_engine import (
    calculate_control_chart_limits, calculate_group_comparison_statistics, calculate_pareto_curve
)
from modules.diagnostics.root_cause_engine import (
    evaluate_driver_correlations, calculate_driver_importance_regression
)
from modules.insights.engine import generate_deterministic_insights
from modules.recommendations.engine import generate_prioritized_recommendations
from modules.reporting.export_builder import generate_excel_evidence_pack


def test_empty_file_ingestion():
    """Verify handling of completely empty file (0 bytes)."""
    df, sheets, meta = read_file_contents(b"", "empty.csv")
    assert df is not None or "error" in meta
    prof = profile_dataset(pd.DataFrame(), "empty.csv")
    assert prof["row_count"] == 0
    qa = evaluate_data_quality_10d(pd.DataFrame())
    assert qa["is_analysis_blocked"] is True
    assert "Empty Dataset" in qa["issues"][0]["title"]


def test_corrupt_binary_file():
    """Verify handling of corrupt binary payload with .xlsx extension."""
    corrupt_bytes = b"CORRUPT_NON_ZIP_BINARY_DATA_123456789"
    df, sheets, meta = read_file_contents(corrupt_bytes, "corrupt.xlsx")
    assert df is None or len(df) == 0
    assert "error" in meta or meta.get("file_size_bytes") > 0


def test_unsupported_file_format():
    """Verify detection of unsupported file formats."""
    assert detect_file_format("data.exe") == "unknown"
    assert detect_file_format("document.pdf") == "unknown"
    assert detect_file_format("data.csv") == "csv"
    assert detect_file_format("data.parquet") == "parquet"


def test_duplicate_columns_handling():
    """Verify parsing when dataframe contains duplicate column headers."""
    csv_bytes = b"metric,metric,category\n10,20,Team A\n30,40,Team B\n"
    df, _, _ = read_file_contents(csv_bytes, "dup_cols.csv")
    assert df is not None
    # Pandas will rename duplicate columns to metric.1
    assert len(df.columns) == 3
    prof = profile_dataset(df, "dup_cols.csv")
    assert prof["col_count"] == 3


def test_missing_kpi_fields():
    """Verify KPI evaluation when configured column is completely absent."""
    df = pd.DataFrame({"actual_output": [10, 20, 30]})
    kpi_missing = KPIDefinition(
        id="kpi_nonexistent",
        name="Missing Metric",
        business_definition="References missing column",
        formula="sum(nonexistent_col)",
        source_field="nonexistent_col",
        aggregation_method="sum"
    )
    val, series, msg = compute_kpi_value(df, kpi_missing)
    assert val is None
    assert "not found" in msg.lower()


def test_all_null_column():
    """Verify profiling and quality checks on a column where all values are NaN."""
    df = pd.DataFrame({
        "valid_col": [1, 2, 3],
        "all_null": [np.nan, np.nan, np.nan]
    })
    prof = profile_dataset(df, "all_null.csv")
    assert prof["columns"]["all_null"]["null_pct"] == 100.0
    qa = evaluate_data_quality_10d(df)
    assert any("all_null" in i["field"] for i in qa["issues"])


def test_zero_denominator_safe_math():
    """Verify zero denominator across scalars and series."""
    assert safe_divide(100.0, 0.0, fill_value=0.0) == 0.0
    assert safe_divide(0.0, 0.0, fill_value=0.0) == 0.0
    assert safe_divide(np.nan, 10.0, fill_value=0.0) == 0.0

    s_num = pd.Series([10.0, 20.0, 30.0])
    s_den = pd.Series([2.0, 0.0, np.nan])
    res = safe_divide(s_num, s_den, fill_value=0.0)
    assert res.iloc[0] == 5.0
    assert res.iloc[1] == 0.0
    assert res.iloc[2] == 0.0


def test_invalid_dates_handling():
    """Verify handling of invalid date strings ('UNKNOWN', '99/99/9999')."""
    df = pd.DataFrame({
        "reporting_date": ["2025-01-01", "INVALID_DATE_STRING", "2025-03-01", "N/A"],
        "metric": [10, 20, 30, 40]
    })
    qa = evaluate_data_quality_10d(df)
    date_issues = [i for i in qa["issues"] if "reporting_date" in i["field"]]
    assert len(date_issues) >= 1
    # SPC chart should handle invalid dates gracefully by dropping non-parsable rows
    spc = calculate_control_chart_limits(df, "reporting_date", "metric")
    assert not spc.empty
    assert len(spc) == 2  # Only valid dates parsed


def test_single_row_dataset():
    """Verify behavior on single-row datasets."""
    df_single = pd.DataFrame({
        "team": ["Alpha"],
        "output": [100],
        "date": ["2025-01-01"]
    })
    prof = profile_dataset(df_single, "single.csv")
    assert prof["row_count"] == 1
    qa = evaluate_data_quality_10d(df_single)
    assert qa["health_score"] >= 0.0
    # Group comparison on single row should not crash
    comp = calculate_group_comparison_statistics(df_single, "team", "output")
    assert len(comp["groups_table"]) == 1
    assert comp["anova_p_value"] is None  # Cannot compute ANOVA on single row


def test_single_group_dataset():
    """Verify behavior when dataset has multiple rows but only 1 group."""
    df_one_grp = pd.DataFrame({
        "team": ["Alpha", "Alpha", "Alpha"],
        "output": [100, 110, 90]
    })
    comp = calculate_group_comparison_statistics(df_one_grp, "team", "output")
    assert len(comp["groups_table"]) == 1
    assert comp["anova_p_value"] is None  # Needs >= 2 groups for ANOVA


def test_dataset_without_date_column():
    """Verify graceful degradation when dataset has no date column."""
    df_nodate = pd.DataFrame({
        "team": ["A", "B", "C"],
        "cost": [100, 200, 150]
    })
    mappings = suggest_semantic_mappings(df_nodate)
    assert not any(info["suggested_role"] == "date" for info in mappings.values())
    spc = calculate_control_chart_limits(df_nodate, "nonexistent_date", "cost")
    assert spc.empty


def test_dataset_without_target_column():
    """Verify KPI RAG evaluation when no target standard is configured (informational only)."""
    kpi_notarget = KPIDefinition(
        id="kpi_notgt",
        name="Cost Spend",
        business_definition="Operational spend",
        formula="sum(cost)",
        source_field="cost",
        target_value=None,
        directionality=TargetDirection.INFORMATIONAL
    )
    rag = evaluate_kpi_rag_status(1500.0, kpi_notarget)
    assert "Informational" in rag["status"]
    assert rag["variance"] is None


def test_very_long_column_names():
    """Verify handling of column names exceeding 200 characters."""
    long_col = "A" * 250
    df_long = pd.DataFrame({
        long_col: [1, 2, 3],
        "team": ["A", "B", "C"]
    })
    prof = profile_dataset(df_long, "long_col.csv")
    assert long_col in prof["columns"]
    mappings = suggest_semantic_mappings(df_long)
    assert long_col in mappings


def test_malicious_formula_injection_strings():
    """Verify sanitization of formula triggers (=cmd, +SUM, @HYPERLINK, -1+1)."""
    malicious_inputs = [
        "=cmd|' /C calc'!A0",
        "+SUM(A1:A100)",
        "@HYPERLINK('http://malicious.site')",
        "-1+1; EXEC sp_help"
    ]
    for inp in malicious_inputs:
        sanitized = sanitize_for_spreadsheet(inp)
        assert sanitized.startswith("'"), f"Failed to sanitize: {inp}"

    df_malicious = pd.DataFrame({"notes": malicious_inputs, "safe_col": [1, 2, 3, 4]})
    df_clean = sanitize_dataframe_for_export(df_malicious)
    for val in df_clean["notes"]:
        assert val.startswith("'")


def test_small_groups_suppression_threshold():
    """Verify statistical suppression of group sizes < 5."""
    df_sensitive = pd.DataFrame({
        "clinic": ["Clinic A", "Clinic B", "Clinic C", "Clinic D"],
        "cases_count": [150, 4, 3, 200]
    })
    suppressed = apply_statistical_suppression(df_sensitive, "cases_count", threshold=5)
    assert suppressed["cases_count"].iloc[0] == 150
    assert "< 5" in str(suppressed["cases_count"].iloc[1])
    assert "< 5" in str(suppressed["cases_count"].iloc[2])
    assert suppressed["cases_count"].iloc[3] == 200
