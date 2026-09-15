"""Tests for Multi-Dataset Architecture, Relationship Mapping, and Assessment Brief Extractor.
"""
import io
import os
import pytest
import pandas as pd
import numpy as np
import streamlit as st

from src.brief_extractor import extract_assessment_brief, extract_docx_text, parse_questions_from_text
from src.relationships import validate_relationship, build_joined_analytical_model
from src.state import (
    init_session_state,
    register_dataset,
    remove_dataset,
    set_primary_dataset,
    get_primary_dataset,
    get_reference_datasets,
    sync_analytical_model,
    clear_dataset_for_new_upload
)
from src.ingestion import load_file


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
        assert len(model_df) == len(raw_p)
        assert "Availability %" in model_df.columns or "Availabilty %" in model_df.columns
        assert "Service" in model_df.columns
        assert "Band" in model_df.columns
        assert "Service A & Band 3" in model_df.columns

        # Verify Q4 benchmarks
        model_df["_year"] = pd.to_datetime(model_df["Reporting Month"], errors="coerce").dt.year
        avail_col = "Availability %" if "Availability %" in model_df.columns else "Availabilty %"
        model_df["_avail"] = pd.to_numeric(model_df[avail_col], errors="coerce")
        band_num = pd.to_numeric(model_df["Band"].astype(str).str.extract(r'(\d+)', expand=False), errors="coerce")

        q4_mask = (model_df["_year"] == 2025) & (model_df["Service"] == "Service B") & (band_num.isin([3, 5]))
        q4_valid = model_df.loc[q4_mask, "_avail"].dropna()

        assert len(q4_valid) == 796
        assert q4_valid.mean() == pytest.approx(0.789078, 0.0001)
        assert q4_valid.median() == pytest.approx(0.850513, 0.0001)


def test_multi_dataset_state_registry():
    """Test state registry management for datasets."""
    init_session_state()
    clear_dataset_for_new_upload(preserve_assessment_context=True)

    df1 = pd.DataFrame({"User": ["A", "B"], "Val": [10, 20]})
    df2 = pd.DataFrame({"User": ["A", "B"], "Area": ["North", "South"]})

    register_dataset("ds1", "Primary.csv", "Primary Analysis Dataset", df1)
    register_dataset("ds2", "Reference.csv", "Reference / Master Data", df2)

    assert len(st.session_state.datasets) == 2
    primary = get_primary_dataset()
    assert primary is not None
    assert primary["id"] == "ds1"

    refs = get_reference_datasets()
    assert len(refs) == 1
    assert refs[0]["id"] == "ds2"

    remove_dataset("ds2")
    assert len(st.session_state.datasets) == 1
    assert len(get_reference_datasets()) == 0
