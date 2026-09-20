"""Comprehensive test suite for Public Presentation platform, findings normalization,
semantic mapping accuracy, and elimination of assessment/interview terminology.
"""
import pytest
import os
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from core.models import EvidenceInsight, RecommendationItem
from modules.insights.engine import normalize_finding, normalize_recommendation
from modules.mapping.mapper import suggest_semantic_mappings
from modules.reporting.export_builder import (
    build_excel_evidence_pack,
    build_powerpoint_presentation,
    build_executive_pdf,
    build_markdown_executive_report
)


def test_findings_stored_as_dataclass_objects():
    """Verify dataclass EvidenceInsight objects normalize safely."""
    finding_obj = EvidenceInsight(
        id="INS-001",
        finding_title="Elevated Wait Times in ED",
        quantitative_evidence="Wait times exceeded 4 hours in 28% of cases.",
        kpi_affected="Wait Time",
        variance_or_gap_size=18.5,
        time_period="Last 12 Months",
        affected_segment="ED Department",
        confidence_level="A - Statistically Significant",
        business_significance="Critical",
        data_quality_caveat="None",
        statistical_limitation="None",
        suggested_follow_up="Triage review",
        status="approved"
    )
    norm = normalize_finding(finding_obj)
    assert norm is not None
    assert norm["title"] == "Elevated Wait Times in ED"
    assert norm["evidence_level"] == "A - Statistically Significant"
    assert "Wait times exceeded" in norm["description"]
    assert norm["status"] == "approved"


def test_findings_stored_as_dictionaries():
    """Verify finding dictionaries with standard and alternative key names normalize cleanly."""
    # Standard dict
    dict_standard = {
        "title": "Turnover Spike in Engineering",
        "description": "Voluntary turnover reached 14.2%.",
        "evidence_level": "Robust",
        "where": "Engineering",
        "when": "Q3 2026",
        "status": "approved"
    }
    norm1 = normalize_finding(dict_standard)
    assert norm1["title"] == "Turnover Spike in Engineering"
    assert norm1["where"] == "Engineering"

    # Alternative keys dict
    dict_alt = {
        "finding": "Customer churn increased by 4%",
        "problem": "High churn rate in Tier 2 customers",
        "confidence": "High",
        "dimension": "Tier 2",
        "period": "Last 6 Months"
    }
    norm2 = normalize_finding(dict_alt)
    assert norm2["title"] == "Customer churn increased by 4%"
    assert norm2["where"] == "Tier 2"
    assert norm2["when"] == "Last 6 Months"


def test_findings_stored_as_plain_strings():
    """Verify plain string findings are gracefully converted to structured records."""
    str_finding = "Planning applications over 8 weeks grew by 12% in Ward A."
    norm = normalize_finding(str_finding)
    assert norm is not None
    assert "Planning applications" in norm["title"]
    assert norm["description"] == str_finding
    assert norm["evidence_level"] == "Not assessed"


def test_mixed_findings_collection_normalization():
    """Verify mixed collections containing dataclasses, dicts, strings, and empty values normalize without error."""
    mixed = [
        EvidenceInsight(
            id="1",
            finding_title="Dataclass Finding",
            quantitative_evidence="Detail 1",
            kpi_affected="KPI",
            variance_or_gap_size=5.0,
            time_period="2026",
            affected_segment="All",
            confidence_level="High",
            business_significance="Operational",
            data_quality_caveat="",
            statistical_limitation="",
            suggested_follow_up=""
        ),
        {"title": "Dict Finding", "description": "Detail 2", "status": "approved"},
        "String Finding 3",
        None,
        {},
        {"finding_title": "Alternative Title", "text": "Detail 4"}
    ]

    normalized = [normalize_finding(x) for x in mixed]
    valid_items = [n for n in normalized if n is not None]

    assert len(valid_items) == 5
    assert valid_items[0]["title"] == "Dataclass Finding"
    assert valid_items[1]["title"] == "Dict Finding"
    assert "String Finding 3" in valid_items[2]["title"]
    assert valid_items[3]["title"] == "Performance Finding"
    assert valid_items[4]["title"] == "Alternative Title"


def test_missing_approval_status_handling():
    """Verify findings without an explicit status field are preserved rather than hidden."""
    unapproved_dict = {
        "title": "Unreviewed Insight",
        "description": "Baseline performance meets standards."
    }
    norm = normalize_finding(unapproved_dict)
    assert norm is not None
    assert norm["title"] == "Unreviewed Insight"
    assert norm.get("status") in [None, "", "Active"]


def test_recommendations_stored_as_dataclass_and_dict():
    """Verify recommendations normalize correctly across objects, dicts, and strings."""
    rec_obj = RecommendationItem(
        id="REC-001",
        linked_insight_id="INS-001",
        problem_addressed="Implement Queue Load Balancing",
        supporting_evidence="28% breaches",
        proposed_action="Deploy dynamic triage during peak periods.",
        expected_benefit="Reduce wait times by 15%",
        responsible_owner="Triage Lead",
        timescale="30 Days"
    )
    norm_r1 = normalize_recommendation(rec_obj)
    assert "Queue Load Balancing" in norm_r1["title"] or "Queue Load Balancing" in norm_r1["problem"]
    assert norm_r1["owner"] == "Triage Lead"

    dict_rec = {
        "title": "Streamline Document Validation",
        "proposed_action": "Automate digital pre-checks.",
        "owner": "Digital Ops",
        "timescale": "60 Days"
    }
    norm_r2 = normalize_recommendation(dict_rec)
    assert norm_r2["title"] == "Streamline Document Validation"
    assert norm_r2["owner"] == "Digital Ops"

    str_rec = "Review staffing schedule on weekends."
    norm_r3 = normalize_recommendation(str_rec)
    assert "Review staffing schedule" in norm_r3["title"]
    assert norm_r3["proposed_action"] == str_rec


