"""Regression test suite for Trends page, SPC Run Charts, and index-like column protections.
Covers:
1. Same date and metric column (e.g. Unnamed: 0 or date_col == metric_col)
2. Unnamed: 0 and index-like column identification and exclusion
3. No valid date column
4. No numeric metric column
5. Invalid date strings (unparseable)
6. Only one valid period
7. All-null metric values
8. Mixed numeric and text metric values
9. Valid end-to-end date and numeric metric workflow
"""
import pytest
import numpy as np
import pandas as pd

from core.security import is_index_like_column
from modules.analysis.stats_engine import calculate_control_chart_limits, calculate_group_comparison_statistics
from modules.mapping.mapper import suggest_semantic_mappings
from src.trends import calculate_trends


def test_is_index_like_column():
    """Verify index-like column detection against Unnamed, index, and row-number patterns."""
    assert is_index_like_column("Unnamed: 0") is True
    assert is_index_like_column("Unnamed: 1") is True
    assert is_index_like_column("Unnamed: 0.1") is True
    assert is_index_like_column("index") is True
    assert is_index_like_column("idx") is True
    assert is_index_like_column("row_num") is True
    assert is_index_like_column("row_id") is True
    assert is_index_like_column("level_0") is True
    
    # Real business columns
    assert is_index_like_column("order_date") is False
    assert is_index_like_column("sales_revenue") is False
    assert is_index_like_column("patient_wait_time") is False
    assert is_index_like_column("department") is False
    
    # Sequential series check
    seq_series = pd.Series(range(100))
    assert is_index_like_column("id", seq_series) is True
    
    non_seq_series = pd.Series([10, 42, 5, 99, 12])
    assert is_index_like_column("sales", non_seq_series) is False


def test_same_date_and_metric_column():
    """Verify engine returns empty DataFrame safely when date_col == metric_col without throwing exceptions."""
    df = pd.DataFrame({
        "Unnamed: 0": [0, 1, 2, 3, 4],
        "date": pd.date_range("2024-01-01", periods=5, freq="D"),
        "revenue": [100.0, 120.0, 110.0, 130.0, 150.0]
    })
    
    # Both set to Unnamed: 0
    res1 = calculate_control_chart_limits(df, "Unnamed: 0", "Unnamed: 0")
    assert isinstance(res1, pd.DataFrame)
    assert res1.empty
    
    # Both set to date
    res2 = calculate_control_chart_limits(df, "date", "date")
    assert isinstance(res2, pd.DataFrame)
    assert res2.empty
    
    # Legacy trends module check
    res3 = calculate_trends(df, "Unnamed: 0", "Unnamed: 0")
    assert "error" in res3


def test_unnamed_index_column_exclusion_in_mapper():
    """Verify that semantic mapper recognizes Unnamed: 0 as index_identifier and excludes it."""
    df = pd.DataFrame({
        "Unnamed: 0": range(20),
        "transaction_date": pd.date_range("2024-01-01", periods=20, freq="D"),
        "amount": np.random.uniform(10, 100, 20)
    })
    
    mappings = suggest_semantic_mappings(df)
    assert mappings["Unnamed: 0"]["suggested_role"] == "index_identifier"
    assert mappings["transaction_date"]["suggested_role"] == "date"


def test_no_valid_date_column():
    """Verify handling when date column has completely missing or non-existent columns."""
    df = pd.DataFrame({
        "category": ["A", "B", "C"],
        "metric": [10, 20, 30]
    })
    res = calculate_control_chart_limits(df, "non_existent_date", "metric")
    assert isinstance(res, pd.DataFrame)
    assert res.empty


def test_no_numeric_metric_column():
    """Verify handling when metric column contains non-convertible text strings."""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5, freq="D"),
        "text_metric": ["low", "high", "medium", "none", "n/a"]
    })
    res = calculate_control_chart_limits(df, "date", "text_metric")
    assert isinstance(res, pd.DataFrame)
    assert res.empty


def test_invalid_date_strings():
    """Verify handling when date values cannot be parsed to datetimes."""
    df = pd.DataFrame({
        "bad_dates": ["not_a_date", "also_bad", "corrupt_val", "foo", "bar"],
        "metric": [100, 200, 300, 400, 500]
    })
    res = calculate_control_chart_limits(df, "bad_dates", "metric")
    assert isinstance(res, pd.DataFrame)
    assert res.empty


def test_single_period_dataset():
    """Verify control chart limits calculation when only a single period exists."""
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-01"],
        "metric": [100.0, 150.0]
    })
    res = calculate_control_chart_limits(df, "date", "metric")
    assert isinstance(res, pd.DataFrame)
    assert len(res) == 1
    assert res["center_line"].iloc[0] == 125.0
    assert res["ucl_3sigma"].iloc[0] == 125.0
    assert res["lcl_3sigma"].iloc[0] == 125.0
    assert not res["is_special_cause"].iloc[0]


def test_all_null_metric():
    """Verify handling when metric column contains all NaNs."""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5, freq="D"),
        "metric": [np.nan, np.nan, np.nan, np.nan, np.nan]
    })
    res = calculate_control_chart_limits(df, "date", "metric")
    assert isinstance(res, pd.DataFrame)
    assert res.empty


def test_mixed_numeric_and_text_metric():
    """Verify robust coercion when metric column contains mixed numbers and strings."""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=6, freq="D"),
        "metric": ["100.5", "N/A", 120.0, "null", 140.2, 110.0]
    })
    res = calculate_control_chart_limits(df, "date", "metric")
    assert isinstance(res, pd.DataFrame)
    assert len(res) == 4  # 4 valid numeric entries
    assert "center_line" in res.columns
    assert "ucl_3sigma" in res.columns
    assert "lcl_3sigma" in res.columns


def test_valid_date_and_numeric_metric_workflow():
    """Verify full SPC calculation workflow on clean multi-period data."""
    dates = pd.date_range("2024-01-01", periods=12, freq="ME")
    values = [100.0, 102.0, 98.0, 105.0, 101.0, 99.0, 150.0, 103.0, 97.0, 102.0, 100.0, 101.0]
    df = pd.DataFrame({"reporting_date": dates, "performance_score": values})
    
    spc_df = calculate_control_chart_limits(df, "reporting_date", "performance_score", aggregation="mean")
    assert not spc_df.empty
    assert len(spc_df) == 12
    assert "center_line" in spc_df.columns
    assert "ucl_3sigma" in spc_df.columns
    assert "lcl_3sigma" in spc_df.columns
    assert "is_special_cause" in spc_df.columns
    assert "mom_change_pct" in spc_df.columns
    
    # 150.0 is an outlier (>3-sigma)
    outliers = spc_df[spc_df["is_special_cause"] == True]
    assert len(outliers) >= 1
    assert float(outliers["performance_score"].iloc[0]) == 150.0
