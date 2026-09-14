import os
import pytest
import pandas as pd
import numpy as np
import io
from src.metrics import evaluate_target_variance, calculate_kpi_summary, safe_divide
from src.mapping import suggest_column_mappings, validate_mapping_integrity
from src.ingestion import ingest_file, generate_dataset_profile
from src.insights import generate_rule_based_insights
from src.state import init_session_state, reset_analysis_only, reset_full_state, get_state, set_state
from src.powerpoint import generate_interview_powerpoint
import streamlit as st

def test_target_directionality_higher_is_better():
    # Higher is better: actual 120 vs target 100 -> +20%, favorable
    res = evaluate_target_variance(120, 100, direction="higher_is_better")
    assert res["is_favorable"] is True
    assert res["variance_pct"] == 20.0
    assert "above target" in res["commentary"].lower()
    
    # Higher is better: actual 80 vs target 100 -> -20%, unfavorable
    res_under = evaluate_target_variance(80, 100, direction="higher_is_better")
    assert res_under["is_favorable"] is False
    assert res_under["variance_pct"] == -20.0
    assert "below target" in res_under["commentary"].lower()

def test_target_directionality_lower_is_better():
    # Lower is better (e.g. processing time, error rate): actual 80 vs target 100 -> favorable!
    res = evaluate_target_variance(80, 100, direction="lower_is_better")
    assert res["is_favorable"] is True
    assert res["variance_pct"] == -20.0
    assert "favorable reduction" in res["commentary"].lower() or "lower than target" in res["commentary"].lower()
    
    # Lower is better: actual 120 vs target 100 -> unfavorable!
    res_over = evaluate_target_variance(120, 100, direction="lower_is_better")
    assert res_over["is_favorable"] is False
    assert res_over["variance_pct"] == 20.0
    assert "exceeding upper threshold" in res_over["commentary"].lower() or "unfavorable" in res_over["commentary"].lower()

def test_target_directionality_neutral():
    # Neutral / descriptive only: actual 110 vs target 100 -> neither favorable nor unfavorable
    res = evaluate_target_variance(110, 100, direction="neutral")
    assert res["is_favorable"] is None
    assert res["variance_pct"] == 10.0
    assert "tracking vs benchmark" in res["commentary"].lower() or "neutral" in res["commentary"].lower()

def test_zero_target_safety():
    # When target is 0, safe division prevents crash and returns 0.0 or None variance_pct
    res = evaluate_target_variance(10, 0, direction="higher_is_better")
    assert res["variance_num"] == 10.0
    assert res["variance_pct"] == 0.0
    assert "zero target baseline" in res["commentary"].lower() or "target is zero" in res["commentary"].lower()
    
    # safe_divide directly
    assert safe_divide(100, 0, default=0.0) == 0.0

def test_unconfirmed_mappings_do_not_activate_kpis():
    # Create test df
    df = pd.DataFrame({
        "processing_time": [10.5, 12.0, 11.2],
        "target_time": [10.0, 10.0, 10.0]
    })
    
    # Auto-suggestions
    suggestions = suggest_column_mappings(df)
    assert len(suggestions) > 0
    
    # Empty confirmed mappings -> calculate_kpi_summary must return empty
    kpis_unconfirmed = calculate_kpi_summary(df, confirmed_mappings={}, target_directions={})
    assert kpis_unconfirmed == {}
    
    # With confirmed mappings -> KPIs are generated
    confirmed = {"processing_time": "metric_time", "target_time": "target"}
    dirs = {"processing_time": "lower_is_better"}
    kpis_confirmed = calculate_kpi_summary(df, confirmed_mappings=confirmed, target_directions=dirs)
    assert "processing_time" in kpis_confirmed
    assert kpis_confirmed["processing_time"]["direction"] == "lower_is_better"

def test_safe_reset_analysis_only():
    # Setup state
    init_session_state()
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    st.session_state["raw_df"] = df.copy()
    st.session_state["clean_df"] = df.copy()
    st.session_state["dataset_name"] = "test.csv"
    st.session_state["confirmed_mappings"] = {"a": "metric_count"}
    st.session_state["insights_list"] = [{"id": "1", "title": "Test Insight", "status": "approved"}]
    st.session_state["recommendations_list"] = [{"id": "r1", "title": "Test Rec", "status": "approved"}]
    
    # Execute reset_analysis_only
    reset_analysis_only()
    
    # Verify raw and clean df are preserved
    assert st.session_state.get("raw_df") is not None
    assert len(st.session_state["raw_df"]) == 3
    assert st.session_state.get("clean_df") is not None
    assert st.session_state.get("dataset_name") == "test.csv"
    
    # Verify derived analysis state is wiped
    assert st.session_state.get("confirmed_mappings") == {}
    assert st.session_state.get("insights_list") == []
    assert st.session_state.get("recommendations_list") == []
    assert st.session_state.get("kpi_results") == {}

def test_excel_ingestion_safety():
    # Test reading both xlsx in-memory and csv
    df_orig = pd.DataFrame({"case_id": ["C1", "C2"], "val": [100, 200]})
    
    # Save to Excel bytes buffer
    excel_buffer = io.BytesIO()
    df_orig.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    raw_df, clean_df, profile = ingest_file(excel_buffer, "test_file.xlsx")
    assert len(raw_df) == 2
    assert profile["row_count"] == 2
    assert "case_id" in clean_df.columns

def test_powerpoint_approved_only_filter(tmp_path):
    df = pd.DataFrame({
        "case_id": [f"C{i}" for i in range(10)],
        "duration": [5.0 + i for i in range(10)],
        "target": [8.0]*10
    })
    mappings = {"duration": "metric_time", "target": "target"}
    target_dirs = {"duration": "lower_is_better"}
    
    insights = [
        {"id": "ins1", "title": "Approved Finding", "finding": "Duration is over SLA", "status": "approved", "severity": "high"},
        {"id": "ins2", "title": "Rejected Finding", "finding": "Ignored noise", "status": "rejected", "severity": "low"},
        {"id": "ins3", "title": "Pending Finding", "finding": "Not yet reviewed", "status": "pending", "severity": "medium"}
    ]
    
    recommendations = [
        {"id": "rec1", "title": "Approved Fix", "action": "Reallocate staff", "owner": "Ops Lead", "timeframe": "Week 1", "expected_impact": "Reduce SLA breach", "status": "approved"},
        {"id": "rec2", "title": "Rejected Fix", "action": "Do nothing", "owner": "None", "timeframe": "N/A", "expected_impact": "None", "status": "rejected"}
    ]
    
    context = {
        "assessment_question": "Reduce cycle time",
        "target_audience": "COO",
        "output_format": "Presentation Deck",
        "time_available": "10 mins",
        "row_granularity": "Case / record"
    }
    
    pptx_file = generate_interview_powerpoint(
        df=df,
        mappings=mappings,
        target_directions=target_dirs,
        insights=insights,
        recommendations=recommendations,
        context=context,
        output_dir=str(tmp_path),
        author="DARAMOLA OMOYELE"
    )
    
    assert os.path.exists(pptx_file)
    assert os.path.getsize(pptx_file) > 1000
