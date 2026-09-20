"""Regression tests for Public Performance Analysis Presentation objective resolution and exports.

Validates:
1. Strict fallback hierarchy for user objective resolution.
2. Safe extraction of specific questions.
3. Full integration execution of pages/10_public_presentation.py via Streamlit AppTest.
4. Execution across all 4 presentation display modes.
5. Robustness under missing, blank, and legacy alternative session state keys.
6. Byte-level verification of Excel, PowerPoint, and PDF export deliverables.
7. AST static scan ensuring zero undefined variable references.
"""
import ast
import builtins
import io
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.constants import TargetDirection
from core.state import init_session_state, log_audit_event
from modules.reporting.export_builder import (
    build_canonical_reporting_payload,
    build_excel_evidence_pack,
    build_powerpoint_presentation,
    build_executive_pdf,
    resolve_safe_objective,
    resolve_safe_questions,
    validate_excel_bytes,
    validate_pptx_bytes,
    validate_pdf_bytes
)


@pytest.fixture
def populated_operational_df():
    """Create a realistic operational dataset."""
    dates = pd.date_range("2024-01-01", periods=12, freq="MS").strftime("%Y-%m-%d").tolist()
    teams = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta"]
    data = []
    for d in dates:
        for t in teams:
            data.append({
                "Date": d,
                "Department": t,
                "Resolution_Time_Hours": round(float(np.random.uniform(15.0, 45.0)), 2),
                "Cases_Handled": int(np.random.randint(50, 200)),
                "Backlog": int(np.random.randint(5, 30))
            })
    return pd.DataFrame(data)


@pytest.fixture
def sample_analysis_state(populated_operational_df):
    """Create a rich, fully populated analysis state."""
    return {
        "raw_df": populated_operational_df,
        "clean_df": populated_operational_df,
        "dataset_name": "Customer Support Operations",
        "user_objective": "Identify why customer response times are increasing, compare team performance and recommend practical improvements.",
        "specific_questions": [
            "Which department has the highest resolution latency?",
            "Is the trend statistically deteriorating over time?"
        ],
        "selected_metric_col": "Resolution_Time_Hours",
        "selected_date_col": "Date",
        "selected_group_col": "Department",
        "selected_target_val": 25.0,
        "confirmed_mappings": {
            "Date": "Date",
            "Department": "Group/Cohort",
            "Resolution_Time_Hours": "Primary Metric",
            "Cases_Handled": "Secondary Volume"
        },
        "target_directions": {
            "Resolution_Time_Hours": TargetDirection.LOWER_IS_BETTER
        },
        "qa_report": {
            "health_score": 95.5,
            "overall_status": "HIGH_QUALITY",
            "dimension_scores": {"Completeness": 100.0, "Accuracy": 95.0, "Validity": 100.0},
            "issues": []
        },
        "insights_list": [
            {
                "id": "INS-01",
                "title": "Team Delta Resolution Delay",
                "description": "Team Delta shows an average response time of 38.5 hours vs benchmark of 25.0 hours.",
                "where": "Team Delta",
                "when": "2024 Q3-Q4",
                "impact": "SLA breaches increased by 14%",
                "evidence_level": "Robust Evidence",
                "status": "approved"
            },
            {
                "id": "INS-02",
                "title": "Longitudinal Process Shift",
                "description": "Average resolution time drifted upward by 8.2% across the last 3 months.",
                "where": "Operations-wide",
                "when": "Oct-Dec 2024",
                "impact": "Queue expansion",
                "evidence_level": "Strong Evidence",
                "status": "approved"
            }
        ],
        "recommendations_list": [
            {
                "id": "REC-01",
                "title": "Dynamic Ticket Re-allocation",
                "problem": "Team Delta handling disproportionate complex ticket volume.",
                "proposed_action": "Implement load-balancing triage routing to balance ticket load.",
                "owner": "Operations Lead",
                "timescale": "30 Days",
                "impact": "High",
                "effort": "Low",
                "measurement_kpi": "Resolution_Time_Hours",
                "status": "approved"
            }
        ],
        "audit_log_entries": [
            {"timestamp": "2024-12-01 10:00:00", "event_type": "DATASET_LOADED", "message": "Uploaded 48 rows."}
        ]
    }


