"""Page 11: Enterprise Reporting, Multi-Format Exports & Scenario Simulator.
Generates publication-grade deliverables:
- Executive Summary Markdown Memo
- Multi-Tab Sanitized Excel Evidence Pack (Formula-Injection Protected)
- PowerPoint Presentation Deck
- ReportLab PDF Briefing
- Interactive Operational What-If Scenario Simulator
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from core.constants import WorkflowStage
from core.state import init_session_state, get_working_df, advance_workflow_stage, log_audit_event
from modules.reporting.export_builder import (
    build_markdown_executive_report, generate_excel_evidence_pack
)
from modules.forecasting.simulator import run_scenario_simulation
from src.powerpoint import generate_assessment_presentation
from src.pdf_report import generate_pdf_report

init_session_state()

st.title("📄 Stage 14 & 15: Reporting, Exports & Scenarios")
st.markdown("Download verified enterprise performance evidence packs and simulate operational what-if scenarios.")

df = get_working_df()
proj_state = st.session_state.get("project_state", {})
kpi_results = st.session_state.get("kpi_results", {})
insights = st.session_state.get("insights_list", [])
recommendations = st.session_state.get("recommendations_list", [])
actions = st.session_state.get("action_registry", [])
qa_report = st.session_state.get("qa_report")

# -------------------------------------------------------------
# 1. WHAT-IF SCENARIO & CAPACITY SIMULATOR
# -------------------------------------------------------------
st.subheader("🔮 Operational Scenario & Capacity Simulator")
st.caption("Model the impact of demand surges, staffing/FTE variations, and productivity gains. All outputs are explicitly flagged as estimates.")

with st.expander("⚙️ Adjust Scenario Assumptions & Parametric Multipliers", expanded=False):
    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1:
        demand_mult = st.slider("Demand Volume Multiplier", 0.70, 1.50, 1.0, 0.05, format="%.2fx")
    with c_s2:
        fte_mult = st.slider("Staffing / FTE Capacity Multiplier", 0.70, 1.50, 1.0, 0.05, format="%.2fx")
    with c_s3:
        prod_gain = st.slider("Productivity Gain % (Continuous Improvement)", -20.0, 30.0, 0.0, 5.0, format="%.1f%%")

    # Baseline calculations
    base_vol = 1000.0
    base_fte = 10.0
    base_prod = 100.0
    if df is not None:
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) > 0:
            base_vol = float(df[num_cols[0]].sum())
            base_prod = float(df[num_cols[0]].mean())

    sim_res = run_scenario_simulation(
        base_vol, base_fte, base_prod, demand_mult, fte_mult, prod_gain
    )

    st.markdown(f"ℹ️ **{sim_res['disclaimer']}**")
    
    scen_rows = []
    for sc_name, sc_data in sim_res["scenarios"].items():
        row = {"Scenario": sc_name}
        row.update(sc_data)
        scen_rows.append(row)
    st.dataframe(pd.DataFrame(scen_rows), use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# 2. MULTI-FORMAT ENTERPRISE EXPORTS
# -------------------------------------------------------------
st.subheader("📥 Export Performance Evidence Deliverables")

col_e1, col_e2, col_e3 = st.columns(3)

# 1. Excel Evidence Pack (Sanitized)
with col_e1:
    st.markdown("##### 📗 Excel Evidence Pack")
    st.caption("Multi-tab workbook with KPI scorecards, insights, action registry, and sanitized data extract.")
    try:
        excel_bytes = generate_excel_evidence_pack(
            proj_state, df, kpi_results, insights, recommendations, actions, qa_report
        )
        st.download_button(
            "⬇️ Download Excel Evidence Pack (.xlsx)",
            data=excel_bytes,
            file_name=f"Performance_Evidence_Pack_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Excel export error: {e}")

# 2. PowerPoint Presentation Deck
with col_e2:
    st.markdown("##### 📙 PowerPoint Deck (16:9)")
    st.caption("Executive slide presentation with scorecard, diagnostic findings, and prioritized actions.")
    try:
        pptx_bytes = generate_assessment_presentation(
            df=df,
            findings_data={"insights": insights, "kpis": kpi_results, "recs": recommendations},
            brief_context=st.session_state.get("assessment_brief_data", {})
        )
        st.download_button(
            "⬇️ Download PowerPoint Deck (.pptx)",
            data=pptx_bytes,
            file_name=f"Executive_Performance_Briefing_{datetime.now().strftime('%Y%m%d')}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PowerPoint export error: {e}")

# 3. PDF Briefing Report
with col_e3:
    st.markdown("##### 📕 PDF Briefing Report")
    st.caption("Publication-ready executive PDF memo formatted for board governance.")
    try:
        pdf_bytes = generate_pdf_report(
            df=df,
            findings_data={"insights": insights, "kpis": kpi_results, "recs": recommendations},
            brief_context=st.session_state.get("assessment_brief_data", {})
        )
        st.download_button(
            "⬇️ Download PDF Briefing (.pdf)",
            data=pdf_bytes,
            file_name=f"Executive_Performance_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PDF export error: {e}")

st.markdown("---")

# -------------------------------------------------------------
# 3. EXECUTIVE SUMMARY MEMORANDUM PREVIEW
# -------------------------------------------------------------
st.subheader("📑 Executive Summary Memo Preview")
exec_report_md = build_markdown_executive_report(
    proj_state, kpi_results, insights, recommendations, actions, qa_report
)

with st.expander("📄 View Full Markdown Report", expanded=True):
    st.markdown(exec_report_md)

st.download_button(
    "⬇️ Download Markdown Executive Memo (.md)",
    data=exec_report_md,
    file_name=f"Executive_Memo_{datetime.now().strftime('%Y%m%d')}.md",
    mime="text/markdown",
    use_container_width=True
)

st.markdown("---")
if st.button("Complete Governance & Export Lifecycle ✅", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_15_EXPORT)
    log_audit_event("LIFECYCLE_COMPLETED", "Full analysis lifecycle completed and exported.")
    st.success("Complete performance analysis lifecycle successfully finalized and archived in audit trail!")
