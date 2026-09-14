import streamlit as st
import pandas as pd
from src.state import init_session_state, get_working_df
from src.metrics import calculate_kpi_summary

init_session_state()

st.title("🎤 10. Interview Defense & Executive Briefing View")
st.markdown("Standalone executive briefing screen designed for real-time presentation and assessor Q&A defense.")

# 1. Assessment Context
st.subheader("🎯 1. Assessment Brief & Objectives")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Audience", st.session_state.get("target_audience", "Senior Leadership"))
c2.metric("Output Format", st.session_state.get("output_format", "Presentation Deck"))
c3.metric("Time Available", st.session_state.get("time_available", "15 mins"))
c4.metric("Row Granularity", st.session_state.get("row_granularity", "Not Confirmed"))

q = st.session_state.get("assessment_question", "")
if q:
    st.info(f"**Assessment Question / Brief:** {q}")
    
notes = st.session_state.get("analyst_notes", "")
if notes:
    st.markdown(f"**Analyst Working Notes:** {notes}")

st.markdown("---")

# 2. Method & Governance
st.subheader("🛡️ 2. Methodology & Analytical Governance")
m_col1, m_col2, m_col3 = st.columns(3)
qa_score = st.session_state.get("qa_report", {}).get("health_score", 100.0) if st.session_state.get("qa_report") else 100.0
confirmed_count = len(st.session_state.get("confirmed_mappings", {}))

m_col1.metric("Confirmed Unit of Analysis", f"1 Row = {st.session_state.get('row_granularity', 'Not Confirmed')}")
m_col2.metric("Data Health Score", f"{qa_score:.1f} / 100")
m_col3.metric("Confirmed Mappings", f"{confirmed_count} Attributes")

st.markdown("---")

# 3. Key Performance Scorecard
df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})

if df is not None and mappings:
    kpis = calculate_kpi_summary(df, confirmed_mappings=mappings, target_directions=target_dirs)
    if kpis:
        st.subheader("📊 3. Operational Performance Scorecard")
        kpi_cols = st.columns(min(len(kpis), 4))
        for i, (k, v) in enumerate(kpis.items()):
            with kpi_cols[i % min(len(kpis), 4)]:
                val = v.get('actual')
                val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
                unit = v.get('unit', '')
                if unit:
                    val_str = f"{val_str} {unit}"
                delta_str = f"{v['variance_pct']:+.1f}% vs Target" if v.get('variance_pct') is not None else None
                st.metric(
                    label=v['display_name'],
                    value=val_str,
                    delta=delta_str,
                    delta_color="normal" if v.get('is_favorable') else ("inverse" if v.get('is_favorable') is False else "off")
                )

st.markdown("---")

# 4. Approved Findings Only
st.subheader("💡 4. Analyst-Approved Diagnostic Findings")
insights = st.session_state.get("insights_list", [])
approved_insights = [x for x in insights if x.get("status") == "approved"]

if approved_insights:
    for item in approved_insights:
        with st.chat_message("assistant"):
            st.markdown(f"**{item.get('title')}** (`{item.get('severity', 'info').upper()}`)")
            st.markdown(item.get('finding', ''))
            if item.get('evidence'):
                st.caption(f"**Evidence:** {item.get('evidence')}")
else:
    st.info("No diagnostic findings currently approved. Review findings on Page 08.")

st.markdown("---")

# 5. Approved Recommendations Only
st.subheader("🛠️ 5. Approved Operational Action Plan")
recs = st.session_state.get("recommendations_list", [])
approved_recs = [x for x in recs if x.get("status") == "approved"]

if approved_recs:
    for rec in approved_recs:
        with st.expander(f"📌 {rec.get('title')} (Owner: {rec.get('owner')} | {rec.get('timeframe')})", expanded=True):
            st.markdown(f"**Action Steps:** {rec.get('action')}")
            if rec.get("expected_impact"):
                st.markdown(f"**Expected Impact:** {rec.get('expected_impact')}")
else:
    st.info("No recommendations currently approved. Review recommendations on Page 09.")

# 6. Limitations Register
st.markdown("---")
st.subheader("⚠️ 6. Documented Limitations & Assumptions")
lims = st.session_state.get("limitations_register")
if lims and hasattr(lims, "get_dataframe"):
    st.dataframe(lims.get_dataframe(), use_container_width=True)

# 7. Assessor Q&A Defense Script
st.markdown("---")
st.subheader("🛡️ 7. Assessor Q&A Defense Playbook")
with st.expander("Q1: 'How do you know this variance isn't just random noise?'"):
    st.markdown("""
    **Model Answer:**
    - I analyzed distribution trends and cohort segmentation to ensure variance was systematic rather than an isolated outlier.
    - Sample sizes and completeness rates were verified during data profiling.
    - We verified target directionality so metrics like processing time and error rates are evaluated on reduction rather than increase.
    """)

with st.expander("Q2: 'What immediate interventions would you implement in Week 1?'"):
    st.markdown("""
    **Model Answer:**
    - Establish a daily 15-minute operational triage standup to balance queues across bottleneck stages.
    - Implement standard operating procedures (SOPs) on highest-error sub-processes.
    - Implement real-time lead time tracking against defined SLAs.
    """)

with st.expander("Q3: 'What data limitations did you identify in this dataset?'"):
    st.markdown(f"""
    **Model Answer:**
    - Confirmed row granularity represents `{st.session_state.get('row_granularity', 'records')}`.
    - Verified missing value rates and excluded unconfirmed column mappings to prevent artificial causation.
    - Target benchmarks were validated against historical baseline averages.
    """)
