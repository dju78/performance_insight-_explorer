import streamlit as st
import pandas as pd
from src.state import init_session_state, get_state, reset_analysis_only, reset_full_state
from src.export import load_app_config

st.set_page_config(
    page_title="Performance Insight Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()
config = load_app_config()

# Sidebar: Assessment Pack Context & Global Controls
with st.sidebar:
    st.title("🎯 Assessment Hub")
    st.caption("Author: DARAMOLA OMOYELE | Performance Insight Explorer")
    
    st.markdown("---")
    st.subheader("📋 Assessment Pack Quick-Edit")
    with st.expander("Quick Context Fields", expanded=False):
        st.session_state["assessment_question"] = st.text_area(
            "Problem Statement / Core Question",
            value=st.session_state.get("assessment_question", ""),
            height=80,
            placeholder="e.g. Investigate backlogs and recommend 3 operational interventions..."
        )
        st.session_state["target_audience"] = st.text_input(
            "Target Audience",
            value=st.session_state.get("target_audience", "Senior Leadership"),
            placeholder="e.g. Operations Director, Assessment Panel"
        )
        st.session_state["response_time"] = st.text_input(
            "Time Available",
            value=st.session_state.get("response_time", "15 minutes (10 presentation + 5 Q&A)"),
            placeholder="e.g. 15 mins"
        )
        st.session_state["output_format"] = st.selectbox(
            "Output Format",
            ["Presentation Deck (PPTX)", "Executive Summary (Word/PDF)", "Live Briefing / Dashboard", "Analytical Memo"],
            index=0 if st.session_state.get("output_format") is None else (
                ["Presentation Deck (PPTX)", "Executive Summary (Word/PDF)", "Live Briefing / Dashboard", "Analytical Memo"].index(st.session_state.get("output_format", "Presentation Deck (PPTX)"))
                if st.session_state.get("output_format") in ["Presentation Deck (PPTX)", "Executive Summary (Word/PDF)", "Live Briefing / Dashboard", "Analytical Memo"]
                else 0
            )
        )
        st.session_state["rapid_mode"] = st.checkbox(
            "⚡ Rapid Assessment Mode",
            value=st.session_state.get("rapid_mode", False),
            help="Highlights mandatory steps and streamlines workflow for tight time limits."
        )

    st.markdown("---")
    st.subheader("🔄 Safety & Reset Controls")
    if st.button("🧹 Reset Analysis Only", help="Clears mappings, metrics, and insights while keeping raw uploaded file intact.", use_container_width=True):
        reset_analysis_only()
        st.success("Analysis, mappings, and metrics reset safely. Raw dataset preserved.")
        st.rerun()
        
    if st.button("⚠️ Full State Reset", help="Clears everything including uploaded files and assessment brief.", use_container_width=True):
        reset_full_state()
        st.warning("Full session reset complete.")
        st.rerun()

# Main Landing Page
st.title("📊 Performance Insight Explorer")
st.markdown("### Operational Performance & Diagnostic Toolkit for Practical Assessments")
st.caption("Candidate / Analyst: **DARAMOLA OMOYELE** | BSR Performance Analyst Assessment Ready")

# Active Dataset Status Banner
if st.session_state.get("raw_df") is not None:
    st.info(f"📁 **Active Dataset:** {st.session_state.get('dataset_name', 'Uploaded File')} | **Rows:** {len(st.session_state['raw_df']):,} | **Columns:** {len(st.session_state['raw_df'].columns)}")
    
    granularity_status = st.session_state.get("row_granularity", "Not Confirmed")
    if granularity_status == "Not Confirmed" or not st.session_state.get("row_granularity_confirmed", False):
        st.warning(
            "⚠️ **ROW GRANULARITY REQUIRED:** Confirm what one row represents before interpreting rates, totals, or lifecycle metrics. "
            "Go to **01_Upload & Profile** to confirm row granularity."
        )
    else:
        st.success(f"✅ **Row Granularity Confirmed:** 1 Row = `{st.session_state['row_granularity']}`")

st.markdown("---")

# 1. ASSESSMENT PACK / PRACTICAL TASK INTAKE SECTION
st.header("📋 Stage 0: Assessment Pack Intake")
st.markdown("""
Enter the specific questions, targets, and constraints from your assessment brief below. 
The application will automatically adapt its analysis, talking points, and executive presentation to address your exact brief.
""")

with st.container():
    c_q1, c_q2 = st.columns(2)
    with c_q1:
        st.session_state["assessment_question"] = st.text_area(
            "1. Core Problem Statement / Main Question",
            value=st.session_state.get("assessment_question", ""),
            height=90,
            placeholder="e.g. Identify why processing lead times have increased and recommend resource reallocations."
        )
        st.session_state["questions_must_answer"] = st.text_area(
            "2. Specific Questions That Must Be Answered (one per line)",
            value=st.session_state.get("questions_must_answer", ""),
            height=90,
            placeholder="e.g.\n- Which teams are underperforming against SLA?\n- Is backlog growth driven by demand surge or reduced capacity?\n- What are the 3 priority actions for next month?"
        )
        st.session_state["mandatory_measures"] = st.text_input(
            "3. Mandatory Measures / Targets Specified",
            value=st.session_state.get("mandatory_measures", ""),
            placeholder="e.g. SLA: 85% in 20 days; Backlog target: <500; Staff utilisation: 80-90%"
        )
        st.session_state["required_comparisons"] = st.text_input(
            "4. Required Comparisons / Cohorts",
            value=st.session_state.get("required_comparisons", ""),
            placeholder="e.g. Compare regional performance, product tier variance, monthly trend"
        )
        
    with c_q2:
        st.session_state["target_audience"] = st.text_input(
            "5. Target Audience",
            value=st.session_state.get("target_audience", "Senior Leadership / Operations Director"),
            placeholder="e.g. Operations Director, Assessment Panel, Casework Team Leads"
        )
        st.session_state["response_time"] = st.text_input(
            "6. Response / Presentation Time Available",
            value=st.session_state.get("response_time", "15 minutes (10 mins presentation + 5 mins Q&A)"),
            placeholder="e.g. 10 mins briefing"
        )
        st.session_state["restrictions_rules"] = st.text_input(
            "7. Key Restrictions / Assessment Rules",
            value=st.session_state.get("restrictions_rules", ""),
            placeholder="e.g. Maximum 6 slides, evidence-based recommendations only, no hiring assumptions"
        )
        st.session_state["other_instructions"] = st.text_area(
            "8. Other Instructions / Working Assumptions / Analyst Notes",
            value=st.session_state.get("other_instructions", ""),
            height=90,
            placeholder="e.g. Assume baseline FTE remains constant; flag any data quality issues early."
        )

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        st.session_state["rapid_mode"] = st.checkbox(
            "⚡ **Enable Rapid Assessment Mode** (Streamlined navigation & quick-pass checks)",
            value=st.session_state.get("rapid_mode", False)
        )
    with col_btn2:
        if st.button("💾 Save Intake Context", use_container_width=True, type="primary"):
            st.success("Assessment context saved! Proceed to 01_Upload & Profile.")

st.markdown("---")

# Quick Workflow Navigation Guide
st.subheader("🧭 End-to-End Analytical Workflow")
w_col1, w_col2, w_col3 = st.columns(3)

with w_col1:
    st.markdown("""
    #### 1️⃣ Ingestion & Quality
    - **01 Upload & Profile:** Ingest dataset (`.csv`, `.xlsx`, `.xls`) & confirm **Row Granularity**.
    - **02 Data Quality:** Run structural & semantic checks, inspect nulls, zero denominators, and anomalies.
    - **03 Column Mapping:** Auto-detect and confirm roles (`volume`, `target`, `fte`, `wait_time`, `dates`).
    """)

with w_col2:
    st.markdown("""
    #### 2️⃣ Diagnostics & Drivers
    - **04 Performance Overview:** Review KPI scorecard against target directionality.
    - **05 Trends:** Evaluate time series, run charts, and stability.
    - **06 Comparisons:** Group variance analysis across operational cohorts.
    - **07 Driver Trees:** Root cause exploration and capacity/demand balancing.
    """)

with w_col3:
    st.markdown("""
    #### 3️⃣ Governance & Defense
    - **08 Insights:** Accept, edit, or reject data-backed findings.
    - **09 Recommendations:** Formulate actionable operational interventions.
    - **10 Interview View:** 13-Section Assessment Summary & Assessor Q&A Defense.
    - **11 Export:** Download 16:9 Widescreen PowerPoint with dynamic speaker notes & PDF reports.
    """)

st.markdown("---")
st.caption("🔒 **Analyst Integrity Principle:** The assessment brief determines the question. The dataset supplies the evidence. The analyst exercises professional judgement. All outputs are strictly derived from verified session state.")
