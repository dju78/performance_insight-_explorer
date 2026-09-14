"""Page 02: Data Quality Engine & Audit Dashboard."""
import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.quality import run_quality_audit, Severity, QualityStatus

init_session_state()

st.title("🛡️ 2. Data Quality Engine")
st.caption("Multi-dimensional quality assurance scan: Completeness, Uniqueness, Validity, Consistency, Plausibility, Integrity.")

if st.session_state.raw_df is None:
    st.warning("⚠️ No dataset loaded. Please upload a file in 'Upload & Profile' first.")
else:
    # Refresh QA if needed
    if st.button("🔄 Re-run Quality Scan"):
        st.session_state.qa_report = run_quality_audit(
            st.session_state.raw_df,
            st.session_state.confirmed_mappings
        )
        st.session_state.audit_logger.log(
            "QA_AUDIT_RERUN",
            f"Executed QA scan. Health Score: {st.session_state.qa_report['health_score']}/100",
            row_count=len(st.session_state.raw_df)
        )
        st.success("Quality audit re-executed.")
        
    qa = st.session_state.qa_report
    if qa:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Data Health Score", f"{qa['health_score']:.1f} / 100")
        c2.metric("Critical Issues", f"{qa['critical_count']}", delta="Requires Review" if qa['critical_count'] > 0 else "Clean", delta_color="inverse")
        c3.metric("Warning Issues", f"{qa['warning_count']}")
        c4.metric("Information Items", f"{qa['info_count']}")
        
        st.markdown("---")
        st.subheader("📋 Detected Data Quality Issues")
        
        issues = qa.get("issues", [])
        if not issues:
            st.success("🎉 No data quality issues detected! Dataset passed all checks.")
        else:
            # Filter severity
            sev_filter = st.multiselect("Filter by Severity:", [Severity.CRITICAL, Severity.WARNING, Severity.INFO], default=[Severity.CRITICAL, Severity.WARNING])
            filtered_issues = [i for i in issues if i["severity"] in sev_filter]
            
            for iss in filtered_issues:
                sev = iss["severity"]
                if sev == Severity.CRITICAL:
                    badge = "🔴 **CRITICAL**"
                elif sev == Severity.WARNING:
                    badge = "🟡 **WARNING**"
                else:
                    badge = "🔵 **INFO**"
                    
                with st.expander(f"{badge} | [{iss['issue_id']}] {iss['title']} (Field: {iss['field']})", expanded=(sev == Severity.CRITICAL)):
                    st.markdown(f"**Dimension:** {iss['dimension']} | **Affected Records:** {iss['affected_count']:,} ({iss['affected_pct']}%)")
                    st.markdown(f"**Description:** {iss['description']}")
                    st.markdown(f"**Recommended Analyst Action:** {iss['recommended_action']}")
                    
                    if iss.get("sample_values"):
                        st.markdown(f"**Sample Affected Values:** `{', '.join([str(v) for v in iss['sample_values'][:5]])}`")
                        
                    if iss.get("sample_indices") and len(iss["sample_indices"]) > 0:
                        st.markdown("**Sample Affected Rows in Dataset:**")
                        st.dataframe(st.session_state.raw_df.loc[iss["sample_indices"]], use_container_width=True)
                        
        st.markdown("---")
        st.markdown("### 📌 Non-Destructive Data Handling Notice")
        st.info("The Data Quality Engine flags anomalies for your awareness but **NEVER automatically deletes, mutates, or fabricates observations**. Preserving raw evidence is essential for transparent analysis.")
