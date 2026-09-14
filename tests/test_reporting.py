"""Unit tests for Excel summary reporting module."""
import os
import pandas as pd
import openpyxl
from src.reporting import generate_excel_summary


def test_generate_excel_workbook():
    out_path = "outputs/reports/test_summary.xlsx"
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    prof = {"filename": "test.csv", "sheet_name": "Sheet1", "row_count": 2, "column_count": 2}
    qa = {"health_score": 100.0, "critical_count": 0, "warning_count": 0, "issues": []}
    kpis = {"summary_kpis": {}}
    
    path = generate_excel_summary(
        out_path, df, prof, qa, kpis, None, None, [], {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )
    assert os.path.exists(path)
    
    wb = openpyxl.load_workbook(path, read_only=True)
    assert "Executive_Summary" in wb.sheetnames
    wb.close()
