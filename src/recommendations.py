"""Recommendation Engine, Assumptions Register, and Limitations Register for Performance Insight Explorer.
Categorizes actions into: Act, Investigate, Monitor, Improve Reporting.
"""
from typing import Dict, Any, List, Optional
import pandas as pd


class RecommendationEngine:
    """Generates structured action plans across 4 operational categories."""
    
    @staticmethod
    def generate_recommendations(
        insights: List[Dict[str, Any]],
        qa_report: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Organize recommendations into Act, Investigate, Monitor, Improve Reporting."""
        recs = {
            "Act": [],
            "Investigate": [],
            "Monitor": [],
            "Improve Reporting": []
        }
        
        # 1. Act (immediate interventions backed by evidence)
        recs["Act"].append({
            "title": "Workload & Intake Dynamic Rebalancing",
            "action": "Rebalance incoming case allocation across teams based on active capacity and throughput velocity.",
            "rationale": "Mitigate queue bottlenecks in high-volume teams and utilize available capacity in lower-workload units.",
            "owner": "Operations Manager"
        })
        
        # 2. Investigate (targeted inquiries where causation is unproven)
        recs["Investigate"].append({
            "title": "Inter-Group Variance & Workflow Deep-Dive",
            "action": "Review case complexity mix, staff experience, and process bottlenecks in lower-quartile teams.",
            "rationale": "Establish whether group differences stem from complex case types, systems downtime, or skill gaps before taking corrective actions.",
            "owner": "Lead Performance Analyst"
        })
        
        # 3. Monitor (established KPIs tracking against thresholds)
        recs["Monitor"].append({
            "title": "Weekly Backlog & SLA Turnaround Tracking",
            "action": "Establish weekly monitoring of net flow pressure and 90th percentile case processing times.",
            "rationale": "Ensure early warning of queue growth before statutory or benchmark SLA deadlines are breached.",
            "owner": "Operations / Delivery Lead"
        })
        
        # 4. Improve Reporting (data collection, consistency, and QA)
        recs["Improve Reporting"].append({
            "title": "Intake-to-Closure Inventory Reconciliation Controls",
            "action": "Implement automated reconciliation checks between case management and reporting databases to eliminate inventory gaps.",
            "rationale": f"Data audit revealed quality issues (Health Score: {qa_report.get('health_score', 100):.1f}/100) requiring upstream validation.",
            "owner": "Data Governance / BI Team"
        })
        
        return recs


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
    """Manages explicit analytical caveats and constraints."""
    
    def __init__(self):
        self.limitations: List[Dict[str, str]] = [
            {
                "id": "LIM-001",
                "limitation": "Absence of granular case-level lifecycle event stamps in aggregated summaries.",
                "impact": "Prevents exact staging bottleneck duration attribution.",
                "mitigation": "Requested case-level event logs for subsequent sprint analysis."
            },
            {
                "id": "LIM-002",
                "limitation": "Unobserved qualitative factors (e.g. staff leave, system outages, regulatory complexity shifts).",
                "impact": "Observed correlations cannot be interpreted as direct causal drivers.",
                "mitigation": "Frame recommendations as exploratory investigation prompts with operational SMEs."
            }
        ]

    def add(self, limitation: str, impact: str, mitigation: str) -> str:
        new_id = f"LIM-{len(self.limitations) + 1:03d}"
        self.limitations.append({
            "id": new_id,
            "limitation": limitation,
            "impact": impact,
            "mitigation": mitigation
        })
        return new_id

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.limitations)
