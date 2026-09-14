"""Unit tests for ingestion module."""
import os
import pytest
import pandas as pd
from src.ingestion import load_file, get_excel_sheet_names, IngestionError


def test_load_csv():
    df, sheets, meta = load_file("sample_data/dataset_a_team_month.csv", "dataset_a_team_month.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert meta["file_format"] == "CSV"
    assert "columns" in meta


def test_load_excel_and_sheets():
    sheets = get_excel_sheet_names("sample_data/dataset_a_team_month.xlsx")
    assert len(sheets) >= 1
    assert "Monthly_Performance" in sheets
    
    df, loaded_sheets, meta = load_file("sample_data/dataset_a_team_month.xlsx", "dataset_a_team_month.xlsx", sheet_name="Monthly_Performance")
    assert len(df) > 0
    assert meta["active_sheet"] == "Monthly_Performance"


def test_invalid_file_extension():
    with pytest.raises(IngestionError):
        load_file("test_fake.pdf", "test_fake.pdf")