def test_consumer_price_semantic_mapping_rules():
    """Verify exact column mapping suggestions for the consumer price test dataset.
    - Date -> Date / Timestamp
    - Category_Num -> Category Code (never Unique Identifier)
    - Category -> Category / Group Dimension
    - Item_ID -> Unique Identifier
    - Item_Name -> Product / Item Dimension
    - Reported_Price -> Performance Metric / KPI Value
    """
    df_cpi = pd.DataFrame({
        "Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
        "Category_Num": [10, 10, 10, 20, 20, 20],  # Repeating category numbers
        "Category": ["Food & Beverage", "Food & Beverage", "Food & Beverage", "Transport", "Transport", "Transport"],
        "Item_ID": ["ITM-001", "ITM-002", "ITM-003", "ITM-004", "ITM-005", "ITM-006"],
        "Item_Name": ["Whole Milk 1L", "White Bread 800g", "Eggs 12pk", "Unleaded Petrol 1L", "Diesel 1L", "Bus Fare"],
        "Reported_Price": [1.15, 1.35, 2.45, 1.48, 1.55, 2.20]
    })

    mappings = suggest_semantic_mappings(df_cpi)

    assert mappings["Date"]["suggested_role"] == "date"
    assert mappings["Date"]["label"] == "Date / Timestamp"

    assert mappings["Category_Num"]["suggested_role"] in ["category_code", "category"]
    assert mappings["Category_Num"]["suggested_role"] != "record_id"  # Must NEVER be Unique Identifier

    assert mappings["Category"]["suggested_role"] == "category"
    assert mappings["Category"]["label"] == "Category / Group Dimension"

    assert mappings["Item_ID"]["suggested_role"] == "record_id"
    assert mappings["Item_ID"]["label"] == "Unique Identifier"

    assert mappings["Item_Name"]["suggested_role"] == "product_service"
    assert mappings["Item_Name"]["label"] == "Product / Item Dimension"

    assert mappings["Reported_Price"]["suggested_role"] == "kpi_metric"
    assert mappings["Reported_Price"]["label"] == "Performance Metric / KPI Value"


def test_common_metric_name_recognition():
    """Verify common performance metric terms are recognized as KPI values."""
    metric_cols = [
        "price", "cost", "revenue", "sales", "amount", "value", "score",
        "rate", "count", "volume", "duration", "waiting_time", "response_time",
        "productivity", "performance", "reported_price"
    ]
    for col in metric_cols:
        df = pd.DataFrame({col: [10.5, 20.0, 35.2, 40.1, 55.0]})
        m = suggest_semantic_mappings(df)
        assert m[col]["suggested_role"] in ["kpi_metric", "actual", "duration_wait_time", "numerator", "volume_inflow"], f"Failed for {col}"
        assert m[col]["category"] == "Metric"


def test_public_presentation_export_generation():
    """Verify multi-format exports generate valid non-empty byte streams for public presentation."""
    df = pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=10),
        "Region": ["North", "South"] * 5,
        "Reported_Price": [100.0, 110.0, 105.0, 115.0, 120.0, 118.0, 125.0, 130.0, 128.0, 135.0]
    })
    findings = [
        {"title": "Price Trend Increase", "description": "Average price grew by 35% over 10 periods.", "evidence_level": "A", "status": "approved"}
    ]
    recs = [
        {"title": "Monitor Price Index", "proposed_action": "Track monthly inflation variance.", "owner": "Finance Lead", "timescale": "Ongoing"}
    ]

    # 1. Excel Evidence Pack
    excel_bytes = build_excel_evidence_pack(
        clean_df=df,
        kpi_definitions=[],
        quality_issues=[],
        evidence_insights=findings,
        recommendation_items=recs,
        action_items=[],
        audit_log_entries=[{"timestamp": "2026-09-20 12:00:00", "event_type": "REPORT_GENERATED", "message": "Exported"}],
        project_state={"project_name": "Public Performance Presentation"}
    )
    assert isinstance(excel_bytes, bytes) and len(excel_bytes) > 1000

    # 2. PowerPoint Presentation
    pptx_bytes = build_powerpoint_presentation(
        project_state={"project_name": "Public Briefing Deck"},
        kpi_summary={"Reported_Price": 120.6},
        trend_summary=pd.DataFrame(),
        comparison_summary={},
        evidence_insights=findings,
        recommendations=recs
    )
    assert isinstance(pptx_bytes, bytes) and len(pptx_bytes) > 1000

    # 3. PDF Brief
    pdf_bytes = build_executive_pdf(
        project_state={"project_name": "Public Executive Brief"},
        kpi_summary={"Reported_Price": 120.6},
        quality_score=98.0,
        insights=findings,
        recommendations=recs
    )
    assert isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 500

    # 4. Markdown Brief
    md_str = build_markdown_executive_report(
        project_state={"project_name": "Public Briefing"},
        kpi_results={"Reported_Price": {"name": "Reported Price", "actual": 120.6, "target": 100.0, "variance_pct": 20.6, "status": "Evaluated"}},
        insights=findings,
        recommendations=recs,
        actions=[]
    )
    assert isinstance(md_str, str) and len(md_str) > 200
    # Confirm no interview language
    assert "interview" not in md_str.lower()
    assert "candidate" not in md_str.lower()
