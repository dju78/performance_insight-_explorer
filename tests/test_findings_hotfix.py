"""Regression tests for findings and recommendations rendering hotfix.
Verifies that normalize_finding and normalize_recommendation safely handle:
- Finding dataclasses (EvidenceInsight)
- Dictionaries with various schemas
- Plain strings
- Missing title / evidence_level
- Empty / None values
- Mixed collections
"""
import pytest
from core.models import EvidenceInsight, RecommendationItem, PriorityLevel
from modules.insights.engine import normalize_finding, normalize_recommendation


def test_normalize_finding_dataclass():
    insight = EvidenceInsight(
        id="INS-001",
        finding_title="Critical Shortfall in Output Against Target",
        quantitative_evidence="Observed output trails target by 15.2%.",
        kpi_affected="Output Volume",
        variance_or_gap_size=-15.2,
        time_period="Last 30 Days",
        affected_segment="Region North",
        confidence_level="High (Verified Calculation)",
        business_significance="Critical Operational Risk",
        data_quality_caveat="Target calibrated.",
        statistical_limitation="No subgroup isolation.",
        suggested_follow_up="Investigate Region North."
    )
    norm = normalize_finding(insight)
    assert norm is not None
    assert norm["title"] == "Critical Shortfall in Output Against Target"
    assert norm["evidence_level"] == "High (Verified Calculation)"
    assert norm["description"] == "Observed output trails target by 15.2%."
    assert norm["metric"] == "Output Volume"
    assert norm["where"] == "Region North"
    assert norm["when"] == "Last 30 Days"
    assert norm["impact"] == "Critical Operational Risk"
    assert norm["limitation"] == "No subgroup isolation."


def test_normalize_finding_dict_variations():
    # Dict with 'title' and 'evidence_level'
    d1 = {
        "title": "High Cycle Time",
        "evidence_level": "Medium",
        "description": "Cycle time is 45 min vs 30 min target.",
        "where": "Line B",
        "when": "Q3",
        "impact": "Production delay",
        "limitation": "Sample size small"
    }
    norm1 = normalize_finding(d1)
    assert norm1["title"] == "High Cycle Time"
    assert norm1["evidence_level"] == "Medium"
    assert norm1["description"] == "Cycle time is 45 min vs 30 min target."

    # Dict with 'finding_title' and 'confidence_level'
    d2 = {
        "finding_title": "Inventory Variance",
        "confidence_level": "High",
        "quantitative_evidence": "Inventory discrepant by 5%.",
        "kpi_affected": "Stock Accuracy",
        "affected_segment": "Warehouse 1",
        "time_period": "August",
        "business_significance": "Financial exposure",
        "statistical_limitation": "Based on cycle counts"
    }
    norm2 = normalize_finding(d2)
    assert norm2["title"] == "Inventory Variance"
    assert norm2["evidence_level"] == "High"
    assert norm2["description"] == "Inventory discrepant by 5%."


def test_normalize_finding_plain_string():
    raw_str = "Customer satisfaction dropped by 12% in the southern district."
    norm = normalize_finding(raw_str)
    assert norm is not None
    assert norm["description"] == raw_str
    assert "Customer satisfaction" in norm["title"]
    assert norm["evidence_level"] == "Not assessed"
    assert norm["where"] == "Enterprise-Wide"


def test_normalize_finding_missing_fields_and_defaults():
    # Empty dict
    norm_empty = normalize_finding({})
    assert norm_empty is not None
    assert norm_empty["title"] == "Performance Finding"
    assert norm_empty["evidence_level"] == "Not assessed"

    # Dict with missing title
    d_no_title = {"quantitative_evidence": "Some evidence without title."}
    norm_no_title = normalize_finding(d_no_title)
    assert norm_no_title["title"] == "Performance Finding"
    assert norm_no_title["description"] == "Some evidence without title."

    # Dict with missing evidence_level
    d_no_level = {"title": "Valid Title", "observation": "Observed drift."}
    norm_no_level = normalize_finding(d_no_level)
    assert norm_no_level["title"] == "Valid Title"
    assert norm_no_level["evidence_level"] == "Not assessed"
    assert norm_no_level["description"] == "Observed drift."


def test_normalize_finding_none_and_empty():
    assert normalize_finding(None) is None
    assert normalize_finding("") is None
    assert normalize_finding("   ") is None


def test_normalize_finding_mixed_collection():
    collection = [
        None,
        "",
        "Simple string finding note",
        {"title": "Dict finding", "confidence_level": "Medium"},
        EvidenceInsight(
            id="INS-002",
            finding_title="Dataclass finding",
            quantitative_evidence="Quantitative proof",
            kpi_affected="Revenue",
            variance_or_gap_size=10.0,
            time_period="2026",
            affected_segment="All",
            confidence_level="High",
            business_significance="Strategic",
            data_quality_caveat="None",
            statistical_limitation="None",
            suggested_follow_up="None"
        ),
        {},
    ]
    results = [normalize_finding(item) for item in collection]
    valid_results = [r for r in results if r is not None]
    assert len(valid_results) == 4
    assert valid_results[0]["description"] == "Simple string finding note"
    assert valid_results[1]["title"] == "Dict finding"
    assert valid_results[2]["title"] == "Dataclass finding"
    assert valid_results[3]["title"] == "Performance Finding"


def test_normalize_recommendation():
    # Dataclass
    rec_item = RecommendationItem(
        id="REC-001",
        linked_insight_id="INS-001",
        problem_addressed="Underperforming triage desk",
        supporting_evidence="Wait times exceed 4 hours",
        proposed_action="Reallocate 2 staff to triage",
        expected_benefit="Reduce wait time by 30%",
        priority=PriorityLevel.HIGH,
        impact="High",
        effort="Low",
        responsible_owner="Nurse Manager",
        timescale="14 days"
    )
    norm_rec = normalize_recommendation(rec_item)
    assert norm_rec is not None
    assert norm_rec["id"] == "REC-001"
    assert norm_rec["problem"] == "Underperforming triage desk"
    assert norm_rec["proposed_action"] == "Reallocate 2 staff to triage"
    assert norm_rec["owner"] == "Nurse Manager"

    # Dict
    d_rec = {
        "title": "Upgrade server memory",
        "problem": "High memory consumption during peak",
        "action": "Add 64GB RAM to cluster nodes",
        "impact": "High",
        "effort": "Low",
        "owner": "Infrastructure Lead",
        "timescale": "7 days"
    }
    norm_d_rec = normalize_recommendation(d_rec)
    assert norm_d_rec["title"] == "Upgrade server memory"
    assert norm_d_rec["owner"] == "Infrastructure Lead"

    # String
    norm_s_rec = normalize_recommendation("Automate weekly data reconciliation batch script.")
    assert norm_s_rec is not None
    assert "Automate weekly data reconciliation" in norm_s_rec["title"]

    # None and empty
    assert normalize_recommendation(None) is None
    assert normalize_recommendation("") is None
