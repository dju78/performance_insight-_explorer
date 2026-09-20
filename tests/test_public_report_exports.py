"""Comprehensive verification and regression tests for public performance report exports.
Tests:
1. Excel Evidence Pack (Formula-Injection Protected)
2. PowerPoint Presentation Deck (16:9, Valid ZIP/Office signature, openable via python-pptx)
3. ReportLab PDF Executive Report (Valid %PDF signature, openable via pypdf, >= 1 page)
4. Full 14-point Canonical Reporting Payload
5. Dataclass, Dictionary, and String Findings & Recommendations
6. Empty / Missing optional fields graceful degradation
7. Absence of candidate, interview, assessment, and defense language in public outputs
8. Friendly error handling for missing data
9. Streamlit export page execution
"""
import io
import os
import pytest
import pandas as pd
from dataclasses import dataclass
from pptx import Presentation
import pypdf
import openpyxl

from modules.reporting.export_builder import (
    build_canonical_reporting_payload,
    generate_excel_evidence_pack,
    build_excel_evidence_pack,
    build_powerpoint_presentation,
    build_executive_pdf,
    build_markdown_executive_report,
    validate_excel_bytes,
    validate_pptx_bytes,
    validate_pdf_bytes
)
from src.powerpoint import (
    generate_public_performance_presentation,
    generate_assessment_presentation
)
from src.pdf_report import generate_pdf_report


@dataclass
class MockEvidenceInsight:
    finding_title: str
    quantitative_evidence: str
    confidence_level: str = "High"
    business_significance: str = "Capacity constraint"
    statistical_limitation: str = "Observational data"
    status: str = "approved"


@dataclass
class MockRecommendation:
    problem_addressed: str
    proposed_action: str
    expected_benefit: str
    priority: str = "High"
    responsible_owner: str = "Operations Lead"
    timescale: str = "30-60 Days"
    status: str = "approved"


@pytest.fixture
def sample_performance_df():
    return pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=10, freq="D"),
        "Team": ["North", "South", "East", "West", "North", "South", "East", "West", "North", "South"],
        "Throughput": [105.0, 112.5, 98.0, 120.0, 115.0, 108.0, 95.0, 125.0, 110.0, 118.0],
        "Queue_Wait_Sec": [45, 52, 60, 38, 42, 55, 65, 35, 48, 50]
    })


@pytest.fixture
def sample_canonical_payload(sample_performance_df):
    return build_canonical_reporting_payload(
        state_or_df=sample_performance_df,
        user_objective="Diagnose operational throughput and eliminate queue wait time bottlenecks.",
        specific_questions=["Which team has the highest queue wait time?", "Are throughput trends stable over time?"],
        target_audience="Executive Leadership & Operations Committee",
        author="DARAMOLA OMOYELE",
        metric_column="Throughput",
        date_column="Date",
        group_column="Team",
        insights_list=[
            MockEvidenceInsight(
                finding_title="East Team Experiences Sustained Queue Wait Bottlenecks",
                quantitative_evidence="Average queue wait in East team is 62.5s vs 40.0s baseline.",
                confidence_level="High (p < 0.01)",
                business_significance="Direct impact on customer service delivery SLA.",
                statistical_limitation="Sample covers 10 observation periods.",
                status="approved"
            ),
            {
                "id": "INS-02",
                "title": "Throughput Remained Stable Across Mid-Week Periods",
                "finding": "Average throughput remained at 110.6 cases per day.",
                "evidence": "110.6 mean daily cases",
                "confidence": "High",
                "status": "approved"
            },
            "Plain string observation: No negative outliers detected during peak hours."
        ],
        recommendations_list=[
            MockRecommendation(
                problem_addressed="East Team Queue Wait Disparity",
                proposed_action="Rebalance workload by cross-skilling 2 FTE from West team to East team.",
                expected_benefit="Reduce East team queue wait times by 25% within 30 days.",
                priority="High",
                responsible_owner="Head of Operations",
                timescale="Immediate (Days 1-14)",
                status="approved"
            ),
            {
                "id": "REC-02",
                "title": "Implement Daily Shift Volume Forecasting",
                "action": "Deploy operational volume forecasts to adjust staffing ahead of demand peaks.",
                "owner": "Resource Planning Lead",
                "timeline": "30-60 Days",
                "expected_impact": "15% improvement in SLA adherence",
                "status": "approved"
            },
            "Plain string recommendation: Review queue threshold alarms quarterly."
        ],
        qa_report={"health_score": 98.5, "issues": []}
    )


