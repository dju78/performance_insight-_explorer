"""Performance Insight Explorer.
Enterprise Performance Analysis, Diagnostic and Decision-Support Platform.
Product Owner: Daramola Omoyele
"""
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.constants import AppMode, UserRole, WorkflowStage
from core.security import is_index_like_column, sanitize_dataframe_for_export, apply_statistical_suppression
from core.state import (
    init_session_state, get_working_df, log_audit_event, advance_workflow_stage,
    save_project_bundle, load_project_bundle, invalidate_derived_state, clear_dataset_state
)
from modules.ingestion.parser import read_file_contents
from modules.profiling.profiler import profile_dataset
from modules.mapping.mapper import suggest_semantic_mappings
from modules.quality.engine import evaluate_data_quality_10d, remediate_quality_issue
from modules.analysis.orchestrator import run_full_performance_analysis
from modules.insights.engine import normalize_finding, normalize_recommendation
from modules.forecasting.simulator import simulate_what_if_scenario
from modules.reporting.export_builder import (
    build_excel_evidence_pack, build_powerpoint_presentation, build_executive_pdf
)
from src.brief_extractor import extract_assessment_brief

st.set_page_config(
    page_title="Enterprise Performance Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# -------------------------------------------------------------
# SIDEBAR: Quick Controls, Demos, Persistence & Inconspicuous Mode
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 Enterprise Performance Platform")
    st.caption("Diagnostic & Decision-Support System")
    
    # Quick Demo Dataset Loader
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
            clear_dataset_state()
            file_map = {
                "Healthcare Service Performance (NHS ED Flow)": "sample_data/healthcare_service_performance.csv",
                "Sales & Commercial Revenue": "sample_data/sales_revenue_performance.csv",
                "Customer Service Operations (Omnichannel)": "sample_data/customer_service_operations.csv",
                "Workforce HR & Turnover": "sample_data/workforce_hr_performance.csv",
                "Local Government Planning & Enforcement": "sample_data/local_government_service_delivery.csv"
            }
            demo_objectives = {
                "Healthcare Service Performance (NHS ED Flow)": "Identify why patient wait times and 4-hour breach rates are rising across clinical departments, compare department flow, and recommend operational mitigations.",
                "Sales & Commercial Revenue": "Analyze commercial revenue trends, identify underperforming sales regions, and discover key drivers of deal conversion.",
                "Customer Service Operations (Omnichannel)": "Evaluate customer handle times, identify team capacity bottlenecks, and improve first-contact resolution.",
                "Workforce HR & Turnover": "Examine employee turnover across directorates, evaluate tenure and flight-risk drivers, and prioritize retention interventions.",
                "Local Government Planning & Enforcement": "Assess planning enforcement turnaround days, identify statutory timeline breaches across wards, and streamline case workflows."
            }
            path = file_map.get(demo_choice)
            if path:
                with open(path, "rb") as f:
                    content = f.read()
                df, sheets, meta = read_file_contents(content, path.split("/")[-1])
                st.session_state.raw_df = df
                st.session_state.clean_df = df.copy()
                st.session_state.dataset_name = demo_choice
                st.session_state.uploaded_file_name = path.split("/")[-1]
                st.session_state.objective_input = demo_objectives.get(demo_choice, "")
                st.session_state.suggested_mappings = suggest_semantic_mappings(df)
                st.session_state.confirmed_mappings = {
                    c: info["suggested_role"] for c, info in st.session_state.suggested_mappings.items()
                    if info.get("confidence", 0) >= 0.50
                }
                st.session_state.qa_report = evaluate_data_quality_10d(df)
                st.session_state.analysis_results = None
                log_audit_event("DEMO_LOADED", f"Loaded demo dataset {demo_choice}")
                st.success(f"✅ Loaded {demo_choice} ({len(df):,} rows, {len(df.columns)} columns)")
                st.rerun()

    # Project Save / Resume
    with st.expander("💾 Save & Resume Project", expanded=False):
        project_bundle_str = save_project_bundle()
        st.download_button(
            "⬇️ Export Project State (.json)",
            data=project_bundle_str,
            file_name=f"project_state_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
        uploaded_proj = st.file_uploader("Restore Project (.json)", type=["json"], key="restore_proj_file")
        if uploaded_proj is not None:
            if st.button("📂 Load Project", use_container_width=True, type="primary"):
                success, msg = load_project_bundle(uploaded_proj.getvalue().decode("utf-8"))
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # Clear state button
    if st.button("🔄 Reset Analysis State", use_container_width=True):
        clear_dataset_state()
        st.success("Analysis state reset.")
        st.rerun()

    st.markdown("---")
    # Inconspicuous Assessment Mode toggle
    with st.expander("⚙️ Advanced Workflow Mode", expanded=False):
        mode_options = [AppMode.ORGANIZATION.value, AppMode.ASSESSMENT.value]
        cur_mode = st.session_state.get("app_mode", AppMode.ORGANIZATION.value)
        mode_idx = mode_options.index(cur_mode) if cur_mode in mode_options else 0
        selected_mode = st.selectbox("Operating Mode", mode_options, index=mode_idx)
        if selected_mode != cur_mode:
            st.session_state.app_mode = selected_mode
            log_audit_event("MODE_SWITCHED", f"Switched mode to {selected_mode}")
            st.rerun()

# -------------------------------------------------------------
# MAIN VIEW
# -------------------------------------------------------------
if st.session_state.get("app_mode") == AppMode.ASSESSMENT.value:
    # ---------------------------------------------------------
    # ASSESSMENT MODE (Preserved candidate hub)
    # ---------------------------------------------------------
    st.title("🎯 Assessment Hub (Practical Assessment Mode)")
    st.caption("Operational Performance & Diagnostic Toolkit for Practical Assessments")
    brief_file = st.file_uploader("Upload Assessment Brief (.docx, .pdf, .txt)", type=["docx", "doc", "pdf", "txt", "md"])
    if brief_file is not None:
        try:
            b_res = extract_assessment_brief(brief_file.getvalue(), brief_file.name)
            st.session_state.questions_must_answer = "\n".join(b_res.get("questions", []))
            st.success(f"Extracted {b_res.get('question_count', 0)} questions from `{brief_file.name}`")
        except Exception as e:
            st.error(f"Error reading brief: {e}")

    c_a1, c_a2 = st.columns(2)
    with c_a1:
        st.session_state.assessment_question = st.text_area("Core Problem Statement", value=st.session_state.get("assessment_question", ""), height=80)
        st.session_state.questions_must_answer = st.text_area("Specific Questions to Answer", value=st.session_state.get("questions_must_answer", ""), height=80)
    with c_a2:
        st.session_state.target_audience = st.text_input("Target Audience", value=st.session_state.get("target_audience", "Assessment Panel"))
        st.session_state.response_time = st.text_input("Time Available", value=st.session_state.get("response_time", "45 Minutes"))
else:
    # ---------------------------------------------------------
    # UNIFIED ENTERPRISE PERFORMANCE PLATFORM
    # ---------------------------------------------------------
    st.title("📊 Enterprise Performance Analysis, Diagnostic and Decision-Support Platform")
    st.caption("Product Owner: **Daramola Omoyele** | Unified Performance Platform")

    # Active Dataset Status Banner
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
    else:
        st.info("ℹ️ **No active dataset loaded.** Start by defining the objective and uploading data below, or load an instant demo from the sidebar.")

    # Expandable Advanced Professional Workflow Lifecycle Overview
    with st.expander("🔬 Advanced Professional Workflow (14-Stage Enterprise Lifecycle)", expanded=False):
        st.markdown("##### 🧭 14-Stage Guided Analysis Lifecycle Progress")
        stages = [
            ("1. Scope", WorkflowStage.STAGE_01_QUESTION),
            ("2. Ingest", WorkflowStage.STAGE_02_INGEST),
            ("3. Granularity", WorkflowStage.STAGE_03_GRANULARITY),
            ("4. QA", WorkflowStage.STAGE_04_QUALITY),
            ("5. Mapping", WorkflowStage.STAGE_05_MAPPING),
            ("6. KPIs", WorkflowStage.STAGE_06_KPIS),
            ("7. Methods", WorkflowStage.STAGE_07_METHODS),
            ("8. Overview", WorkflowStage.STAGE_08_OVERVIEW),
            ("9. Trends", WorkflowStage.STAGE_09_TRENDS),
            ("10. Root Cause", WorkflowStage.STAGE_10_ROOT_CAUSE),
            ("11. Uncertainty", WorkflowStage.STAGE_11_UNCERTAINTY),
            ("12. Insights", WorkflowStage.STAGE_12_INSIGHTS),
            ("13. Actions", WorkflowStage.STAGE_13_RECOMMENDATIONS),
            ("14. Tracking", WorkflowStage.STAGE_14_ACTIONS),
            ("15. Governance", WorkflowStage.STAGE_15_EXPORT)
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
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            st.markdown("""
            **1️⃣ Data Foundation**
            - **01 Upload & Profile:** Ingest CSV, Excel, Parquet, JSON with chunking.
            - **02 Data Quality:** 10-dimension QA engine with interactive remediation.
            - **03 Column Mapping:** 25+ standard semantic roles with confidence scoring.
            - **04 KPI Configuration:** No-code formula builder with RAG directionality.
            """)
        with col_nav2:
            st.markdown("""
            **2️⃣ Diagnostics & Modeling**
            - **05 Performance Overview:** Executive 3-tier dashboard & scorecard.
            - **06 Trends & Forecasts:** Statistical process control (SPC) & time-series.
            - **07 Comparisons & Cohorts:** ANOVA, Cohen's d effect sizes, and quartiles.
            - **08 Root Cause:** 10-step RCA workflow, driver trees, and 5-Whys.
            """)
        with col_nav3:
            st.markdown("""
            **3️⃣ Stakeholder Briefing & Governance**
            - **09 Recommendations:** Impact × Effort prioritization & traceability.
            - **10 Public Presentation:** 12-section evidence briefing, slide view, and executive memo.
            - **11 Export Hub:** Sanitized Excel packs, PPTX decks, and PDF briefs.
            - **12 Audit Trail:** Cryptographic integrity log & transformation provenance.
            """)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 1. Objective & Data",
        "🛡️ 2. Data Quality",
        "📊 3. Dashboard & Analysis",
        "💡 4. Findings, Recommendations & Export"
    ])

    df = get_working_df()

    # =========================================================
    # TAB 1: OBJECTIVE & DATA
    # =========================================================
    with tab1:
        st.markdown("### Step 1: What do you want to achieve?")
        objective_val = st.text_area(
            "What do you want to achieve with this data?",
            value=st.session_state.get("objective_input", ""),
            help="Describe the performance question, problem or decision you want the analysis to address.",
            placeholder="e.g. Identify why customer response times are increasing, compare team performance and recommend practical improvements.",
            height=90,
            key="user_objective_area"
        )
        st.session_state.objective_input = objective_val

        specific_questions_val = st.text_area(
            "Specific questions you want answered (Optional)",
            value=st.session_state.get("specific_questions_input", ""),
            help="Enter specific questions you want answered, one per line.",
            placeholder="1. Which teams are experiencing the highest backlog?\n2. Are response times statistically deteriorating over time?\n3. What are the key drivers of resolution delays?",
            height=90,
            key="user_specific_questions_area"
        )
        st.session_state.specific_questions_input = specific_questions_val

        st.markdown("---")
        st.markdown("### Step 2: Upload your data")
        uploaded_file = st.file_uploader(
            "Upload your dataset (CSV, Excel, JSON, Parquet)",
            type=["csv", "xlsx", "xls", "json", "parquet"],
            help="Upload structured tabular performance data."
        )

        if uploaded_file is not None:
            if st.session_state.get("uploaded_file_name") != uploaded_file.name:
                clear_dataset_state()
                content_bytes = uploaded_file.getvalue()
                df_parsed, sheet_names, meta = read_file_contents(content_bytes, uploaded_file.name)
                
                if sheet_names and len(sheet_names) > 1:
                    selected_sheet = st.selectbox("Select Excel Sheet", sheet_names)
                    df_parsed, _, meta = read_file_contents(content_bytes, uploaded_file.name, sheet_name=selected_sheet)
                    
                st.session_state.raw_df = df_parsed
                st.session_state.clean_df = df_parsed.copy()
                st.session_state.dataset_name = uploaded_file.name
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.suggested_mappings = suggest_semantic_mappings(df_parsed)
                st.session_state.confirmed_mappings = {
                    c: info["suggested_role"] for c, info in st.session_state.suggested_mappings.items()
                    if info.get("confidence", 0) >= 0.50
                }
                st.session_state.qa_report = evaluate_data_quality_10d(df_parsed)
                log_audit_event("FILE_UPLOADED", f"Uploaded {uploaded_file.name} ({len(df_parsed)} rows)")
                st.success(f"✅ Ingested `{uploaded_file.name}` ({len(df_parsed):,} rows, {len(df_parsed.columns)} columns)")

        # Re-fetch active dataframe
        df = get_working_df()

        if df is not None and len(df) > 0:
            st.markdown("#### 📋 Data Overview")
            
            # Detect column types
            detected_numeric = [
                c for c in df.select_dtypes(include=[np.number]).columns
                if not is_index_like_column(c, df[c]) and not pd.api.types.is_bool_dtype(df[c])
            ]
            detected_categories = [
                c for c in df.select_dtypes(include=["object", "category", "string"]).columns
                if not is_index_like_column(c, df[c])
            ]
            detected_dates = []
            for c in df.columns:
                if is_index_like_column(c, df[c]):
                    continue
                if pd.api.types.is_datetime64_any_dtype(df[c]):
                    detected_dates.append(c)
                elif any(k in str(c).lower() for k in ["date", "month", "period", "timestamp", "time", "year", "quarter"]):
                    detected_dates.append(c)

            # Date range calculation
            date_range_str = "No chronological date detected"
            if detected_dates:
                primary_dt = detected_dates[0]
                try:
                    parsed_dt = pd.to_datetime(df[primary_dt], errors="coerce", format="mixed").dropna()
                    if len(parsed_dt) > 0:
                        date_range_str = f"{parsed_dt.min().strftime('%Y-%m-%d')} to {parsed_dt.max().strftime('%Y-%m-%d')}"
                except Exception:
                    pass

            # Summary metrics
            total_missing = int(df.isna().sum().sum())
            missing_pct = (total_missing / (len(df) * max(len(df.columns), 1))) * 100.0
            total_dups = int(df.duplicated().sum())

            c_ov1, c_ov2, c_ov3, c_ov4, c_ov5, c_ov6 = st.columns(6)
            with c_ov1:
                st.metric("📁 File Name", st.session_state.get("dataset_name", "Data"))
            with c_ov2:
                st.metric("📏 Total Rows", f"{len(df):,}")
            with c_ov3:
                st.metric("📐 Columns", f"{len(df.columns):,}")
            with c_ov4:
                st.metric("📅 Date Range", date_range_str)
            with c_ov5:
                st.metric("⚠️ Missing Cells", f"{total_missing:,} ({missing_pct:.1f}%)")
            with c_ov6:
                st.metric("🔄 Duplicate Rows", f"{total_dups:,}")

            # Column Confirmation Controls
            st.markdown("##### ⚙️ Confirm Analysis Dimensions")
            c_conf1, c_conf2, c_conf3, c_conf4 = st.columns(4)
            with c_conf1:
                date_options = ["None / Auto-Detect"] + detected_dates + [c for c in df.columns if c not in detected_dates and not is_index_like_column(c, df[c])]
                sel_date = st.selectbox("Chronological Date / Period", date_options, index=1 if detected_dates else 0)
                selected_date_col = sel_date if sel_date != "None / Auto-Detect" else None
            with c_conf2:
                metric_options = detected_numeric if detected_numeric else df.columns.tolist()
                selected_metric_col = st.selectbox("Primary Performance Measure", metric_options, index=0)
            with c_conf3:
                group_options = ["None / Overall Only"] + detected_categories + [c for c in df.columns if c not in detected_categories and not is_index_like_column(c, df[c])]
                sel_group = st.selectbox("Cohort / Grouping Dimension", group_options, index=1 if detected_categories else 0)
                selected_group_col = sel_group if sel_group != "None / Overall Only" else None
            with c_conf4:
                target_val = st.number_input("Target / Benchmark Value (Optional)", value=0.0, step=1.0, help="Set to 0 if no target exists.")
                target_num = target_val if target_val > 0 else None

            st.markdown("---")
            st.markdown("### Step 3: Run performance analysis")
            
            if st.button("🚀 Analyse Performance", type="primary", use_container_width=True):
                with st.spinner("Executing comprehensive performance diagnostics, quality scoring, trends, and recommendations..."):
                    try:
                        analysis_output = run_full_performance_analysis(
                            df=df,
                            objective_text=objective_val,
                            specific_questions=specific_questions_val,
                            date_col=selected_date_col,
                            metric_col=selected_metric_col,
                            group_col=selected_group_col,
                            target_val=target_num
                        )
                        if analysis_output and isinstance(analysis_output, dict) and "metric_mean" in analysis_output:
                            st.session_state.analysis_results = analysis_output
                            st.session_state.selected_metric_col = selected_metric_col
                            st.session_state.selected_date_col = selected_date_col
                            st.session_state.selected_group_col = selected_group_col
                            st.session_state.selected_target_val = target_num
                            log_audit_event("ANALYSIS_EXECUTED", f"Executed analysis for {selected_metric_col}")
                            st.success("✅ Analysis Complete! Switch to **📊 Dashboard & Analysis** or **💡 Findings, Recommendations & Export** to explore results.")
                        else:
                            st.error("Analysis completed but output validation failed. Please verify your selected columns.")
                    except Exception as ex:
                        st.error(f"Analysis failed to complete: {ex}")
        else:
            st.info("💡 Upload a data file above or select an **Instant Demo Dataset** from the sidebar to get started.")

    # =========================================================
    # TAB 2: DATA QUALITY
    # =========================================================
    with tab2:
        st.markdown("### 🛡️ Data Quality & Integrity Assessment")
        if df is None or len(df) == 0:
            st.warning("⚠️ No active dataset loaded. Please upload data on Tab 1.")
        else:
            qa_rep = evaluate_data_quality_10d(df)
            health = qa_rep.get("health_score", 100.0)
            
            c_q1, c_q2, c_q3 = st.columns(3)
            with c_q1:
                st.metric("🛡️ Overall Quality Index", f"{health:.1f}/100")
            with c_q2:
                st.metric("🚨 Blocking / Critical Issues", len([i for i in qa_rep.get("issues", []) if i.get("severity") in ["CRITICAL", "BLOCKING"]]))
            with c_q3:
                st.metric("⚠️ Warnings & Advisories", len([i for i in qa_rep.get("issues", []) if i.get("severity") in ["WARNING", "ADVISORY"]]))

            # Issues table & remediation
            issues = qa_rep.get("issues", [])
            if issues:
                st.markdown("#### 🔍 Detected Quality Issues")
                for idx, iss in enumerate(issues):
                    sev = iss.get("severity", "WARNING")
                    badge = "🔴" if sev in ["CRITICAL", "BLOCKING"] else "🟡"
                    with st.expander(f"{badge} {iss.get('rule_name', 'Issue')} — {iss.get('details', '')}", expanded=(idx < 2)):
                        st.markdown(f"**Impact:** {iss.get('impact', 'May introduce distortion in calculations.')}")
                        st.markdown(f"**Recommended Fix:** {iss.get('remediation', 'Review records.')}")
                        
                        col_rem1, col_rem2 = st.columns([1, 4])
                        with col_rem1:
                            if st.button(f"Apply Auto-Remediation #{idx+1}", key=f"btn_rem_{idx}"):
                                rem_df, success, msg = remediate_quality_issue(df, iss.get("rule_name", ""), iss.get("column", ""))
                                if success:
                                    st.session_state.clean_df = rem_df
                                    st.session_state.qa_report = evaluate_data_quality_10d(rem_df)
                                    log_audit_event("QUALITY_REMEDIATION", f"Applied fix for {iss.get('rule_name')}: {msg}")
                                    st.success(f"Applied fix: {msg}")
                                    st.rerun()
                                else:
                                    st.warning(msg)
            else:
                st.success("✅ **Exceptional Data Quality:** No critical anomalies, duplicates, or format breaches detected.")

            # Audit Trail
            with st.expander("📜 Data Transformation Audit Log", expanded=False):
                audit_entries = st.session_state.get("audit_trail", [])
                if audit_entries:
                    st.dataframe(pd.DataFrame(audit_entries)[["timestamp", "event_type", "details"]], use_container_width=True)
                else:
                    st.caption("No data modifications recorded.")

    # =========================================================
    # TAB 3: DASHBOARD & ANALYSIS
    # =========================================================
    with tab3:
        try:
            analysis_res = st.session_state.get("analysis_results")
            if not analysis_res:
                st.info("ℹ️ Please click **🚀 Analyse Performance** on **Tab 1: Objective & Data** to generate the dashboard.")
            else:
                summary = analysis_res.get("summary", {})
                st.markdown("### 📊 Executive Performance Summary")
                
                # Summary KPI Ribbon
                c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
                with c_sum1:
                    st.metric("🏆 Strongest Cohort", summary.get("strongest_area", "N/A"))
                with c_sum2:
                    st.metric("⚠️ Weakest Cohort", summary.get("weakest_area", "N/A"))
                with c_sum3:
                    st.metric("📈 Largest Improvement", summary.get("largest_improvement", "N/A"))
                with c_sum4:
                    st.metric("🎯 Target Status", summary.get("target_achievement", "N/A"))

                st.info(f"💡 **Key Finding:** {summary.get('main_result', '')}")
                if "Quality Index" in summary.get("quality_warning", ""):
                    st.caption(f"🛡️ {summary.get('quality_warning')}")

                st.markdown("---")
                st.markdown("### 📈 Essential Performance Visualizations")

                metric_col = analysis_res.get("metric_col")
                date_col = analysis_res.get("date_col")
                group_col = analysis_res.get("group_col")
                spc_df = analysis_res.get("spc_df", pd.DataFrame())
                comp_res = analysis_res.get("comparison_results", {})
                groups_tbl = comp_res.get("groups_table", pd.DataFrame())
                pareto_df = analysis_res.get("pareto_df", pd.DataFrame())

                # 1. Time-Series Trend Chart (if date exists)
                if not spc_df.empty and date_col and metric_col:
                    st.subheader(f"1️⃣ Longitudinal Trend & Stability: {metric_col}")
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=spc_df[date_col], y=spc_df[metric_col],
                        mode="lines+markers", name="Observed",
                        line=dict(color="#0d6efd", width=2.5)
                    ))
                    fig_trend.add_trace(go.Scatter(
                        x=spc_df[date_col], y=spc_df["center_line"],
                        mode="lines", name="Process Mean",
                        line=dict(color="#198754", dash="dash", width=2)
                    ))
                    if len(spc_df) >= 5:
                        fig_trend.add_trace(go.Scatter(
                            x=spc_df[date_col], y=spc_df["ucl_3sigma"],
                            mode="lines", name="UCL (+3σ)",
                            line=dict(color="#dc3545", dash="dot", width=1.5)
                        ))
                        fig_trend.add_trace(go.Scatter(
                            x=spc_df[date_col], y=spc_df["lcl_3sigma"],
                            mode="lines", name="LCL (-3σ)",
                            line=dict(color="#dc3545", dash="dot", width=1.5)
                        ))
                    fig_trend.update_layout(
                        title=f"Chronological Trajectory of {metric_col} over {date_col}",
                        xaxis_title=date_col, yaxis_title=f"{metric_col} (Mean)",
                        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Plain English interpretation
                    first_p = spc_df[metric_col].iloc[0]
                    last_p = spc_df[metric_col].iloc[-1]
                    net_chg = ((last_p - first_p) / max(first_p, 0.001)) * 100.0 if first_p != 0 else 0.0
                    st.caption(f"📝 **Trend Interpretation:** '{metric_col}' changed by {net_chg:+.1f}% from the first period ({spc_df[date_col].iloc[0]}) to the latest period ({spc_df[date_col].iloc[-1]}).")

                # 2. Group Comparison Bar Chart
                if not groups_tbl.empty and group_col and metric_col:
                    st.subheader(f"2️⃣ Cohort Comparison: {metric_col} by {group_col}")
                    fig_bar = px.bar(
                        groups_tbl, x=group_col, y="mean", color="mean",
                        color_continuous_scale="Blues", text="mean",
                        title=f"Mean {metric_col} across {group_col} Cohorts"
                    )
                    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig_bar.update_layout(xaxis_title=group_col, yaxis_title=f"Mean {metric_col}")
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    top_name = groups_tbl.iloc[0][group_col]
                    bot_name = groups_tbl.iloc[-1][group_col]
                    gap_val = groups_tbl.iloc[0]["mean"] - groups_tbl.iloc[-1]["mean"]
                    st.caption(f"📝 **Comparison Interpretation:** Top-performing cohort is '{top_name}' ({groups_tbl.iloc[0]['mean']:,.2f}) vs lowest '{bot_name}' ({groups_tbl.iloc[-1]['mean']:,.2f}), representing a spread of {abs(gap_val):,.2f} units.")

                # 3. Distribution & Outlier Spread (Box Plot & Histogram)
                if metric_col and metric_col in df.columns:
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        st.subheader(f"3️⃣ Distribution: {metric_col}")
                        fig_hist = px.histogram(
                            df, x=metric_col, nbins=25, marginal="rug",
                            title=f"Frequency Distribution of {metric_col}",
                            color_discrete_sequence=["#0d6efd"]
                        )
                        fig_hist.update_layout(xaxis_title=metric_col, yaxis_title="Record Count")
                        st.plotly_chart(fig_hist, use_container_width=True)
                    with c_d2:
                        st.subheader("4️⃣ Outliers & Interquartile Spread")
                        fig_box = px.box(
                            df, x=group_col if group_col and group_col in df.columns else None,
                            y=metric_col, points="outliers",
                            title=f"Variation Spread & Outliers for {metric_col}",
                            color_discrete_sequence=["#198754"]
                        )
                        st.plotly_chart(fig_box, use_container_width=True)

                # 4. Pareto 80/20 Concentration (if groups exist)
                if not pareto_df.empty and group_col and metric_col and len(pareto_df) >= 3:
                    st.subheader(f"5️⃣ Pareto 80/20 Concentration Curve: {group_col}")
                    fig_pareto = go.Figure()
                    fig_pareto.add_trace(go.Bar(
                        x=pareto_df[group_col], y=pareto_df[metric_col],
                        name="Volume / Sum", marker_color="#0d6efd"
                    ))
                    fig_pareto.add_trace(go.Scatter(
                        x=pareto_df[group_col], y=pareto_df["cumulative_share_pct"],
                        name="Cumulative Share %", yaxis="y2",
                        line=dict(color="#dc3545", width=2.5)
                    ))
                    fig_pareto.update_layout(
                        title=f"Pareto 80/20 Rule: Cumulative Contribution of {group_col}",
                        yaxis=dict(title=f"Total {metric_col}"),
                        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_pareto, use_container_width=True)
                    
                    top_80 = pareto_df[pareto_df["is_top_80pct"] == True]
                    st.caption(f"📝 **Pareto Interpretation:** {len(top_80)} of {len(pareto_df)} cohorts account for 80% of cumulative volume in '{metric_col}'.")

                # -------------------------------------------------
                # COLLAPSIBLE ADVANCED ANALYSIS SECTION
                # -------------------------------------------------
                st.markdown("---")
                with st.expander("🔬 Advanced Statistical Analysis & Diagnostics", expanded=False):
                    st.markdown("#### Statistical Significance & Driver Models")
                    
                    # ANOVA Significance
                    p_val = comp_res.get("anova_p_value")
                    cohen = comp_res.get("cohens_d")
                    if p_val is not None:
                        c_st1, c_st2 = st.columns(2)
                        with c_st1:
                            st.metric("ANOVA F-Test p-value", f"{p_val:.4f}", delta="Statistically Significant" if p_val < 0.05 else "Not Significant")
                        with c_st2:
                            st.metric("Cohen's d Effect Size (Top vs Bottom)", f"{cohen:.2f}" if cohen is not None else "N/A")
                        st.caption("ℹ️ *Statistical Note:* $p < 0.05$ indicates differences between cohorts are unlikely to be caused by random chance alone.")

                    # Regression Drivers & Scatter Plot
                    reg_sum = analysis_res.get("regression_summary", {})
                    driver_results = analysis_res.get("driver_results", [])
                    if reg_sum.get("r_squared") is not None:
                        st.markdown(f"**Multivariate OLS Regression ($R^2 = {reg_sum['r_squared']:.1%}$):** Explains variance in `{metric_col}`.")
                        driver_weights = reg_sum.get("driver_weights", {})
                        if driver_weights:
                            st.dataframe(pd.DataFrame(list(driver_weights.items()), columns=["Operational Driver", "Relative Weight (%)"]), use_container_width=True)

                    if driver_results and metric_col:
                        st.markdown("#### 🎯 Driver Scatter Relationship & Trendline")
                        top_driver = driver_results[0]["driver_field"]
                        sub_clean = df[[top_driver, metric_col]].dropna().copy()
                        sub_clean[top_driver] = pd.to_numeric(sub_clean[top_driver], errors="coerce")
                        sub_clean[metric_col] = pd.to_numeric(sub_clean[metric_col], errors="coerce")
                        sub_clean = sub_clean.dropna()
                        if len(sub_clean) >= 3:
                            try:
                                fig_sc = px.scatter(
                                    sub_clean, x=top_driver, y=metric_col,
                                    trendline="ols" if len(sub_clean) >= 5 else None,
                                    title=f"Driver Relationship: {top_driver} vs {metric_col}"
                                )
                            except Exception:
                                fig_sc = px.scatter(
                                    sub_clean, x=top_driver, y=metric_col,
                                    title=f"Driver Relationship: {top_driver} vs {metric_col}"
                                )
                            st.plotly_chart(fig_sc, use_container_width=True)

                    # Interactive What-If Simulator
                    st.markdown("#### 🔮 What-If Scenario Sensitivity Simulator")
                    sim_pct = st.slider("Simulate Metric Improvement / Reduction (%)", min_value=-50, max_value=50, value=10, step=5)
                    desc_st = analysis_res.get("descriptive_stats", {})
                    cur_mean = desc_st.get("mean", 0.0)
                    sim_res = simulate_what_if_scenario(cur_mean, float(sim_pct), "Mean Performance Score")
                    c_w1, c_w2, c_w3 = st.columns(3)
                    with c_w1:
                        st.metric("Baseline Mean", f"{sim_res['baseline_metric']:,.2f}")
                    with c_w2:
                        st.metric("Simulated Outcome", f"{sim_res['simulated_metric']:,.2f}")
                    with c_w3:
                        st.metric("Projected Delta", f"{sim_res['delta_absolute']:+,.2f} ({sim_res['delta_percentage']:+.1f}%)")
        except Exception as e:
            st.error(f"An error occurred while displaying the dashboard: {e}")

    # =========================================================
    # TAB 4: FINDINGS, RECOMMENDATIONS & EXPORT
    # =========================================================
    with tab4:
        try:
            analysis_res = st.session_state.get("analysis_results")
            if not analysis_res:
                st.info("ℹ️ Please run the analysis on Tab 1 to view findings and download reports.")
            else:
                objective_title = analysis_res.get("objective", "Performance Evaluation")
                st.markdown(f"### 💡 Evidence Findings & Action Plan")
                st.caption(f"Tied to Objective: **{objective_title}**")

                findings_raw = analysis_res.get("findings", [])
                recs_raw = analysis_res.get("recommendations", [])

                # Safely normalize findings
                normalized_findings = []
                if isinstance(findings_raw, (list, tuple)):
                    for f in findings_raw:
                        norm_f = normalize_finding(f)
                        if norm_f:
                            normalized_findings.append(norm_f)
                elif findings_raw:
                    norm_f = normalize_finding(findings_raw)
                    if norm_f:
                        normalized_findings.append(norm_f)

                # Findings Grid
                if normalized_findings:
                    st.subheader("🔍 What Happened & Why (Deterministic Evidence)")
                    for f_item in normalized_findings:
                        try:
                            f_title = f_item.get("title", "Performance Finding")
                            f_level = f_item.get("evidence_level", "Not assessed")
                            with st.expander(f"📌 {f_title} — Evidence Level: {f_level}", expanded=True):
                                if f_item.get("description"):
                                    st.markdown(f"**What happened:** {f_item['description']}")
                                st.markdown(f"**Where it occurred:** Cohort dimension `{f_item.get('where', analysis_res.get('group_col', 'System-wide'))}`")
                                st.markdown(f"**When it occurred:** Time period `{f_item.get('when', analysis_res.get('date_col', 'Entire Period'))}`")
                                if f_item.get("impact"):
                                    st.markdown(f"**Impact / Gap:** {f_item['impact']}")
                                if f_item.get("limitation"):
                                    st.markdown(f"**Limitations & Caveats:** {f_item['limitation']}")
                        except Exception as err:
                            st.warning(f"Could not render finding: {err}")
                else:
                    st.info("No anomalous deviations detected in the uploaded dataset.")

                # Safely normalize recommendations
                normalized_recs = []
                if isinstance(recs_raw, (list, tuple)):
                    for r in recs_raw:
                        norm_r = normalize_recommendation(r)
                        if norm_r:
                            normalized_recs.append(norm_r)
                elif recs_raw:
                    norm_r = normalize_recommendation(recs_raw)
                    if norm_r:
                        normalized_recs.append(norm_r)

                # Recommendations Matrix
                if normalized_recs:
                    st.markdown("---")
                    st.subheader("🎯 Prioritized Action Recommendations (Impact × Effort)")
                    rec_rows = []
                    for r in normalized_recs:
                        rec_rows.append({
                            "Action Title": r.get("title", "Recommended Action"),
                            "Strategic Rationale": r.get("problem", "Operational improvement"),
                            "Proposed Intervention": r.get("proposed_action", ""),
                            "Impact": r.get("impact", "Medium"),
                            "Effort": r.get("effort", "Medium"),
                            "Owner": r.get("owner", "Operations Lead"),
                            "Target Milestone": r.get("timescale", "30-60 days")
                        })
                    st.dataframe(pd.DataFrame(rec_rows), use_container_width=True)

                # Export Hub
                st.markdown("---")
                st.subheader("📥 Executive Export & Reporting Hub")
                st.markdown("Generate presentation-ready deliverables containing evidence tables, methodology disclaimers, and audit provenance.")

                c_ex1, c_ex2, c_ex3 = st.columns(3)
                with c_ex1:
                    # Excel Evidence Pack
                    excel_bytes = build_excel_evidence_pack(
                        clean_df=df,
                        kpi_definitions=[],
                        quality_issues=analysis_res.get("qa_report", {}).get("issues", []),
                        evidence_insights=findings_raw if isinstance(findings_raw, list) else [],
                        recommendation_items=recs_raw if isinstance(recs_raw, list) else [],
                        action_items=[],
                        audit_log_entries=st.session_state.get("audit_trail", []),
                        project_state=st.session_state.get("project_state", {})
                    )
                    st.download_button(
                        label="📊 Download Excel Evidence Pack (.xlsx)",
                        data=excel_bytes,
                        file_name=f"Performance_Evidence_Pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                with c_ex2:
                    # PowerPoint Presentation
                    pptx_bytes = build_powerpoint_presentation(
                        project_state=st.session_state.get("project_state", {}),
                        kpi_summary={"Metric": analysis_res.get("metric_col", "")},
                        trend_summary=analysis_res.get("spc_df", pd.DataFrame()),
                        comparison_summary=analysis_res.get("comparison_results", {}),
                        evidence_insights=findings_raw if isinstance(findings_raw, list) else [],
                        recommendations=recs_raw if isinstance(recs_raw, list) else []
                    )
                    st.download_button(
                        label="📽️ Download Executive Deck (.pptx)",
                        data=pptx_bytes,
                        file_name=f"Performance_Executive_Brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )

                with c_ex3:
                    # Executive PDF Summary
                    pdf_bytes = build_executive_pdf(
                        project_state=st.session_state.get("project_state", {}),
                        kpi_summary={"Metric": analysis_res.get("metric_col", "")},
                        quality_score=analysis_res.get("health_score", 100.0),
                        insights=findings_raw if isinstance(findings_raw, list) else [],
                        recommendations=recs_raw if isinstance(recs_raw, list) else []
                    )
                    st.download_button(
                        label="📄 Download Executive PDF Brief (.pdf)",
                        data=pdf_bytes,
                        file_name=f"Performance_Executive_Brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        except Exception as e:
            st.error(f"An error occurred while displaying findings or export options: {e}")