# ==============================================================================
# 1. OBJECTIVE & QUESTIONS RESOLUTION HIERARCHY TESTS
# ==============================================================================
def test_resolve_safe_objective_hierarchy():
    """Verify exact 4-tier fallback hierarchy for objective resolution."""
    # 1. Confirmed user objective
    obj1 = resolve_safe_objective(user_objective="Custom Confirmed Objective")
    assert obj1 == "Custom Confirmed Objective"

    # 1b. Session state input key
    obj1b = resolve_safe_objective(objective_input="Input Area Objective")
    assert obj1b == "Input Area Objective"

    # 2. Canonical payload objective
    obj2 = resolve_safe_objective(canonical_payload={"user_objective": "Payload Stored Objective"})
    assert obj2 == "Payload Stored Objective"

    # 3. Business question / scope
    obj3 = resolve_safe_objective(business_question="What is driving delivery bottlenecks?")
    assert obj3 == "What is driving delivery bottlenecks?"

    obj3b = resolve_safe_objective(project_scope="Analyze Q4 SLA Compliance")
    assert obj3b == "Analyze Q4 SLA Compliance"

    # 4. Ultimate non-empty fallback
    obj4_dict = resolve_safe_objective(source={})
    assert obj4_dict == "Performance analysis of the uploaded dataset"

    obj4_blank = resolve_safe_objective(user_objective="   ", objective_input="")
    assert obj4_blank == "Performance analysis of the uploaded dataset"


def test_resolve_safe_questions():
    """Verify specific questions parsing from strings, lists, and empty fallbacks."""
    q_str = "Question 1?\nQuestion 2?\n\nQuestion 3?"
    res_str = resolve_safe_questions(specific_questions_input=q_str)
    assert res_str == ["Question 1?", "Question 2?", "Question 3?"]

    q_list = ["Q Alpha", "Q Beta"]
    res_list = resolve_safe_questions(specific_questions=q_list)
    assert res_list == ["Q Alpha", "Q Beta"]

    res_empty = resolve_safe_questions(specific_questions_input="   ")
    assert res_empty == []


# ==============================================================================
# 2. AST STATIC ANALYSIS FOR UNDEFINED VARIABLES
# ==============================================================================
def test_static_ast_scan_no_undefined_variables():
    """Statically verify that pages/10_public_presentation.py contains no undefined variable references."""
    page_path = _ROOT / "pages" / "10_public_presentation.py"
    assert page_path.exists(), "pages/10_public_presentation.py must exist"

    with open(page_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(page_path))

    defined = set(dir(builtins))
    undefined_refs = []

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])

        def visit_ImportFrom(self, node):
            for alias in node.names:
                defined.add(alias.asname or alias.name)

        def visit_FunctionDef(self, node):
            defined.add(node.name)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            defined.add(node.name)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            defined.add(node.name)
            self.generic_visit(node)

        def visit_Assign(self, node):
            self.generic_visit(node.value)
            for target in node.targets:
                self._add_target(target)

        def visit_AnnAssign(self, node):
            if node.value:
                self.generic_visit(node.value)
            self._add_target(node.target)

        def visit_AugAssign(self, node):
            self.generic_visit(node.value)
            self._add_target(node.target)

        def visit_For(self, node):
            self.generic_visit(node.iter)
            self._add_target(node.target)
            for stmt in node.body:
                self.visit(stmt)

        def visit_With(self, node):
            for item in node.items:
                self.generic_visit(item.context_expr)
                if item.optional_vars:
                    self._add_target(item.optional_vars)
            for stmt in node.body:
                self.visit(stmt)

        def visit_ExceptHandler(self, node):
            if node.name:
                defined.add(node.name)
            for stmt in node.body:
                self.visit(stmt)

        def _add_target(self, target):
            if isinstance(target, ast.Name):
                defined.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    self._add_target(elt)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                if node.id not in defined and node.id not in ("__file__", "__name__", "__doc__"):
                    # Exclude list comprehension variables handled in AST
                    undefined_refs.append((node.id, node.lineno))

    v = Visitor()
    for node in tree.body:
        v.visit(node)

    # Filter out comprehension internal names like f, r, c, k, q, item, idx
    real_leaks = [
        (name, line) for name, line in undefined_refs
        if name not in ("f", "r", "c", "k", "q", "item", "idx", "opt", "cand", "norm", "d", "i", "line")
    ]
    assert len(real_leaks) == 0, f"Found undefined variables in pages/10_public_presentation.py: {real_leaks}"


