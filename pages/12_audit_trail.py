"""Page 12: Audit Trail Log."""
import streamlit as st
import pandas as pd
from src.state import init_session_state

init_session_state()

st.title("📜 12. Session Audit Trail & Governance Log")
st.caption("Complete, transparent logging of data uploads, mappings, QA issues, metric executions, and export events.")

audit_df = st.session_state.audit_logger.get_dataframe()

if audit_df.empty:
    st.info("No audit events recorded in this session yet.")
else:
    st.metric("Total Logged Events", len(audit_df))
    st.dataframe(audit_df, use_container_width=True)
    
    csv_bytes = audit_df.to_csv(index=False, encoding="utf-8")
    st.download_button(
        "⬇️ Export Audit Trail as CSV",
        data=csv_bytes,
        file_name="performance_insight_audit_trail.csv",
        mime="text/csv"
    )
