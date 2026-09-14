import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.insights import generate_rule_based_insights

init_session_state()

st.title("💡 08. Diagnostic Insights & Hypothesis Engine")
st.markdown("""
Review auto-generated analytical findings.
- **Review Workflow:** Mark each finding as **Accept**, **Edit**, or **Reject**.
- Only **Approved** insights feed downstream recommendations, the **Interview View**, and export decks.
""")

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
granularity = st.session_state.get("row_granularity", "Case / record")

if df is None or not mappings:
    st.warning("⚠️ **Workflow Gate:** Please upload data and confirm column mappings on Page 03 first.")
    st.stop()

# Generate raw insights if empty
if not st.session_state.get("insights_list"):
    st.session_state["insights_list"] = generate_rule_based_insights(df, mappings, target_dirs, granularity)

insights = st.session_state.get("insights_list", [])

if not insights:
    st.info("No rule-based anomalies detected based on current mappings.")
else:
    st.subheader(f"🔍 Diagnostic Findings ({len(insights)} Generated)")
    
    for i, item in enumerate(insights):
        with st.container():
            st.markdown(f"### Finding #{i+1}: {item.get('title', 'Insight')}")
            
            c_badge1, c_badge2, c_badge3 = st.columns([1, 1, 2])
            c_badge1.caption(f"**Severity:** `{item.get('severity', 'medium').upper()}`")
            c_badge2.caption(f"**Category:** `{item.get('category', 'general')}`")
            status = item.get('status', 'pending')
            status_color = "green" if status == "approved" else ("red" if status == "rejected" else "orange")
            c_badge3.markdown(f"**Status:** :{status_color}[{status.upper()}]")
            
            # Editable finding text
            current_text = item.get('finding', '')
            edited_finding = st.text_area(f"Finding Description (Editable)", value=current_text, key=f"insight_edit_{i}", height=70)
            item['finding'] = edited_finding
            
            # Action buttons
            b1, b2, b3 = st.columns([1, 1, 4])
            with b1:
                if st.button("✅ Accept", key=f"acc_ins_{i}", use_container_width=True):
                    item['status'] = "approved"
                    st.session_state.audit_logger.log("INSIGHT_APPROVED", f"Approved insight {item.get('id')}", details={"id": item.get("id"), "title": item.get("title")})
                    st.rerun()
            with b2:
                if st.button("❌ Reject", key=f"rej_ins_{i}", use_container_width=True):
                    item['status'] = "rejected"
                    st.session_state.audit_logger.log("INSIGHT_REJECTED", f"Rejected insight {item.get('id')}", details={"id": item.get("id"), "title": item.get("title")})
                    st.rerun()
            with b3:
                if st.button("✏️ Save Edits & Approve", key=f"save_ins_{i}"):
                    item['status'] = "approved"
                    st.session_state.audit_logger.log("INSIGHT_EDITED", f"Edited and approved insight {item.get('id')}", details={"id": item.get("id"), "text": edited_finding})
                    st.success("Saved and approved!")
                    st.rerun()
            
            st.markdown("---")

approved_count = len([x for x in insights if x.get('status') == 'approved'])
st.info(f"📊 **Approved Findings:** {approved_count} of {len(insights)} approved for presentation export.")
