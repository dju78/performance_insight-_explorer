import os
import streamlit as st
from src.state import init_session_state, reset_analysis_only, clear_dataset_for_new_upload
from src.export import (
    build_export_payload_from_state,
    generate_executive_excel_pack,
    generate_powerpoint_deck,
    generate_pdf_report,
    generate_audit_trail_text
)

init_session_state()

st.title("📦 11. Multi-Format Export & Final Deliverables")
st.markdown("Generate executive PDF briefings, PowerPoint decks, analytical Excel workbooks, and reproducible audit logs.")

df = st.session_state.get("clean_df")
if df is None:
    df = st.session_state.get("raw_df")
    
if df is None:
    st.warning("⚠️ No active dataset loaded. Please upload a dataset on Page 01 first.")
    st.stop()

# 1. Build & Inspect Verified Export Payload
payload = build_export_payload_from_state()

st.subheader("📋 Pre-Export Governance Checklist")
c_ck1, c_ck2, c_ck3, c_ck4 = st.columns(4)
c_ck1.metric("Dataset File", payload.get("filename", "N/A")[:18])
c_ck2.metric("Worksheet / Scope", payload.get("active_sheet", "Default"))
c_ck3.metric("Data Volume", f"{payload.get('row_count', 0):,} rows")
c_ck4.metric("Row Granularity", payload.get("row_granularity", "Not Confirmed"))

c_ck5, c_ck6, c_ck7, c_ck8 = st.columns(4)
qa = payload.get("qa_report", {})
c_ck5.metric("QA Health Score", f"{qa.get('health_score', 100):.1f} / 100")
c_ck6.metric("Mappings Confirmed", f"{len(payload.get('confirmed_mappings', {}))} columns")
c_ck7.metric("Approved Findings", f"{len(payload.get('approved_insights', []))}")
c_ck8.metric("Approved Actions", f"{len(payload.get('approved_recommendations', []))}")

# Check Validation Errors
if not payload["is_valid_for_export"]:
    st.error("🚫 **Export Blocked — Mandatory Prerequisites Missing:**")
    for err in payload["validation_errors"]:
        st.markdown(f"- {err}")
    st.info("Please complete the required workflow steps before generating final deliverables.")
    st.stop()
else:
    st.success("✅ **Governance Gate Passed:** All mandatory workflow steps are verified. Deliverables will contain active session findings only.")

st.markdown("---")
st.subheader("🚀 Export Deliverables")

col_e1, col_e2, col_e3, col_e4 = st.columns(4)

with col_e1:
    st.markdown("#### 📄 Executive PDF Brief")
    st.caption("A4 publication-ready briefing generated via ReportLab Platypus.")
    pdf_aud = st.selectbox(
        "PDF Report Audience:",
        ["Senior Leadership", "Operational Management", "Analyst / Technical", "General Briefing"],
        key="pdf_aud_select"
    )
    if st.button("Generate PDF Brief", type="primary", use_container_width=True):
        try:
            pdf_path = generate_pdf_report(payload, audience=pdf_aud)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=f.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success(f"PDF saved: `{os.path.basename(pdf_path)}`")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

with col_e2:
    st.markdown("#### 📊 Presentation Deck")
    st.caption("6-slide executive briefing deck with live KPI scorecard and actions.")
    if st.button("Generate PowerPoint", use_container_width=True):
        try:
            pptx_path = generate_powerpoint_deck(payload)
            with open(pptx_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Deck (.pptx)",
                    data=f.read(),
                    file_name=os.path.basename(pptx_path),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            st.success(f"PowerPoint saved: `{os.path.basename(pptx_path)}`")
        except Exception as e:
            st.error(f"Error generating PowerPoint: {e}")

with col_e3:
    st.markdown("#### 📑 Analytical Excel Pack")
    st.caption("Multi-tab workbook containing KPIs, QA audit, insights, and raw data.")
    if st.button("Generate Excel Pack", use_container_width=True):
        try:
            excel_path = generate_executive_excel_pack(payload)
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Excel (.xlsx)",
                    data=f.read(),
                    file_name=os.path.basename(excel_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            st.success(f"Excel workbook saved: `{os.path.basename(excel_path)}`")
        except Exception as e:
            st.error(f"Error generating Excel: {e}")

with col_e4:
    st.markdown("#### 🛡️ Audit & Repro Log")
    st.caption("Complete timestamped ledger of analyst actions and transformations.")
    if st.button("Generate Audit Trail", use_container_width=True):
        try:
            audit_path = generate_audit_trail_text(payload.get("audit_trail", []))
            with open(audit_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Audit Log (.txt)",
                    data=f.read(),
                    file_name=os.path.basename(audit_path),
                    mime="text/plain",
                    use_container_width=True
                )
            st.success(f"Audit log saved: `{os.path.basename(audit_path)}`")
        except Exception as e:
            st.error(f"Error generating Audit log: {e}")

st.markdown("---")
st.subheader("🧹 Session Transition & Data Management")
st.caption("Choose between clearing the active dataset to start a new analysis or resetting calculations to re-map columns.")

col_rst1, col_rst2 = st.columns(2)
with col_rst1:
    if st.button("✅ Analysis Complete — Clear Data & Start New Upload", type="primary", use_container_width=True):
        clear_dataset_for_new_upload(preserve_assessment_context=True)
        st.success("Dataset and analysis cleared cleanly. Returning to Data Upload...")
        st.switch_page("pages/01_upload_profile.py")

with col_rst2:
    if st.button("🔄 Reset Analysis Only (Keep Uploaded File)", use_container_width=True):
        reset_analysis_only()
        st.success("Analysis reset safely! Returning to Column Mapping...")
        st.switch_page("pages/03_column_mapping.py")

