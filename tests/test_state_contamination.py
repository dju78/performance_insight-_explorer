"""Regression tests for state contamination prevention and downstream consistency.
Tests transition from sample data to assessment datasets, validating state invalidation,
canonical mapping prioritization, and accurate mathematical calculation across downstream modules.
"""
import pytest
import pandas as pd
import numpy as np
import streamlit as st

from src.state import (
    init_session_state,
    register_dataset,
    set_primary_dataset,
    sync_analytical_model,
    clear_dataset_for_new_upload,
    get_working_df,
    invalidate_derived_state
)
from src.relationships import build_joined_analytical_model
from src.mapping import suggest_mappings, validate_mappings
from src.trends import calculate_trends
from src.comparisons import compare_groups
from src.root_cause import analyze_root_cause_pillars
from src.insights import generate_rule_based_insights


def test_state_contamination_invalidation():
    """Verify that loading sample data and then transitioning to assessment data clears all derived state."""
    init_session_state()
    
    # 1. Simulate initial sample dataset
    sample_df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "Actual Output": [100, 120, 110],
        "Target Output": [100, 100, 100],
        "Team": ["Alpha", "Beta", "Gamma"]
    })
    
    register_dataset(
        dataset_id="sample_ds",
        name="Sample Data",
        role="Primary Analysis Dataset",
        raw_df=sample_df
    )
    
    st.session_state["confirmed_mappings"] = {
        "Date": "date",
        "Actual Output": "actual",
        "Target Output": "target",
        "Team": "team"
    }
    st.session_state["kpi_results"] = {"sample_metric": 100}
    st.session_state["trend_summary"] = {"trajectory": "Rising"}
    st.session_state["insights_list"] = [{"id": "OLD-01", "finding": "Stale sample finding"}]
    
    old_version = st.session_state.model_version
    
    # 2. Now load assessment dataset and build analytical model
    perf_df = pd.read_excel("performance.xlsx")
    users_df = pd.read_excel("Users.xlsx")
    
    register_dataset(
        dataset_id="perf",
        name="Performance",
        role="Primary Analysis Dataset",
        raw_df=perf_df
    )
    register_dataset(
        dataset_id="users",
        name="Users",
        role="Reference / Master Dataset",
        raw_df=users_df,
        key_field="User"
    )
    
    st.session_state.relationships = [{
        "left_dataset_id": "perf",
        "right_dataset_id": "users",
        "left_key": "User",
        "right_key": "User",
        "join_type": "left"
    }]
    
    sync_analytical_model()
    
    # 3. Assert state invalidation occurred
    assert st.session_state.model_version > old_version
    assert st.session_state["trend_summary"] is None
    assert st.session_state["comparison_summary"] is None
    
    # 4. Assert working df is the joined 2,539 row model
    working_df = get_working_df()
    assert working_df is not None
    assert len(working_df) == 2539
    
    # 5. Assert confirmed mappings contain canonical assessment columns, not stale sample columns
    confirmed = st.session_state.get("confirmed_mappings", {})
    assert "Actual Output" not in confirmed
    assert "Target Output" not in confirmed
    assert "Service_primary" not in confirmed
    assert "Band_primary" not in confirmed
    assert confirmed.get("Reporting Month") == "reporting_period"
    assert confirmed.get("Availability %") == "actual"
    assert confirmed.get("Service") == "team"
    assert confirmed.get("Band") == "category"


