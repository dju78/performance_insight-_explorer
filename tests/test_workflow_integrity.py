import os
import sys
import pytest
import pandas as pd
import numpy as np
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.state import (
    init_session_state,
    compute_dataset_fingerprint,
    reset_derived_state_for_new_dataset,
    reset_analysis_only
)
from src.mapping import suggest_mappings, suggest_column_mappings
from src.quality import run_structural_qa, run_semantic_qa, run_quality_audit
from src.trends import calculate_trends, classify_trajectory
from src.recommendations import RecommendationEngine
from src.metrics import calculate_kpi_summary


def test_dataset_switch_invalidates_derived_state():
    """Test Item 1 & 8: Switching datasets clears mappings, KPIs, insights, and recommendations."""
    init_session_state()
    
    # 1. Load Dataset A
    df_a = pd.DataFrame({"month": ["2025-01", "2025-02"], "vol": [100, 120]})
    fp_a = compute_dataset_fingerprint(df_a, "dataset_a.csv")
    reset_derived_state_for_new_dataset(fp_a)
    st.session_state["raw_df"] = df_a
    st.session_state["clean_df"] = df_a
    st.session_state["confirmed_mappings"] = {"vol": "completed"}
    st.session_state["kpi_results"] = {"vol": {"actual": 110}}
    st.session_state["insights_list"] = [{"id": "INS-1", "title": "A insight", "status": "approved"}]
    st.session_state["recommendations_list"] = [{"id": "REC-1", "title": "A rec", "status": "approved"}]
    
    assert st.session_state["dataset_fingerprint"] == fp_a
    assert len(st.session_state["confirmed_mappings"]) == 1
    assert len(st.session_state["insights_list"]) == 1
    
    # 2. Switch to Dataset B
    df_b = pd.DataFrame({"period": ["Q1", "Q2"], "cases_closed": [500, 600], "team": ["T1", "T2"]})
    fp_b = compute_dataset_fingerprint(df_b, "dataset_b.csv")
    assert fp_a != fp_b
    
    # Trigger reset on dataset change
    reset_derived_state_for_new_dataset(fp_b)
    st.session_state["raw_df"] = df_b
    st.session_state["clean_df"] = df_b
    st.session_state["suggested_mappings"] = suggest_mappings(df_b)
    
    # Confirm old derived state is completely eradicated
    assert st.session_state["dataset_fingerprint"] == fp_b
    assert st.session_state["confirmed_mappings"] == {}
    assert st.session_state["kpi_results"] == {}
    assert st.session_state["insights_list"] == []
    assert st.session_state["recommendations_list"] == []
    
    # Confirm new suggestions match Dataset B fields
    assert "cases_closed" in st.session_state["suggested_mappings"]
    assert st.session_state["suggested_mappings"]["cases_closed"]["suggested_role"] == "completed"
    assert "vol" not in st.session_state["suggested_mappings"]


def test_no_recommendations_without_approved_insights():
    """Test Item 6: No recommendations or unsupported triage default created without approved insights."""
    # When 0 approved insights:
    recs = RecommendationEngine.generate_recommendations([])
    assert recs == []
    
    # When approved insight is provided:
    approved_insights = [{
        "id": "INS-001",
        "title": "Delivery Shortfall",
        "finding": "Output trailed target benchmark by 12.5%.",
        "evidence": "Total closed 350 vs target 400.",
        "recommendation": "Implement fast-track triage queue.",
        "status": "approved"
    }]
    recs = RecommendationEngine.generate_recommendations(approved_insights)
    assert len(recs) == 1
    assert recs[0]["linked_insight_id"] == "INS-001"
    assert recs[0]["status"] == "pending"
    assert recs[0]["expected_impact"] == ""  # Never fabricates percentage claims