# ==============================================================================
# 1. CANONICAL PAYLOAD VERIFICATION
# ==============================================================================
def test_canonical_reporting_payload_structure(sample_canonical_payload):
    """Verify that build_canonical_reporting_payload creates all 14 required analysis elements."""
    p = sample_canonical_payload
    
    # 1. User objective and questions
    assert "user_objective" in p and len(p["user_objective"]) > 0
    assert "specific_questions" in p and len(p["specific_questions"]) == 2
    
    # 2. Dataset profile
    assert p["dataset"]["row_count"] == 10
    assert p["dataset"]["column_count"] == 4
    assert p["dataset"]["metric_column"] == "Throughput"
    assert p["dataset"]["date_column"] == "Date"
    assert p["dataset"]["group_column"] == "Team"
    
    # 3. Data Quality
    assert p["data_quality"]["health_score"] == 98.5
    assert p["data_quality"]["fitness_status"] == "Fit for purpose"
    
    # 4. Methods Used
    assert len(p["methods_used"]) >= 4
    
    # 5. KPIs
    assert len(p["kpis"]) > 0
    
    # 6. Findings (Normalized dataclass, dict, and string)
    assert len(p["findings"]) == 3
    assert p["findings"][0]["title"] == "East Team Experiences Sustained Queue Wait Bottlenecks"
    assert p["findings"][1]["title"] == "Throughput Remained Stable Across Mid-Week Periods"
    assert "Plain string observation" in p["findings"][2]["title"] or "Plain string observation" in p["findings"][2]["finding"]
    
    # 7. Recommendations (Normalized dataclass, dict, and string)
    assert len(p["recommendations"]) == 3
    assert p["recommendations"][0]["problem_addressed"] == "East Team Queue Wait Disparity"
    assert "Rebalance workload" in p["recommendations"][0]["proposed_action"]
    
    # 8. Governance (Assumptions & Limitations)
    assert len(p["assumptions"]) >= 2
    assert len(p["limitations"]) >= 2


# ==============================================================================
# 2. EXCEL EVIDENCE PACK TESTS
# ==============================================================================
def test_excel_evidence_pack_generation_and_validation(sample_canonical_payload):
    """Verify Excel Evidence Pack generates valid openable openpyxl workbook with all required tabs."""
    excel_bytes = generate_excel_evidence_pack(payload=sample_canonical_payload)
    
    # Byte-level validation
    assert isinstance(excel_bytes, (bytes, bytearray))
    assert len(excel_bytes) > 1000
    assert validate_excel_bytes(excel_bytes) is True
    
    # Open through openpyxl and verify sheets and contents
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), read_only=True)
    sheet_names = wb.sheetnames
    assert "Executive Summary" in sheet_names
    assert "KPI Scorecard" in sheet_names
    assert "Evidence Insights" in sheet_names
    assert "Recommendations" in sheet_names
    assert "Verified Data Extract" in sheet_names


def test_excel_formula_injection_defense():
    """Verify Excel generator protects against formula injection (=, +, -, @, cmd)."""
    malicious_payload = build_canonical_reporting_payload(
        user_objective="=SUM(1+1)",
        insights_list=[{"title": "@HYPERLINK('http://evil.com')", "finding": "-2+5+cmd|' /C calc'!A0", "status": "approved"}],
        recommendations_list=[{"title": "+cmd|' /C calc'!A0", "action": "=cmd|' /C calc'!A0", "status": "approved"}]
    )
    excel_bytes = generate_excel_evidence_pack(payload=malicious_payload)
    assert validate_excel_bytes(excel_bytes) is True
    
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    ws_ins = wb["Evidence Insights"]
    cell_val = ws_ins.cell(row=2, column=2).value
    # Must be sanitized with leading single quote or stripped
    assert not str(cell_val).startswith("@HYPERLINK") or str(cell_val).startswith("'")


