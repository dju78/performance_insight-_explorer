import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.quality import run_structural_qa, run_semantic_qa, run_quality_audit, Severity, QualityStatus

init_session_state()

st.title("🛡️ 02. Two-Stage Data Quality Engine")
st.caption("Automatic Stage A (Structural QA) and Stage B (Semantic QA with confirmed mappings).")

df = st.session_state.get("clean_df")
mappings = st.session_state.get("confirmed_mappings", {})

if df is None:
    st.warning("⚠️ No dataset loaded. Please upload a file on Page 01 first.")
    st.stop()

# Ensure Stage A Structural QA is populated
if not st.session_state.get("structural_qa_report"):
    st.session_state["structural_qa_report"] = run_structural_qa(df)

# If mappings exist, ensure Stage B Semantic QA is populated
if mappings and not st.session_state.get("semantic_qa_report"):
    st.session_state["semantic_qa_report"] = run_semantic_qa(df, mappings)

if st.button("🔄 Refresh & Re-run Full Quality Scan"):
    st.session_state["structural_qa_report"] = run_structural_qa(df)
    if mappings:
        st.session_state["semantic_qa_report"] = run_semantic_qa(df, mappings)
    st.session_state["qa_report"] = run_quality_audit(df, mappings)
    st.session_state.audit_logger.log(
        "QA_AUDIT_RERUN",
        f"Re-executed quality scan. Overall Health: {st.session_state['qa_report']['health_score']}/100",
        row_count=len(df)
    )
    st.success("Quality audit re-executed successfully.")
    st.rerun()

struct_qa = st.session_state.get("structural_qa_report", {})
sem_qa = st.session_state.get("semantic_qa_report", {})

st.markdown("---")
tab_a, tab_b = st.tabs(["🏗️ Stage A: Structural QA (Immediate)", "🎯 Stage B: Semantic QA (Business Logic)"])

with tab_a:
    st.subheader("Stage A: Automatic Structural Quality Audit")
    st.caption("Scans completeness, duplicate rows, invalid dates, negative numbers, zeros, text inconsistencies, and constant columns without needing column mappings.")
    
    ca1, ca2, ca3, ca4 = st.columns(4)
    ca1.metric("Structural Health Score", f"{struct_qa.get('health_score', 100):.1f} / 100")
    ca2.metric("Critical Issues", f"{struct_qa.get('critical_count', 0)}")
    ca3.metric("Warning Issues", f"{struct_qa.get('warning_count', 0)}")
    ca4.metric("Info Items", f"{struct_qa.get('info_count', 0)}")
    
    s_issues = struct_qa.get("issues", [])
    if not s_issues:
        st.success("🎉 No structural quality issues detected! Dataset passed all Stage A checks.")
    else:
        for iss in s_issues:
            sev = iss["severity"]
            badge = "🔴 **CRITICAL**" if sev == Severity.CRITICAL else ("🟡 **WARNING**" if sev == Severity.WARNING else "🔵 **INFO**")
            with st.expander(f"{badge} | [{iss['issue_id']}] {iss['title']} (Field: {iss['field']})", expanded=(sev == Severity.CRITICAL or sev == Severity.WARNING)):
                st.markdown(f"**Dimension:** `{iss['dimension']}` | **Affected Records:** {iss['affected_count']:,} ({iss['affected_pct']}%)")
                st.markdown(f"**Description:** {iss['description']}")
                if "method_used" in iss:
                    st.markdown(f"**Method Used:** `{iss['method_used']}` | **Threshold:** `{iss.get('threshold', 'N/A')}`")
                if iss.get("sample_values"):
                    st.markdown(f"**Sample Values / Context:** `{', '.join(str(x) for x in iss['sample_values'][:5])}`")
                if iss.get("sample_indices"):
                    st.markdown(f"**Affected Row Indices:** `{iss['sample_indices'][:10]}`")
                st.markdown(f"**Recommended Action:** {iss['recommended_action']}")

with tab_b:
    st.subheader("Stage B: Semantic Business Rule QA")
    st.caption("Validates business relationships, duplicate record IDs, mapped denominator zero-risks, and backlog reconciliation gaps once column mappings are confirmed.")
    
    if not mappings:
        st.info("ℹ️ **Semantic QA Pending:** Please go to **03. Column Mapping** and confirm column mappings to activate Stage B business logic checks.")
    else:
        cb1, cb2, cb3, cb4 = st.columns(4)
        cb1.metric("Semantic Health Score", f"{sem_qa.get('health_score', 100):.1f} / 100")
        cb2.metric("Critical Semantic Issues", f"{sem_qa.get('critical_count', 0)}")
        cb3.metric("Warning Issues", f"{sem_qa.get('warning_count', 0)}")
        cb4.metric("Info Items", f"{sem_qa.get('info_count', 0)}")
        
        b_issues = sem_qa.get("issues", [])
        if not b_issues:
            st.success("✅ All semantic and business logic checks passed cleanly!")
        else:
            for iss in b_issues:
                sev = iss["severity"]
                badge = "🔴 **CRITICAL**" if sev == Severity.CRITICAL else ("🟡 **WARNING**" if sev == Severity.WARNING else "🔵 **INFO**")
                with st.expander(f"{badge} | [{iss['issue_id']}] {iss['title']} (Field: {iss['field']})", expanded=(sev == Severity.CRITICAL or sev == Severity.WARNING)):
                    st.markdown(f"**Dimension:** `{iss['dimension']}` | **Affected Records:** {iss['affected_count']:,} ({iss['affected_pct']}%)")
                    st.markdown(f"**Description:** {iss['description']}")
                    if iss.get("sample_values"):
                        st.markdown(f"**Sample Values / Context:** `{', '.join(str(x) for x in iss['sample_values'][:5])}`")
                    if iss.get("sample_indices"):
                        st.markdown(f"**Affected Row Indices:** `{iss['sample_indices'][:10]}`")
                    st.markdown(f"**Recommended Action:** {iss['recommended_action']}")
