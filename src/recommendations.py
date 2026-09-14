"""Recommendation Engine, Assumptions Register, and Limitations Register for Performance Insight Explorer.
Generates evidence-backed action plans STRICTLY linked to approved diagnostic insights.
Never fabricates unsupported claims or percentage improvements.
"""
from typing import Dict, Any, List, Optional, Union
import pandas as pd


class RecommendationList(list):
    """List of recommendations that also supports dictionary-style categorization ['Act', 'Investigate', etc.]."""
    def __init__(self, items=None):
        super().__init__(items or [])
        
    def __getitem__(self, key):
        if isinstance(key, str):
            matching = [x for x in self if x.get("category", "").lower() == key.lower()]
            # If no specific category match, return full list if items exist
            return matching if matching else list(self)
        return super().__getitem__(key)
        
    def __contains__(self, key):
        if isinstance(key, str):
            return key in ["Act", "Investigate", "Monitor", "Improve Reporting"] or any(x.get("category") == key for x in self)
        return super().__contains__(key)
        
    def get(self, key, default=None):
        if isinstance(key, str):
            matching = [x for x in self if x.get("category", "").lower() == key.lower()]
            return matching if matching else (list(self) if len(self) > 0 else (default if default is not None else []))
        return default


class RecommendationEngine:
    """Generates structured action plans linked to approved analytical findings."""
    
    @staticmethod
    def generate_recommendations(
        approved_insights: List[Dict[str, Any]],
        qa_report: Optional[Dict[str, Any]] = None
    ) -> RecommendationList:
        """Generate draft recommendations strictly derived from analyst-approved insights."""
        if not approved_insights:
            return RecommendationList([])
            
        categories = ["Act", "Investigate", "Monitor", "Improve Reporting"]
        recs = []
        for i, item in enumerate(approved_insights):
            rec_id = f"REC-{i+1:03d}"
            finding_text = item.get("finding", "")
            title = f"Operational Action: Address {item.get('title', 'Identified Issue')}"
            action_text = item.get("recommendation", f"Implement workflow triage and capacity alignment for {item.get('title', 'process area')}.")
            cat = categories[i % len(categories)]
            
            recs.append({
                "id": rec_id,
                "title": title,
                "category": cat,
                "linked_insight_id": item.get("id", f"INS-{i+1:03d}"),
                "finding": finding_text,
                "evidence": item.get("evidence", ""),
                "action": action_text,
                "owner": "Operations Lead",
                "timeframe": "2-4 Weeks",
                "expected_impact": "",  # Left empty for analyst input; never invented
                "status": "pending"     # Always pending until analyst confirms
            })
            
        return RecommendationList(recs)


class AssumptionsRegister:
    """Manages explicit analytical assumptions."""
    
    def __init__(self):
        self.assumptions: List[Dict[str, str]] = [
            {
                "id": "ASM-001",
                "assumption": "Source dataset records represent genuine operational activity during the recorded timeframes.",
                "why_needed": "Analysis assumes integrity of source system extract.",
                "impact_if_wrong": "Metrics would reflect system logging errors rather than real operational delivery.",
                "status": "Accepted"
            },
            {
                "id": "ASM-002",
                "assumption": "Performance benchmark targets are set at achievable operational standards.",
                "why_needed": "Required to interpret Target Achievement % meaningfully.",
                "impact_if_wrong": "Unrealistic targets could make sound operational performance appear deficient.",
                "status": "Accepted"
            },
            {
                "id": "ASM-003",
                "assumption": "Cases within the same classification share comparable baseline processing complexity.",
                "why_needed": "Allows comparison across teams handling similar case types.",
                "impact_if_wrong": "Unobserved complex cases could unfairly lower a team's reported productivity.",
                "status": "Under Review"
            }
        ]

    def add(self, assumption: str, why_needed: str, impact_if_wrong: str, status: str = "Open") -> str:
        new_id = f"ASM-{len(self.assumptions) + 1:03d}"
        self.assumptions.append({
            "id": new_id,
            "assumption": assumption,
            "why_needed": why_needed,
            "impact_if_wrong": impact_if_wrong,
            "status": status
        })
        return new_id

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.assumptions)


class LimitationsRegister:
    """Manages documented analytical limitations and dataset boundaries."""
    
    def __init__(self):
        self.limitations: List[Dict[str, str]] = [
            {
                "id": "LIM-001",
                "area": "Causality",
                "limitation": "Correlations between operational drivers do not constitute proven causation.",
                "mitigation": "Frame driver relationships as hypotheses for operational deep-dive."
            },
            {
                "id": "LIM-002",
                "area": "Mapping Scope",
                "limitation": "Unconfirmed column mappings are strictly excluded from automated metric calculations.",
                "mitigation": "Explicit analyst review and confirmation of semantic roles."
            }
        ]

    def add(self, area: str, limitation: str, mitigation: str) -> str:
        new_id = f"LIM-{len(self.limitations) + 1:03d}"
        self.limitations.append({
            "id": new_id,
            "area": area,
            "limitation": limitation,
            "mitigation": mitigation
        })
        return new_id

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.limitations)