def test_trends_and_comparisons_on_joined_model():
    """Verify Trends and Comparisons calculate cleanly on canonical assessment fields."""
    perf_df = pd.read_excel("performance.xlsx")
    users_df = pd.read_excel("Users.xlsx")
    
    rel = [{
        "left_dataset_id": "perf",
        "right_dataset_id": "users",
        "left_key": "User",
        "right_key": "User",
        "join_type": "left"
    }]
    datasets = {
        "perf": {"clean_df": perf_df, "name": "Performance"},
        "users": {"clean_df": users_df, "name": "Users"}
    }
    joined_df, summary = build_joined_analytical_model(perf_df, rel, datasets, compute_derived=True)
    
    # Trend on Availability %
    trend_res = calculate_trends(joined_df, "Reporting Month", "Availability %", agg_func="mean")
    assert "error" not in trend_res
    assert trend_res["period_count"] == 13
    assert trend_res["start_value"] == pytest.approx(0.83, 0.01)
    
    # Trend on Contracted Hours
    trend_contract = calculate_trends(joined_df, "Reporting Month", "Contracted Hours", agg_func="mean")
    assert "error" not in trend_contract
    assert trend_contract["period_count"] == 13
    
    # Comparison on Service
    comp_serv = compare_groups(joined_df, "Service", "Availability %", agg_func="mean")
    assert "error" not in comp_serv
    assert comp_serv["group_count"] == 4
    assert set(comp_serv["comparison_df"]["group"]) == {"Service A", "Service B", "Service C", "Service D"}
    
    # Comparison on Band
    comp_band = compare_groups(joined_df, "Band", "Availability %", agg_func="mean")
    assert "error" not in comp_band
    assert comp_band["group_count"] == 3
    assert set(comp_band["comparison_df"]["group"]) == {"Band 3", "Band 4", "Band 5"}


def test_assessment_q1_to_q5_exact_mathematical_benchmarks():
    """Verify exact Q1-Q5 requirements on the joined analytical model."""
    perf_df = pd.read_excel("performance.xlsx")
    users_df = pd.read_excel("Users.xlsx")
    
    rel = [{
        "left_dataset_id": "perf",
        "right_dataset_id": "users",
        "left_key": "User",
        "right_key": "User",
        "join_type": "left"
    }]
    datasets = {
        "perf": {"clean_df": perf_df, "name": "Performance"},
        "users": {"clean_df": users_df, "name": "Users"}
    }
    joined_df, summary = build_joined_analytical_model(perf_df, rel, datasets, compute_derived=True)
    
    # Q1 Availability %
    assert len(joined_df) == 2539
    valid_avail = joined_df["Availability %"].dropna()
    assert len(valid_avail) == 2394
    assert (len(joined_df) - len(valid_avail)) == 145
    uncapped = int((valid_avail > 1.0).sum())
    assert uncapped == 376
    assert valid_avail.max() == pytest.approx(1.48956, 0.001)
    
    # Q2 Lookup
    qa = summary["relationship_qa"]
    assert qa["user_match_coverage_pct"] == 100.0
    assert qa["missing_service_after_join"] == 0
    assert qa["missing_band_after_join"] == 0
    assert qa["unmatched_users"] == 0
    
    # Q3 Service A & Band 3
    q3_series = joined_df["Service A & Band 3"]
    assert int(q3_series.sum()) == 856
    assert int((~q3_series).sum()) == 1683
    
    # Q4 2025 Service B Band 3 & 5
    df_q4 = joined_df.copy()
    df_q4["_year"] = pd.to_datetime(df_q4["Reporting Month"]).dt.year
    df_q4["_band_clean"] = pd.to_numeric(df_q4["Band"].astype(str).str.extract(r'(\d+)', expand=False), errors="coerce")
    
    mask = (df_q4["_year"] == 2025) & (df_q4["Service"] == "Service B") & (df_q4["_band_clean"].isin([3, 5]))
    q4_avail = df_q4.loc[mask, "Availability %"].dropna()
    
    assert len(q4_avail) == 796
    assert q4_avail.mean() == pytest.approx(0.789078, 0.0001)
    assert q4_avail.median() == pytest.approx(0.850513, 0.0001)
    
    # Q5 Service B Band 3 Monthly Trend
    df_q5 = df_q4[(df_q4["_year"] == 2025) & (df_q4["Service"] == "Service B") & (df_q4["_band_clean"] == 3)].copy()
    df_q5["_month"] = pd.to_datetime(df_q5["Reporting Month"]).dt.strftime("%Y-%m")
    m_grp = df_q5.groupby("_month")["Availability %"].mean()
    assert m_grp["2025-01"] == pytest.approx(0.759265, 0.0001)
    assert m_grp["2025-02"] == pytest.approx(0.842555, 0.0001)