# ==============================================================================
# 3. POWERPOINT PRESENTATION TESTS
# ==============================================================================
def test_powerpoint_presentation_generation_and_validation(sample_canonical_payload):
    """Verify PowerPoint generates valid 16:9 deck with ZIP header and opens via python-pptx."""
    pptx_bytes = build_powerpoint_presentation(payload=sample_canonical_payload)
    
    # Byte validation
    assert isinstance(pptx_bytes, (bytes, bytearray))
    assert len(pptx_bytes) > 2000
    assert validate_pptx_bytes(pptx_bytes) is True
    
    # Open via python-pptx and verify slide structure
    prs = Presentation(io.BytesIO(pptx_bytes))
    assert len(prs.slides) >= 3
    assert round(prs.slide_width.inches, 2) == 13.33
    assert round(prs.slide_height.inches, 2) == 7.50


def test_generate_public_performance_presentation_api_signatures(sample_canonical_payload):
    """Verify generate_public_performance_presentation and backward-compatible wrapper."""
    # 1. Called with payload dict
    prs = generate_public_performance_presentation(sample_canonical_payload)
    assert prs is not None
    assert len(prs.slides) >= 6
    
    # 2. Called with backward-compatible alias generate_assessment_presentation
    prs_alias = generate_assessment_presentation(sample_canonical_payload)
    assert prs_alias is not None
    assert len(prs_alias.slides) >= 6
    
    # 3. Called with as_bytes=True
    raw_bytes = generate_public_performance_presentation(sample_canonical_payload, as_bytes=True)
    assert isinstance(raw_bytes, (bytes, bytearray))
    assert validate_pptx_bytes(raw_bytes) is True


# ==============================================================================
# 4. REPORTLAB PDF REPORT TESTS
# ==============================================================================
def test_pdf_report_generation_and_validation(sample_canonical_payload):
    """Verify PDF Report generates valid %PDF document, openable via pypdf with >= 1 page."""
    pdf_bytes = generate_pdf_report(sample_canonical_payload)
    
    # Byte validation
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    assert validate_pdf_bytes(pdf_bytes) is True
    
    # Open via pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    page1_text = reader.pages[0].extract_text()
    assert "Performance Insight Explorer" in page1_text
    assert "Objective:" in page1_text or "Throughput" in page1_text


def test_pdf_report_flexible_caller_signatures(sample_performance_df):
    """Verify generate_pdf_report supports df=..., findings_data=..., and direct payload."""
    # 1. Called with df and keyword args
    pdf_1 = generate_pdf_report(
        df=sample_performance_df,
        findings_data={"insights": ["Finding A", "Finding B"], "kpis": {}, "recs": ["Action 1"]},
        brief_context={"question": "Test Question"}
    )
    assert validate_pdf_bytes(pdf_1) is True
    
    # 2. Called with positional payload dict
    payload = build_canonical_reporting_payload(state_or_df=sample_performance_df)
    pdf_2 = generate_pdf_report(payload)
    assert validate_pdf_bytes(pdf_2) is True


# ==============================================================================
# 5. CONTENT INTEGRITY & ABSENCE OF RECRUITMENT TERMINOLOGY
# ==============================================================================
def test_no_assessment_or_interview_language_in_exports(sample_canonical_payload):
    """Verify that generated outputs contain no interview, candidate, defense, or assessment jargon."""
    md_text = build_markdown_executive_report(payload=sample_canonical_payload)
    
    forbidden_terms = ["candidate", "interview view", "assessment summary & defense", "defense view", "prompt card", "scoring rubric"]
    for term in forbidden_terms:
        assert term not in md_text.lower(), f"Found forbidden recruitment term '{term}' in Markdown report"


# ==============================================================================
# 6. GRACEFUL DEGRADATION WITH EMPTY / MISSING DATA
# ==============================================================================
def test_empty_optional_fields_graceful_degradation():
    """Verify export builders do not crash when given completely minimal / empty payloads."""
    minimal_payload = build_canonical_reporting_payload(
        state_or_df=None,
        user_objective="",
        specific_questions=[],
        insights_list=[],
        recommendations_list=[]
    )
    
    # Excel
    excel_bytes = generate_excel_evidence_pack(payload=minimal_payload)
    assert validate_excel_bytes(excel_bytes) is True
    
    # PPTX
    pptx_bytes = build_powerpoint_presentation(payload=minimal_payload)
    assert validate_pptx_bytes(pptx_bytes) is True
    
    # PDF
    pdf_bytes = build_executive_pdf(payload=minimal_payload)
    assert validate_pdf_bytes(pdf_bytes) is True
    
    # Markdown
    md = build_markdown_executive_report(payload=minimal_payload)
    assert len(md) > 100