def test_trajectory_classification_mixed_and_sustained():
    """Test Item 5: Trajectory classification prevents Sustained Rise on mixed/volatile trends."""
    # 1. Both rises and falls -> Mixed / Volatile
    df_mixed = pd.DataFrame({
        "diff_abs": [10.0, 15.0, 20.0, -25.0, -30.0, -20.0]
    })
    traj_mixed = classify_trajectory(df_mixed, net_pct_change=-30.0)
    assert traj_mixed == "Mixed / Volatile"
    
    # 2. Consistent rise -> Sustained Rise
    df_rise = pd.DataFrame({
        "diff_abs": [10.0, 12.0, 15.0, 14.0, 18.0]
    })
    traj_rise = classify_trajectory(df_rise, net_pct_change=45.0)
    assert traj_rise == "Sustained Rise"
    
    # 3. Consistent fall -> Sustained Fall
    df_fall = pd.DataFrame({
        "diff_abs": [-10.0, -12.0, -15.0, -8.0, -14.0]
    })
    traj_fall = classify_trajectory(df_fall, net_pct_change=-50.0)
    assert traj_fall == "Sustained Fall"
    
    # 4. Small fluctuation within ±3% -> Broadly Stable
    df_stable = pd.DataFrame({
        "diff_abs": [1.0, -1.0, 0.5, -0.5]
    })
    traj_stable = classify_trajectory(df_stable, net_pct_change=0.5)
    assert traj_stable == "Broadly Stable"


def test_two_stage_quality_assurance():
    """Test Item 3: Stage A structural QA runs without mappings; Stage B semantic QA validates business rules."""
    df = pd.DataFrame({
        "case_id": ["C1", "C1", "C2", "C3"], # duplicate ID
        "date_str": ["2025-01-01", "2025-01-02", "INVALID_DATE", "2025-01-04"],
        "open_wip": [100, 100, 100, 100],
        "received": [50, 60, 40, 50],
        "closed": [40, 50, 30, 40],
        "closing_wip": [110, 110, 250, 110], # Gap in row 2: 100+40-30=110 != 250
        "target": [0, 50, 50, 50]            # zero target
    })
    
    # Stage A Structural QA (no mappings)
    struct_qa = run_structural_qa(df)
    assert struct_qa["stage"] == "Structural QA"
    assert struct_qa["total_issues"] > 0
    # Found invalid date
    inv_date_issues = [i for i in struct_qa["issues"] if "date" in i["title"].lower()]
    assert len(inv_date_issues) > 0
    
    # Stage B Semantic QA (with mappings)
    mappings = {
        "case_id": "record_id",
        "open_wip": "opening_backlog",
        "received": "received",
        "closed": "completed",
        "closing_wip": "closing_backlog",
        "target": "target"
    }
    sem_qa = run_semantic_qa(df, mappings)
    assert sem_qa["stage"] == "Semantic QA"
    # Found duplicate record ID
    dup_id_issues = [i for i in sem_qa["issues"] if "duplicate record id" in i["title"].lower()]
    assert len(dup_id_issues) > 0
    # Found zero target denominator risk
    zero_den_issues = [i for i in sem_qa["issues"] if "zero values in mapped denominator" in i["title"].lower()]
    assert len(zero_den_issues) > 0
    # Found backlog gap
    gap_issues = [i for i in sem_qa["issues"] if "backlog flow reconciliation" in i["title"].lower()]
    assert len(gap_issues) > 0


def test_fifteen_column_test_dataset_mappings():
    """Test Item 2 & 11: All 15 columns from performance_insight_explorer_test_data.csv match expected roles."""
    csv_path = os.path.join(ROOT, "sample_data", "performance_insight_explorer_test_data.csv")
    assert os.path.exists(csv_path), "Test data CSV must exist"
    
    df = pd.read_csv(csv_path)
    assert len(df) == 60
    assert len(df.columns) == 15
    
    sugs = suggest_mappings(df)
    expected_mapping = {
        "Period": "reporting_period",
        "Service_Team": "team",
        "Region": "location",
        "Demand_Received": "received",
        "Cases_Closed": "completed",
        "Output_Target": "target",
        "Open_Work_Start": "opening_backlog",
        "Open_Work_End": "closing_backlog",
        "Available_FTE": "fte",
        "Scheduled_Hours": "hours_available",
        "Productive_Hours": "hours_used",
        "Median_Turnaround_Days": "processing_time",
        "Quality_Score_Pct": "quality_measure",
        "Customer_Satisfaction_Pct": "customer_measure",
        "Unit_Cost_GBP": "cost"
    }
    
    for col, expected_role in expected_mapping.items():
        assert col in sugs, f"Column '{col}' must be analyzed"
        actual_role = sugs[col]["suggested_role"]
        confidence = sugs[col]["confidence"]
        assert actual_role == expected_role, f"Column '{col}' mapped to '{actual_role}', expected '{expected_role}'"
        assert confidence >= 0.70, f"Confidence for '{col}' was {confidence}, expected >= 0.70"
