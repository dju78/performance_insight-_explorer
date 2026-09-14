"""Unit tests for Group Comparisons module."""
import os
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.comparisons import compare_groups
from src.visualisations import create_comparison_bar


def test_compare_groups_ranking():
    """Verify rate normalisation and ranking calculation."""
    df = pd.DataFrame({
        "Team": ["Alpha", "Alpha", "Beta", "Beta", "Gamma"],
        "Completions": [50, 60, 30, 40, 90],
        "FTE": [5, 5, 5, 5, 10]
    })
    res = compare_groups(df, "Team", "Completions", denominator_col="FTE")
    assert res["top_performer"] == "Alpha"  # 110/10 = 11.0 rate vs Gamma 90/10 = 9.0 vs Beta 70/10 = 7.0
    assert res["bottom_performer"] == "Beta"
    assert "Gamma" in res["small_sample_groups"]  # N=1 < 5
    assert res["top_group"] == "Alpha"
    assert res["bottom_group"] == "Beta"


def test_compare_groups_agg_choices():
    """Verify sum vs mean aggregation choices."""
    df = pd.DataFrame({
        "Team": ["Team A", "Team A", "Team B", "Team B"],
        "Volume": [100, 200, 140, 150]
    })
    # Sum: Team A = 300, Team B = 290 -> Team A top
    res_sum = compare_groups(df=df, group_col="Team", metric_col="Volume", agg_func="sum")
    assert res_sum["top_group"] == "Team A"
    assert res_sum["top_value"] == 300.0
    assert res_sum["bottom_group"] == "Team B"
    assert res_sum["bottom_value"] == 290.0
    
    # Mean: Team A = 150, Team B = 145 -> Team A top
    res_mean = compare_groups(df=df, group_col="Team", metric_col="Volume", agg_func="mean")
    assert res_mean["top_group"] == "Team A"
    assert res_mean["top_value"] == 150.0
    assert res_mean["bottom_group"] == "Team B"
    assert res_mean["bottom_value"] == 145.0


def test_compare_groups_positional_agg_choice_safe():
    """Verify that passing agg_choice as 5th positional argument or string does NOT trigger TypeError."""
    df = pd.DataFrame({
        "Team": ["Team 1", "Team 2"],
        "Output": [10, 20]
    })
    # Legacy/positional style: compare_groups(df, "Team", "Output", None, "sum")
    res = compare_groups(df, "Team", "Output", None, "sum")
    assert "error" not in res
    assert res["group_count"] == 2
    assert res["aggregation"] == "sum"


def test_compare_groups_contract_schema():
    """Verify comparison_df always includes all required contract columns."""
    df = pd.DataFrame({
        "Region": ["North", "North", "South", "East"],
        "Cases": [100, 150, 200, 80],
        "Staff": [10, 15, 20, 10]
    })
    res = compare_groups(df, group_col="Region", metric_col="Cases", denominator_col="Staff", agg_func="sum")
    comp_df = res["comparison_df"]
    
    expected_cols = [
        "group", "sample_count", "total_sum", "mean", "median", "std", "min", "max",
        "value", "normalised_rate", "var_from_benchmark", "var_pct_benchmark", "is_small_sample", "rank"
    ]
    for col in expected_cols:
        assert col in comp_df.columns, f"Required column '{col}' missing from comparison_df"
        
    assert res["top_group"] == comp_df.iloc[0]["group"]
    assert res["top_value"] == comp_df.iloc[0]["value"]
    assert res["bottom_group"] == comp_df.iloc[-1]["group"]
    assert res["bottom_value"] == comp_df.iloc[-1]["value"]
    
    # Check chart generation with comparison_df
    fig = create_comparison_bar(comp_df, x_col="group", y_col="value")
    assert fig is not None


def test_compare_groups_zero_denominator_safety():
    """Verify that zero in denominator column returns valid dataframe with NaN rates without error."""
    df = pd.DataFrame({
        "Team": ["Alpha", "Beta"],
        "Output": [100, 50],
        "FTE": [0, 0]
    })
    res = compare_groups(df, group_col="Team", metric_col="Output", denominator_col="FTE")
    assert "error" not in res
    comp_df = res["comparison_df"]
    assert comp_df["normalised_rate"].isna().all()


def test_compare_groups_assessment_scenarios():
    """Verify the 4 operational assessment scenarios against performance_insight_explorer_test_data.csv."""
    csv_path = os.path.join(ROOT, "sample_data", "performance_insight_explorer_test_data.csv")
    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    
    # Scenario A: Group = Service_Team, Metric = Demand_Received, Denominator = None, Aggregation = Sum
    res_a = compare_groups(df=df, group_col="Service_Team", metric_col="Demand_Received", denominator_col=None, agg_func="sum")
    assert "error" not in res_a
    assert res_a["group_count"] >= 5
    assert res_a["top_value"] > 0
    
    # Scenario B: Group = Service_Team, Metric = Demand_Received, Denominator = None, Aggregation = Mean
    res_b = compare_groups(df=df, group_col="Service_Team", metric_col="Demand_Received", denominator_col=None, agg_func="mean")
    assert "error" not in res_b
    assert res_b["group_count"] >= 5
    assert res_b["aggregation"] == "mean"
    
    # Scenario C: Group = Service_Team, Metric = Cases_Closed, Denominator = Available_FTE, Aggregation = Sum
    res_c = compare_groups(df=df, group_col="Service_Team", metric_col="Cases_Closed", denominator_col="Available_FTE", agg_func="sum")
    assert "error" not in res_c
    assert res_c["group_count"] >= 5
    assert "normalised_rate" in res_c["comparison_df"].columns
    
    # Scenario D: Group = Region, Metric = Median_Turnaround_Days, Denominator = None, Aggregation = Mean
    res_d = compare_groups(df=df, group_col="Region", metric_col="Median_Turnaround_Days", denominator_col=None, agg_func="mean")
    assert "error" not in res_d
    assert res_d["group_count"] >= 5
    assert res_d["aggregation"] == "mean"
