"""Tests for Multi-Dataset Architecture, Relationship Mapping, Assessment Brief Extractor, and Audit Logging.
"""
import io
import os
import pytest
import pandas as pd
import numpy as np
import streamlit as st

from src.brief_extractor import extract_assessment_brief, extract_docx_text, parse_questions_from_text
from src.relationships import validate_relationship, build_joined_analytical_model
from src.audit import AuditLogger
from src.state import (
    init_session_state,
    register_dataset,
    remove_dataset,
    set_primary_dataset,
    get_primary_dataset,
    get_reference_datasets,
    sync_analytical_model,
    clear_dataset_for_new_upload,
    get_working_df
)
from src.ingestion import load_file
from src.metrics import calculate_kpi_summary
from src.quality import run_quality_audit
from src.comparisons import compare_groups
from src.trends import calculate_trend_summary


def test_brief_extractor_on_question1_docx():
    """Test that Question1.docx is accurately parsed and all 5 questions are extracted."""
    if os.path.exists("Question1.docx"):
        res = extract_assessment_brief("Question1.docx")
        assert res["is_assessment_brief"] is True
        assert res["question_count"] >= 5
        assert any("Availability %" in q for q in res["questions"])
        assert any("Service" in q and "Band" in q for q in res["questions"])
        assert any("Service A and has a Band 3" in q or "Service A" in q for q in res["questions"])
        assert any("2025" in q and "Average" in q for q in res["questions"])
        assert any("dynamic table" in q or "filters" in q for q in res["questions"])


def test_parse_questions_from_text_helper():
    """Test text parsing helper with various question formatting styles."""
    sample_text = """
    Question 1: Compute the volume per FTE.
    Question 2: Calculate 90th percentile wait times.
    3. Determine bottleneck stages in the pipeline.
    """
    questions = parse_questions_from_text(sample_text)
    assert len(questions) == 3
    assert "Question 1: Compute the volume per FTE." in questions[0]
    assert "Question 2: Calculate 90th percentile wait times." in questions[1]
    assert "3. Determine bottleneck stages in the pipeline." in questions[2]


def test_audit_logger_kwarg_resilience():
    """Verify AuditLogger.log handles arbitrary kwargs such as role, dataset_id, rows, cols without error."""
    logger = AuditLogger()
    # Must not raise TypeError
    logger.log(
        "DATASET_REGISTERED",
        "Registered performance.xlsx",
        filename="performance.xlsx",
        role="Primary Analysis Dataset",
        rows=2539,
        cols=9,
        worksheet="Performance Data",
        dataset_id="performance.xlsx"
    )
    df = logger.get_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["event_type"] == "DATASET_REGISTERED"
    assert df.iloc[0]["row_count"] == "2539"
    assert "Primary Analysis Dataset" in df.iloc[0]["details"]


def test_validate_relationship_perfect_match():
    """Test relationship validation on perfect 1-to-1 / many-to-1 match."""
    df_left = pd.DataFrame({
        "User": ["U001", "U002", "U003", "U001", "U002"],
        "Month": ["2025-01", "2025-01", "2025-01", "2025-02", "2025-02"],
        "Hours": [100, 120, 110, 95, 130]
    })
    df_right = pd.DataFrame({
        "User": ["U001", "U002", "U003", "U004"],
        "Operational Area": ["Service A", "Service B", "Service A", "Service C"],
        "Band": ["Band 3", "Band 5", "Band 3", "Band 4"]
    })

    val = validate_relationship(df_left, "User", df_right, "User", "Perf", "Users")
    assert val["is_valid"] is True
    assert val["status"] == "OPTIMAL"
    assert val["matched_rows"] == 5
    assert val["unmatched_rows"] == 0
    assert val["match_rate"] == 1.0
    assert val["right_duplicates"] == 0


def test_validate_relationship_partial_match_and_duplicates():
    """Test relationship validation with unmatched rows and reference duplicates."""
    df_left = pd.DataFrame({
        "User": ["U001", "U002", "U999"],
        "Hours": [100, 120, 110]
    })
    df_right = pd.DataFrame({
        "User": ["U001", "U001", "U002"],
        "Service": ["Service A", "Service A Duplicate", "Service B"]
    })

    val = validate_relationship(df_left, "User", df_right, "User", "Perf", "Users")
    assert val["matched_rows"] == 2
    assert val["unmatched_rows"] == 1
    assert val["match_rate"] == pytest.approx(2 / 3, 0.01)
    assert val["right_duplicates"] == 1
    assert len(val["warnings"]) > 0


