"""Page 11: Enterprise Reporting, Multi-Format Exports & Scenario Simulator.
Generates publication-grade, validated deliverables:
- Executive Summary Markdown Memo
- Multi-Tab Sanitized Excel Evidence Pack (Formula-Injection Protected)
- PowerPoint Presentation Deck (16:9 Widescreen)
- ReportLab PDF Executive Briefing
- Interactive Operational What-If Scenario Simulator
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path for Streamlit Cloud deployment
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime

from core.constants import WorkflowStage
from core.state import init_session_state, get_working_df, advance_workflow_stage, log_audit_event
from modules.reporting.export_builder import (
    build_canonical_reporting_payload,
    build_markdown_executive_report,
    generate_excel_evidence_pack,
    build_powerpoint_presentation,
    build_executive_pdf,
    validate_excel_bytes,
    validate_pptx_bytes,
    validate_pdf_bytes
)
from modules.forecasting.simulator import run_scenario_simulation

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

# Build unified canonical payload from active analysis state
canonical_payload = build_canonical_reporting_payload(
    state_or_df=df,
    project_state=proj_state,
    kpi_results=kpi_results,
    insights_list=insights,
    recommendations_list=recommendations,
    action_registry=actions,
    qa_report=qa_report
)

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

if df is None or len(df) == 0:
    st.info("ℹ️ No active dataset is currently loaded. Please upload or load data in Stages 1 & 2 to generate verified evidence deliverables.")
else:
    col_e1, col_e2, col_e3 = st.columns(3)

    # 1. Excel Evidence Pack (Sanitized)
    with col_e1:
        st.markdown("##### 📗 Excel Evidence Pack")
        st.caption("Multi-tab workbook with KPI scorecards, insights, action registry, and sanitized data extract.")
        try:
            excel_bytes = generate_excel_evidence_pack(payload=canonical_payload)
            if validate_excel_bytes(excel_bytes):
                st.download_button(
                    "⬇️ Download Excel Evidence Pack (.xlsx)",
                    data=excel_bytes,
                    file_name=f"Performance_Evidence_Pack_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Excel generation did not produce a verified OpenXML workbook.")
        except Exception as e:
            st.error(f"Excel export error: {e}")

    # 2. PowerPoint Presentation Deck
    with col_e2:
        st.markdown("##### 📙 PowerPoint Deck (16:9)")
        st.caption("Executive slide presentation with scorecard, diagnostic findings, and prioritized actions.")
        try:
            pptx_bytes = build_powerpoint_presentation(payload=canonical_payload)
            if validate_pptx_bytes(pptx_bytes):
                st.download_button(
                    "⬇️ Download PowerPoint Deck (.pptx)",
                    data=pptx_bytes,
                    file_name=f"Performance_Presentation_{datetime.now().strftime('%Y%m%d')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ PowerPoint generation did not produce a verified presentation deck.")
        except Exception as e:
            st.error(f"PowerPoint export error: {e}")

    # 3. PDF Briefing Report
    with col_e3:
        st.markdown("##### 📕 PDF Briefing Report")
        st.caption("Publication-ready executive PDF memo formatted for board governance.")
        try:
            pdf_bytes = build_executive_pdf(payload=canonical_payload)
            if validate_pdf_bytes(pdf_bytes):
                st.download_button(
                    "⬇️ Download PDF Briefing (.pdf)",
                    data=pdf_bytes,
                    file_name=f"Performance_Executive_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ PDF generation did not produce a verified document.")
        except Exception as e:
            st.error(f"PDF export error: {e}")

st.markdown("---")

# -------------------------------------------------------------
# 3. EXECUTIVE SUMMARY MEMORANDUM PREVIEW
# -------------------------------------------------------------
st.subheader("📑 Executive Summary Memo Preview")
exec_report_md = build_markdown_executive_report(payload=canonical_payload)

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