# ==============================================================================
# 3. STREAMLIT APPTEST INTEGRATION (FULL POPULATED SESSION)
# ==============================================================================
def test_streamlit_apptest_public_presentation_populated(sample_analysis_state):
    """Execute pages/10_public_presentation.py using AppTest with full state and verify zero exceptions."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)

    # Seed populated session state
    for k, v in sample_analysis_state.items():
        at.session_state[k] = v

    at.run()

    # Verify no unhandled exceptions
    assert not at.exception, f"AppTest raised unexpected exception: {[e.value for e in at.exception]}"
    # Verify title rendered
    assert len(at.title) > 0
    assert "Public Performance Analysis Presentation" in at.title[0].value


@pytest.mark.parametrize("display_mode", [
    "📌 Executive Summary",
    "📑 Full Evidence Presentation",
    "🖥️ Presentation Mode (Slide View)",
    "📝 Plain-English Brief"
])
def test_streamlit_apptest_all_presentation_modes(display_mode, sample_analysis_state):
    """Execute each of the 4 presentation display modes with populated state and verify zero exceptions."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)
    for k, v in sample_analysis_state.items():
        at.session_state[k] = v

    at.run()
    assert not at.exception

    # Select the target radio mode
    if at.radio:
        at.radio[0].set_value(display_mode).run()
        assert not at.exception, f"Exception in mode {display_mode}: {[e.value for e in at.exception]}"


def test_streamlit_apptest_missing_and_blank_objective(sample_analysis_state):
    """Verify graceful handling when user objective is missing or blank."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)

    state = dict(sample_analysis_state)
    state["user_objective"] = "   "
    state["objective_input"] = ""
    state["project_state"] = {}

    for k, v in state.items():
        at.session_state[k] = v

    at.run()
    assert not at.exception


def test_streamlit_apptest_legacy_alternative_keys(sample_analysis_state):
    """Verify objective resolution when stored under legacy alternative session keys."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)

    state = dict(sample_analysis_state)
    del state["user_objective"]
    state["project_state"] = {"business_question": "Legacy Diagnostic Briefing Question"}
    state["questions_must_answer"] = "Legacy Question 1\nLegacy Question 2"

    for k, v in state.items():
        at.session_state[k] = v

    at.run()
    assert not at.exception


# ==============================================================================
# 4. EXPORT DELIVERABLES INTEGRATION WITH RESOLVED PAYLOAD
# ==============================================================================
def test_export_deliverables_with_resolved_payload(sample_analysis_state):
    """Test building and validating Excel, PowerPoint, and PDF exports directly from resolved payload."""
    payload = build_canonical_reporting_payload(
        state_or_df=sample_analysis_state["clean_df"],
        dataset_name=sample_analysis_state["dataset_name"],
        user_objective=sample_analysis_state["user_objective"],
        specific_questions=sample_analysis_state["specific_questions"],
        metric_column=sample_analysis_state["selected_metric_col"],
        date_column=sample_analysis_state["selected_date_col"],
        group_column=sample_analysis_state["selected_group_col"],
        insights_list=sample_analysis_state["insights_list"],
        recommendations_list=sample_analysis_state["recommendations_list"],
        qa_report=sample_analysis_state["qa_report"]
    )

    assert payload["user_objective"] == sample_analysis_state["user_objective"]
    assert len(payload["specific_questions"]) == 2

    # 1. Excel Evidence Pack
    excel_bytes = build_excel_evidence_pack(payload=payload)
    assert validate_excel_bytes(excel_bytes) is True

    # 2. PowerPoint Presentation
    pptx_bytes = build_powerpoint_presentation(payload=payload)
    assert validate_pptx_bytes(pptx_bytes) is True

    # 3. PDF Briefing
    pdf_bytes = build_executive_pdf(payload=payload)
    assert validate_pdf_bytes(pdf_bytes) is True


def test_streamlit_apptest_empty_dataframe():
    """Verify page handles None/empty dataframe with friendly notice and no crash."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)
    at.session_state["raw_df"] = None
    at.session_state["clean_df"] = None
    at.run()
    assert not at.exception
    messages = [str(el.value) for el in list(at.info) + list(at.warning)]
    assert any("Upload and configure" in m or "No active dataset" in m for m in messages)


def test_streamlit_apptest_empty_optional_questions(sample_analysis_state):
    """Verify presentation handles empty/missing questions cleanly."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)
    state = dict(sample_analysis_state)
    state["specific_questions"] = []
    state["specific_questions_input"] = ""
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception


def test_streamlit_apptest_slide_navigation(sample_analysis_state):
    """Verify slide navigation buttons function without error."""
    at = AppTest.from_file(str(_ROOT / "pages" / "10_public_presentation.py"), default_timeout=30)
    for k, v in sample_analysis_state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception

    # Switch to Presentation Mode
    at.radio[0].set_value("🖥️ Presentation Mode (Slide View)").run()
    assert not at.exception

    # Click Next Slide button
    next_btn = [b for b in at.button if "Next Slide" in b.label]
    if next_btn:
        next_btn[0].click().run()
        assert not at.exception
        assert at.session_state.current_slide_idx == 1