def test_build_joined_analytical_model_with_assessment_files():
    """Test end-to-end model building on actual assessment files (performance.xlsx + Users.xlsx)."""
    if os.path.exists("performance.xlsx") and os.path.exists("Users.xlsx"):
        raw_p, _, _ = load_file("performance.xlsx", "performance.xlsx", sheet_name="Performance Data")
        raw_u, _, _ = load_file("Users.xlsx", "Users.xlsx", sheet_name="Users")

        datasets = {
            "performance.xlsx": {
                "id": "performance.xlsx",
                "name": "performance.xlsx",
                "clean_df": raw_p
            },
            "Users.xlsx": {
                "id": "Users.xlsx",
                "name": "Users.xlsx",
                "clean_df": raw_u
            }
        }

        relationships = [{
            "left_dataset_id": "performance.xlsx",
            "left_key": "User",
            "right_dataset_id": "Users.xlsx",
            "right_key": "User",
            "join_type": "left"
        }]

        model_df, meta = build_joined_analytical_model(raw_p, relationships, datasets, compute_derived=True)

        assert meta["status"] == "SUCCESS"
        assert len(model_df) == len(raw_p) == 2539
        assert "Availability %" in model_df.columns
        assert "Service" in model_df.columns
        assert "Band" in model_df.columns
        assert "Service A & Band 3" in model_df.columns

        # Verify QA summary
        rel_qa = meta["relationship_qa"]
        assert rel_qa["analytical_rows"] == 2539
        assert rel_qa["user_match_coverage_pct"] == 100.0
        assert rel_qa["unmatched_users"] == 0
        assert rel_qa["duplicate_master_keys"] == 0
        assert rel_qa["missing_service_after_join"] == 0
        assert rel_qa["missing_band_after_join"] == 0
        assert rel_qa["is_verified"] is True

        # Verify Q3: Service A & Band 3
        true_q3_count = int((model_df["Service A & Band 3"] == True).sum())
        assert true_q3_count > 0

        # Verify Q4 benchmarks: 2025, Service B, Band 3 & Band 5
        model_df["_year"] = pd.to_datetime(model_df["Reporting Month"], errors="coerce").dt.year
        avail_col = "Availability %"
        model_df["_avail"] = pd.to_numeric(model_df[avail_col], errors="coerce")
        band_num = pd.to_numeric(model_df["Band"].astype(str).str.extract(r'(\d+)', expand=False), errors="coerce")

        q4_mask = (model_df["_year"] == 2025) & (model_df["Service"] == "Service B") & (band_num.isin([3, 5]))
        q4_valid = model_df.loc[q4_mask, "_avail"].dropna()

        assert len(q4_valid) == 796
        assert q4_valid.mean() == pytest.approx(0.789078, 0.0001)
        assert q4_valid.median() == pytest.approx(0.850513, 0.0001)

        # Verify Q5 benchmarks: Service B, Band 3 monthly in 2025
        q5_mask = (model_df["_year"] == 2025) & (model_df["Service"] == "Service B") & (band_num == 3)
        q5_df = model_df[q5_mask]
        q5_monthly = q5_df.groupby("Reporting Month")["_avail"].mean()
        assert q5_monthly.iloc[0] == pytest.approx(0.759288, 0.0001)  # Jan 2025 ≈ 75.93%
        assert q5_monthly.iloc[1] == pytest.approx(0.842556, 0.0001)  # Feb 2025 ≈ 84.26%


def test_multi_dataset_state_registry_and_downstream_integration():
    """Test state registry management and downstream analysis execution on joined model."""
    init_session_state()
    clear_dataset_for_new_upload(preserve_assessment_context=True)

    if os.path.exists("performance.xlsx") and os.path.exists("Users.xlsx"):
        raw_p, sheets_p, meta_p = load_file("performance.xlsx", "performance.xlsx", sheet_name="Performance Data")
        raw_u, sheets_u, meta_u = load_file("Users.xlsx", "Users.xlsx", sheet_name="Users")

        register_dataset("performance.xlsx", "performance.xlsx", "Primary Analysis Dataset", raw_p, sheets=sheets_p)
        register_dataset("Users.xlsx", "Users.xlsx", "Reference / Master Data", raw_u, sheets=sheets_u)

        st.session_state.relationships = [{
            "left_dataset_id": "performance.xlsx",
            "left_key": "User",
            "right_dataset_id": "Users.xlsx",
            "right_key": "User",
            "join_type": "left"
        }]

        sync_analytical_model()

        working_df = get_working_df()
        assert working_df is not None
        assert len(working_df) == 2539
        assert "Service" in working_df.columns
        assert "Band" in working_df.columns
        assert "Availability %" in working_df.columns

        # Verify Data Quality on joined model
        qa_rep = run_quality_audit(working_df, {})
        assert qa_rep["health_score"] >= 0

        # Verify Comparisons on joined model
        comp = compare_groups(working_df, "Service", "Availability %")
        assert comp.get("comparison_df") is not None
        assert len(comp["comparison_df"]) > 0

        # Verify Trends on joined model
        trend = calculate_trend_summary(working_df, "Reporting Month", "Availability %")
        assert trend is not None
