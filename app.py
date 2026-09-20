"""Performance Insight Explorer.
Enterprise Performance Analysis, Diagnostic and Decision-Support Platform.
Product Owner: Daramola Omoyele
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime

from core.constants import AppMode, UserRole, WorkflowStage, WORKFLOW_STAGES_ORDER
from core.state import (
    init_session_state, get_working_df, log_audit_event, advance_workflow_stage,
    save_project_bundle, load_project_bundle, invalidate_derived_state
)
from modules.ingestion.parser import read_file_contents
from modules.profiling.profiler import profile_dataset
from modules.mapping.mapper import suggest_semantic_mappings
from modules.quality.engine import evaluate_data_quality_10d
from src.brief_extractor import extract_assessment_brief

st.set_page_config(
    page_title="Performance Insight Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# -------------------------------------------------------------
# SIDEBAR: Mode Switcher, Role, Workflow Stepper & Project Persistence
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 Performance Insight Explorer")
    st.caption("Enterprise Performance Analysis & Decision-Support")
    
    # 1. Dual Mode Switcher
    mode_options = [AppMode.ORGANIZATION.value, AppMode.ASSESSMENT.value]
    current_mode = st.session_state.get("app_mode", AppMode.ORGANIZATION.value)
    mode_idx = mode_options.index(current_mode) if current_mode in mode_options else 0
    selected_mode = st.selectbox("🌐 Platform Mode", mode_options, index=mode_idx)
    if selected_mode != current_mode:
        st.session_state.app_mode = selected_mode
        log_audit_event("MODE_SWITCHED", f"Switched mode to {selected_mode}")
        st.rerun()

    # 2. User Role
    role_options = [UserRole.ADMIN.value, UserRole.ANALYST.value, UserRole.VIEWER.value]
    cur_role = st.session_state.get("user_role", UserRole.ANALYST.value)
    role_idx = role_options.index(cur_role) if cur_role in role_options else 1
    st.session_state.user_role = st.selectbox("👤 Active Role", role_options, index=role_idx)

    st.markdown("---")

    # 3. Project Save / Resume
    with st.expander("💾 Project Save & Resume", expanded=False):
        project_bundle_str = save_project_bundle()
        st.download_button(
            "⬇️ Export Project State (.json)",
            data=project_bundle_str,
            file_name=f"project_state_{st.session_state.get('project_state', {}).get('project_id', 'proj')}.json",
            mime="application/json",
            use_container_width=True
        )
        uploaded_proj = st.file_uploader("Restore Project State", type=["json"], key="restore_proj_file")
        if uploaded_proj is not None:
            if st.button("📂 Load Project Bundle", use_container_width=True, type="primary"):
                success, msg = load_project_bundle(uploaded_proj.getvalue().decode("utf-8"))
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # 4. Quick Demo Dataset Loader
    with st.expander("🚀 Instant Demo Datasets", expanded=False):
        demo_choice = st.selectbox(
            "Select Industry Dataset",
            [
                "None / Custom Upload",
                "Healthcare Service Performance (NHS ED Flow)",
                "Sales & Commercial Revenue",
                "Customer Service Operations (Omnichannel)",
                "Workforce HR & Turnover",
                "Local Government Planning & Enforcement"
            ]
        )
        if st.button("⚡ Load Selected Demo", use_container_width=True) and demo_choice != "None / Custom Upload":
            file_map = {
                "Healthcare Service Performance (NHS ED Flow)": "sample_data/healthcare_service_performance.csv",
                "Sales & Commercial Revenue": "sample_data/sales_revenue_performance.csv",
                "Customer Service Operations (Omnichannel)": "sample_data/customer_service_operations.csv",
                "Workforce HR & Turnover": "sample_data/workforce_hr_performance.csv",
                "Local Government Planning & Enforcement": "sample_data/local_government_service_delivery.csv"
            }
            path = file_map.get(demo_choice)
            if path:
                with open(path, "rb") as f:
                    content = f.read()
                df, sheets, meta = read_file_contents(content, path.split("/")[-1])
                st.session_state.raw_df = df
                st.session_state.clean_df = df.copy()
                st.session_state.dataset_name = demo_choice
                st.session_state.data_profile = profile_dataset(df, demo_choice)
                st.session_state.suggested_mappings = suggest_semantic_mappings(df)
                st.session_state.confirmed_mappings = {c: info["suggested_role"] for c, info in st.session_state.suggested_mappings.items() if info.get("confidence", 0) >= 0.50}
                st.session_state.qa_report = evaluate_data_quality_10d(df)
                st.session_state.row_granularity = st.session_state.data_profile.get("inferred_granularity", "Periodic Snapshot")
                st.session_state.row_granularity_confirmed = True
                advance_workflow_stage(WorkflowStage.STAGE_02_INGEST)
                advance_workflow_stage(WorkflowStage.STAGE_03_GRANULARITY)
                advance_workflow_stage(WorkflowStage.STAGE_04_QUALITY)
                advance_workflow_stage(WorkflowStage.STAGE_05_MAPPING)
                st.success(f"Loaded {demo_choice} ({len(df):,} records)")
                st.rerun()

    st.markdown("---")
    st.subheader("🔄 Safety & State Reset")
    if st.button("🧹 Clear Active Analysis", use_container_width=True):
        invalidate_derived_state()
        st.success("Cleared derived metric calculations.")
        st.rerun()

# -------------------------------------------------------------
# MAIN VIEW ROUTING: Organization Mode vs Assessment Mode
# -------------------------------------------------------------
if st.session_state.app_mode == AppMode.ORGANIZATION.value:
    # ---------------------------------------------------------
    # ENTERPRISE ORGANIZATION MODE
    # ---------------------------------------------------------
    st.title("📊 Performance Insight Explorer")
    st.markdown("#### Enterprise Performance Analysis, Diagnostic and Decision-Support Platform")
    st.caption(f"Active Organization: **{st.session_state.project_state.get('organization_name', 'Enterprise')}** | Lead Analyst: **{st.session_state.project_state.get('created_by', 'Daramola Omoyele')}**")

    # Workflow Stepper Banner
    st.markdown("---")
    st.subheader("🧭 Guided Analysis Lifecycle Progress")
    
    stages = [
        ("1. Question", WorkflowStage.STAGE_01_QUESTION),
        ("2. Ingest", WorkflowStage.STAGE_02_INGEST),
        ("3. Granularity", WorkflowStage.STAGE_03_GRANULARITY),
        ("4. Quality", WorkflowStage.STAGE_04_QUALITY),
        ("5. Mapping", WorkflowStage.STAGE_05_MAPPING),
        ("6. KPIs", WorkflowStage.STAGE_06_KPIS),
        ("7. Methods", WorkflowStage.STAGE_07_METHODS),
        ("8. Overview", WorkflowStage.STAGE_08_OVERVIEW),
        ("9. Trends", WorkflowStage.STAGE_09_TRENDS),
        ("10. Root Cause", WorkflowStage.STAGE_10_ROOT_CAUSE),
        ("11. Uncertainty", WorkflowStage.STAGE_11_UNCERTAINTY),
        ("12. Insights", WorkflowStage.STAGE_12_INSIGHTS),
        ("13. Actions", WorkflowStage.STAGE_13_RECOMMENDATIONS),
        ("14. Governance", WorkflowStage.STAGE_15_EXPORT)
    ]
    
    cols = st.columns(len(stages))
    completed = st.session_state.get("completed_stages", [])
    
    for i, (label, stage_enum) in enumerate(stages):
        is_done = stage_enum.value in completed
        with cols[i]:
            if is_done:
                st.markdown(f"**🟢 {label}**")
            else:
                st.markdown(f"⚪ {label}")

    st.markdown("---")

    # Active Dataset Status Alert
    if st.session_state.get("clean_df") is not None:
        df_active = st.session_state["clean_df"]
        qa_rep = st.session_state.get("qa_report", {})
        health_score = qa_rep.get("health_score", 100.0) if qa_rep else 100.0
        
        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
        with c_stat1:
            st.metric("📁 Active Dataset", st.session_state.get("dataset_name", "Uploaded File"))
        with c_stat2:
            st.metric("📏 Total Records", f"{len(df_active):,}")
        with c_stat3:
            st.metric("📐 Active Columns", f"{len(df_active.columns):,}")
        with c_stat4:
            st.metric("🛡️ Data Quality Index", f"{health_score:.1f}/100")
            
        if qa_rep and qa_rep.get("is_analysis_blocked", False):
            st.error("🚨 **CRITICAL DATA QUALITY ISSUES DETECTED:** Downstream analysis is blocked until critical issues are accepted or remediated in Stage 4.")
    else:
        st.info("ℹ️ **No active dataset loaded.** Start by defining the business question below or loading an industry demo from the sidebar.")

    # Stage 1: Business Question & Project Definition Form
    st.header("📋 Stage 1: Define Project Scope & Business Question")
    with st.container():
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.session_state.project_state["project_name"] = st.text_input(
                "Project Title",
                value=st.session_state.project_state.get("project_name", "Executive Operational Review")
            )
            st.session_state.project_state["organization_name"] = st.text_input(
                "Organization / Department",
                value=st.session_state.project_state.get("organization_name", "Enterprise Operations")
            )
            st.session_state.project_state["business_question"] = st.text_area(
                "Core Business Question / Performance Objective",
                value=st.session_state.project_state.get("business_question", "What are the primary operational bottlenecks, quality variances, and efficiency opportunities?"),
                height=100
            )
        with c_p2:
            st.session_state.project_state["target_audience"] = st.text_input(
                "Target Audience / Stakeholders",
                value=st.session_state.project_state.get("target_audience", "Executive Leadership & Board")
            )
            st.session_state.project_state["time_horizon"] = st.text_input(
                "Analysis Time Horizon",
                value=st.session_state.project_state.get("time_horizon", "Last 12 Months")
            )
            st.session_state.project_state["notes"] = st.text_area(
                "Strategic Context & Working Assumptions",
                value=st.session_state.project_state.get("notes", ""),
                height=100,
                placeholder="Operational context, regulatory constraints, or policy changes..."
            )

        if st.button("💾 Save Project Definition", type="primary"):
            advance_workflow_stage(WorkflowStage.STAGE_01_QUESTION)
            st.success("Project definition saved! Proceed to **01_Data_Ingestion**.")

    st.markdown("---")
    st.subheader("🚀 Platform Capabilities & Lifecycle Navigation")
    
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        st.markdown("""
        #### 1️⃣ Data Foundation
        - **01 Upload & Profile:** Ingest CSV, Excel, Parquet, JSON with chunking.
        - **02 Data Quality:** 10-dimension QA engine with interactive remediation.
        - **03 Column Mapping:** 25+ standard semantic roles with confidence scoring.
        - **04 KPI Configuration:** No-code formula builder with RAG directionality.
        """)
    with col_nav2:
        st.markdown("""
        #### 2️⃣ Diagnostics & Modeling
        - **05 Performance Overview:** Executive 3-tier dashboard & scorecard.
        - **06 Trends & Forecasts:** Statistical process control (SPC) & time-series.
        - **07 Comparisons & Cohorts:** ANOVA, Cohen's d effect sizes, and quartiles.
        - **08 Root Cause:** 10-step RCA workflow, driver trees, and 5-Whys.
        """)
    with col_nav3:
        st.markdown("""
        #### 3️⃣ Action & Governance
        - **09 Evidence Insights:** Curated deterministic findings.
        - **10 Recommendations:** Impact × Effort prioritization & traceability.
        - **11 Action Tracking:** Realization dashboard with causality warnings.
        - **12 Scenario Simulator:** Interactive what-if forecasting.
        - **13 Reporting & Exports:** Sanitized Excel packs, PPTX decks, and PDF briefs.
        """)

else:
    # ---------------------------------------------------------
    # PRESERVED ASSESSMENT MODE (Candidate / Timed Workflow)
    # ---------------------------------------------------------
    st.title("🎯 Assessment Hub (Practical Assessment Mode)")
    st.markdown("### Operational Performance & Diagnostic Toolkit for Practical Assessments")
    st.caption("Candidate / Analyst: **DARAMOLA OMOYELE** | Performance Analyst Assessment Ready")

    st.info("""
    ⚠️ **Assessment Rules Check:** Ensure using this tool aligns with assessment instructions.
    All prompt cards, time-limited intake fields, and interview summaries are preserved in this mode.
    """)

    st.header("📋 Stage 0: Assessment Pack Intake")
    brief_file = st.file_uploader("Upload Assessment Brief (.docx, .pdf, .txt)", type=["docx", "doc", "pdf", "txt", "md"])
    if brief_file is not None:
        try:
            b_res = extract_assessment_brief(brief_file.getvalue(), brief_file.name)
            st.session_state.assessment_brief_data = {
                "filename": brief_file.name,
                "raw_text": b_res.get("raw_text", ""),
                "questions": b_res.get("questions", []),
                "question_count": b_res.get("question_count", 0),
                "is_loaded": True
            }
            if b_res.get("questions"):
                st.session_state.questions_must_answer = "\n".join(b_res["questions"])
            st.success(f"Extracted {b_res.get('question_count', 0)} questions from `{brief_file.name}`")
        except Exception as e:
            st.error(f"Error reading brief: {e}")

    c_a1, c_a2 = st.columns(2)
    with c_a1:
        st.session_state.assessment_question = st.text_area(
            "1. Core Problem Statement / Main Question",
            value=st.session_state.get("assessment_question", ""),
            height=80
        )
        st.session_state.questions_must_answer = st.text_area(
            "2. Specific Questions to Answer (one per line)",
            value=st.session_state.get("questions_must_answer", ""),
            height=80
        )
    with c_a2:
        st.session_state.target_audience = st.text_input(
            "3. Target Audience",
            value=st.session_state.get("target_audience", "Assessment Panel / Leadership")
        )
        st.session_state.response_time = st.text_input(
            "4. Time Available",
            value=st.session_state.get("response_time", "45 Minutes")
        )

    st.session_state.rapid_mode = st.checkbox("⚡ Enable Rapid Assessment Mode", value=st.session_state.get("rapid_mode", False))

    if st.button("💾 Save Assessment Context", type="primary"):
        st.success("Assessment context saved! Use **15_Assessment_Hub** for prompt cards and Q&A defense.")
