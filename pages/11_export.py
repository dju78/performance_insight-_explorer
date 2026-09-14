import streamlit as st
import os
from src.state import init_session_state, reset_analysis_only
from src.export import generate_executive_excel_pack, generate_audit_trail_text
from src.powerpoint import generate_interview_powerpoint
from src.audit import log_audit_event

init_session_state()

st.title("📦 11. Multi-Format Export & Final Deliverables")
st.markdown("Export presentation decks, analytical Excel workbooks, and reproducible audit logs.")

df = st.session_state.get("clean_df")
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
granularity = st.session_state.get("row_granularity", "Case / record")
insights = st.session_state.get("insights_list", [])
recs = st.session_state.get("recommendations_list", [])

if df is None:
    st.warning("⚠️ No active dataset loaded. Please upload a dataset on Page 01 first.")
    st.stop()

st.subheader("📊 Export Options")

col_e1, col_e2, col_e3 = st.columns(3)

with col_e1:
    st.markdown("#### 📑 PowerPoint Deck (.pptx)")
    st.caption("Custom formatted 6-slide executive deck with context, scorecard, findings, and recommendations.")
    
    if st.button("Generate PowerPoint Deck", type="primary", use_container_width=True):
        try:
            pptx_path = generate_interview_powerpoint(
                df=df,
                mappings=mappings,
                target_directions=target_dirs,
                insights=insights,
                recommendations=recs,
                context={
                    "assessment_question": st.session_state.get("assessment_question", ""),
                    "target_audience": st.session_state.get("target_audience", "Senior Leadership"),
                    "output_format": st.session_state.get("output_format", "Presentation Deck"),
                    "time_available": st.session_state.get("time_available", "15 mins"),
                    "analyst_notes": st.session_state.get("analyst_notes", ""),
                    "row_granularity": granularity
                },
                author="DARAMOLA OMOYELE"
            )
            with open(pptx_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Presentation Deck",
                    data=f.read(),
                    file_name=os.path.basename(pptx_path),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            st.success(f"Deck saved to `{pptx_path}`")
        except Exception as e:
            st.error(f"Error generating PowerPoint: {e}")

with col_e2:
    st.markdown("#### 📗 Excel Executive Pack (.xlsx)")
    st.caption("Multi-tab clean workbook containing KPIs, approved insights, actions, and raw summary.")
    
    if st.button("Generate Excel Pack", use_container_width=True):
        try:
            excel_path = generate_executive_excel_pack(
                df=df,
                mappings=mappings,
                target_directions=target_dirs,
                insights=insights,
                recommendations=recs
            )
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Excel Pack",
                    data=f.read(),
                    file_name=os.path.basename(excel_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            st.success(f"Workbook saved to `{excel_path}`")
        except Exception as e:
            st.error(f"Error generating Excel: {e}")

with col_e3:
    st.markdown("#### 🛡️ Audit & Reproducibility Log")
    st.caption("Full timestamped audit trail of all mappings, transformations, and analyst actions.")
    
    if st.button("Generate Audit Report", use_container_width=True):
        try:
            audit_path = generate_audit_trail_text(st.session_state.get("audit_trail", []))
            with open(audit_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Audit Log (.txt)",
                    data=f.read(),
                    file_name=os.path.basename(audit_path),
                    mime="text/plain",
                    use_container_width=True
                )
            st.success(f"Audit log saved to `{audit_path}`")
        except Exception as e:
            st.error(f"Error generating Audit log: {e}")

st.markdown("---")
st.subheader("🧹 Safe Session Management")
st.markdown("Need to restart your analysis with a new brief or different mappings without losing the uploaded file?")

if st.button("Reset Analysis & Clear Mappings", help="Resets all derived findings while keeping raw data in memory"):
    reset_analysis_only()
    st.success("Analysis reset safely! Head back to **03. Column Mapping** to re-map.")
    st.rerun()
