import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.insights import generate_rule_based_insights

init_session_state()

st.title("💡 08. Diagnostic Insights & Hypothesis Engine")
st.markdown("""
Review auto-generated analytical findings.
- **Review Workflow:** Mark each finding as **Accept**, **Edit**, or **Reject**.
- Only **Approved** insights will feed into the **Interview View** and export decks.
""")

df = st.session_state.get("clean_df")
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
granularity = st.session_state.get("row_granularity", "Case / record")

if df is None or not mappings:
    st.warning("⚠️ Please upload data and confirm column mappings first.")
    st.stop()

# Generate raw insights if empty
if not st.session_state.get("insights_list"):
    st.session_state["insights_list"] = generate_rule_based_insights(df, mappings, target_dirs, granularity)

insights = st.session_state.get("insights_list", [])

if not insights:
    st.info("No rule-based anomalies or target deviations detected based on current mappings.")
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
                    st.session_state.audit_logger.log("ACCEPT_INSIGHT", f"Accepted insight {item.get('id')}", details={"id": item.get("id"), "title": item.get("title")})
                    st.rerun()
            with b2:
                if st.button("❌ Reject", key=f"rej_ins_{i}", use_container_width=True):
                    item['status'] = "rejected"
                    st.session_state.audit_logger.log("REJECT_INSIGHT", f"Rejected insight {item.get('id')}", details={"id": item.get("id"), "title": item.get("title")})
                    st.rerun()
            with b3:
                if st.button("✏️ Save Edits & Approve", key=f"save_ins_{i}"):
                    item['status'] = "approved"
                    st.session_state.audit_logger.log("EDIT_APPROVE_INSIGHT", f"Edited insight {item.get('id')}", details={"id": item.get("id"), "text": edited_finding})
                    st.success("Saved and approved!")
                    st.rerun()
            
            st.markdown("---")

# Summary of approved insights
approved_count = len([x for x in insights if x.get('status') == 'approved'])
st.info(f"📊 **Approved Findings:** {approved_count} of {len(insights)} ready for presentation export.")
