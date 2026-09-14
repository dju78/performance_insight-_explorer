import streamlit as st
import pandas as pd
from datetime import datetime
from src.state import init_session_state, get_working_df
from src.metrics import calculate_kpi_summary, calculate_utilisation
from src.quality import evaluate_data_fitness
from src.comparisons import compare_groups
from src.trends import calculate_trend_summary

init_session_state()

st.title("🎤 10. Assessment Summary & Defense View")
st.caption("BSR Performance Analyst HEO Assessment View | Candidate: **DARAMOLA OMOYELE**")

# View Mode Switcher
view_mode = st.radio(
    "Select Display Mode:",
    ["📑 Full 13-Section Assessment Summary", "📇 Prompt Card Mode (Live Speaking Cues)", "📋 Plain-Text Assessment Memo"],
    horizontal=True
)

df = get_working_df()
mappings = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})
qa_rep = st.session_state.get("qa_report", {})
insights = st.session_state.get("insights_list", [])
approved_insights = [x for x in insights if x.get("status") == "approved"]
recs = st.session_state.get("recommendations_list", [])
approved_recs = [x for x in recs if x.get("status") == "approved"]

kpis = calculate_kpi_summary(df, confirmed_mappings=mappings, target_directions=target_dirs) if (df is not None and mappings) else {}

# Evaluate Data Fitness
fitness = evaluate_data_fitness(qa_rep, df, mappings) if df is not None else {"status": "Unknown", "reasons": [], "caveats": []}

# MODE 1: FULL 13-SECTION PRACTICAL ASSESSMENT SUMMARY
if view_mode == "📑 Full 13-Section Assessment Summary":
    st.markdown("---")
    
    # Section 1: Candidate & Assessment Metadata
    st.subheader("1. Candidate & Assessment Metadata")
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown("**Candidate / Analyst:**\nDARAMOLA OMOYELE")
    m2.markdown(f"**Date:**\n{datetime.now().strftime('%d %B %Y')}")
    m3.markdown(f"**Target Audience:**\n{st.session_state.get('target_audience') or 'Not specified'}")
    m4.markdown(f"**Role:**\nPerformance Analyst (HEO)")
    
    st.markdown("---")
    
    # Section 2: Problem Statement & Core Questions
    st.subheader("2. Problem Statement & Core Questions to Answer")
    q_main = st.session_state.get("assessment_question") or "Operational performance evaluation as defined in assessment brief."
    st.info(f"**Primary Problem Statement:**\n{q_main}")
    
    q_must = st.session_state.get("questions_must_answer", "")
    if q_must:
        st.markdown("**Key Questions to Address:**")
        for line in q_must.split("\n"):
            if line.strip():
                st.markdown(f"- {line.strip()}")
                
    st.markdown("---")
    
    # Section 3: Dataset Overview & Data Fitness Assessment
    st.subheader("3. Dataset Overview & Data Fitness Assessment")
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        st.metric("Data Fitness Status", fitness.get("status", "Fit for purpose"))
        st.metric("Health Score", f"{qa_rep.get('health_score', 100.0):.1f} / 100")
    with f_col2:
        if fitness.get("reasons"):
            st.markdown("**Fitness Evaluation Justification:**")
            for r in fitness.get("reasons", []):
                st.markdown(f"- {r}")
        if fitness.get("caveats"):
            st.markdown("**Analytical Caveats & Data Hygiene Notes:**")
            for c in fitness.get("caveats", []):
                st.markdown(f"- ⚠️ {c}")
                
    st.markdown("---")
    
    # Section 4: Row Granularity & Unit of Analysis Confirmation
    st.subheader("4. Row Granularity & Unit of Analysis Confirmation")
    gran = st.session_state.get("row_granularity", "Not Confirmed")
    is_conf = st.session_state.get("row_granularity_confirmed", False)
    if is_conf:
        st.success(f"✅ **Confirmed Unit of Analysis:** 1 Row = `{gran}`. All rate calculations, variance metrics, and totals are anchored to this level.")
    else:
        st.warning("⚠️ **Unit of analysis not yet confirmed.** Go to 01_Upload & Profile to confirm row granularity.")
        
    st.markdown("---")
    
    # Section 5: Executive Performance Summary (Scorecard)
    st.subheader("5. Executive Performance Summary")
    if kpis:
        k_cols = st.columns(min(len(kpis), 4))
        for i, (k, v) in enumerate(kpis.items()):
            with k_cols[i % min(len(kpis), 4)]:
                val = v.get('actual')
                val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
                unit = v.get('unit', '')
                if unit:
                    val_str = f"{val_str} {unit}"
                delta_str = f"{v['variance_pct']:+.1f}% vs Target" if v.get('variance_pct') is not None else None
                st.metric(
                    label=v.get('display_name', k),
                    value=val_str,
                    delta=delta_str,
                    delta_color="normal" if v.get('is_favorable') else ("inverse" if v.get('is_favorable') is False else "off")
                )
                if v.get('commentary'):
                    st.caption(v['commentary'])
    else:
        st.info("No confirmed KPI mappings available. Please confirm column mappings in 03_Column Mapping.")
        
    st.markdown("---")
    
    # Section 6: Diagnostic Findings & Root-Cause Analysis
    st.subheader("6. Diagnostic Findings & Root-Cause Analysis")
    if approved_insights:
        for ins in approved_insights:
            with st.chat_message("assistant"):
                st.markdown(f"**{ins.get('title', 'Diagnostic Finding')}** (`{ins.get('severity', 'info').upper()}`)")
                st.markdown(ins.get('finding', ''))
                if ins.get('evidence'):
                    st.caption(f"📊 **Evidence Base:** {ins.get('evidence')}")
                if ins.get('implication'):
                    st.caption(f"⚡ **Operational Implication:** {ins.get('implication')}")
    else:
        st.info("No diagnostic findings have been formally approved yet. Review findings on 08_Insights.")
        
    st.markdown("---")
    
    # Section 7: Operational Comparisons & Variance Analysis
    st.subheader("7. Operational Comparisons & Variance Analysis")
    group_col = mappings.get("team") or mappings.get("category") or mappings.get("stage")
    metric_col = mappings.get("volume") or mappings.get("numerator") or mappings.get("wait_time")
    if df is not None and group_col and metric_col:
        try:
            comp_res = compare_groups(df, group_col, metric_col)
            if not comp_res.get("insufficient_data") and comp_res.get("summary_df") is not None:
                st.dataframe(comp_res["summary_df"], use_container_width=True)
                if comp_res.get("spread"):
                    st.caption(f"**Spread Analysis:** Range: {comp_res['spread'].get('range'):,.2f} | Ratio (Max/Min): {comp_res['spread'].get('ratio'):,.2f}x")
            else:
                st.info("Comparison data insufficient or group cardinality too high.")
        except Exception as e:
            st.caption(f"Cohort comparison unavailable: {e}")
    else:
        st.info("Operational group comparisons require confirmed Group and Metric column mappings.")
        
    st.markdown("---")
    
    # Section 8: Trend & Stability Analysis
    st.subheader("8. Trend & Stability Analysis")
    date_col = mappings.get("date") or mappings.get("period")
    if df is not None and date_col and metric_col:
        try:
            t_res = calculate_trend_summary(df, date_col, metric_col)
            st.markdown(f"**Overall Direction:** `{t_res.get('direction', 'Stable').upper()}` | **Net Change:** {t_res.get('pct_change', 0.0):+.1f}%")
            if t_res.get("run_chart_signals"):
                st.markdown("**Run Chart Signals Detected:**")
                for sig in t_res.get("run_chart_signals", []):
                    st.markdown(f"- {sig}")
        except Exception as e:
            st.caption(f"Trend calculation notice: {e}")
    else:
        st.info("ℹ️ **Trend analysis not applicable:** Active dataset does not contain confirmed longitudinal date/period columns. Graceful degradation applied.")
        
    st.markdown("---")
    
    # Section 9: Capacity, Demand & Utilisation Analysis
    st.subheader("9. Capacity, Demand & Utilisation Analysis")
    fte_col = mappings.get("fte")
    vol_col = mappings.get("volume")
    if df is not None and fte_col and vol_col:
        try:
            u_res = calculate_utilisation(df, vol_col, fte_col)
            if u_res.get("available"):
                st.metric("Mean Output per FTE", f"{u_res.get('mean_ratio', 0.0):,.1f} units/FTE")
                st.caption(u_res.get("commentary", ""))
            else:
                st.info(u_res.get("reason", "Capacity data unavailable."))
        except Exception as e:
            st.caption(f"Capacity analysis notice: {e}")
    else:
        st.info("ℹ️ **Capacity analysis not applicable:** Active dataset does not contain confirmed FTE/Staffing columns. Output-per-FTE evaluation omitted.")
        
    st.markdown("---")
    
    # Section 10: Recommended Operational Interventions
    st.subheader("10. Recommended Operational Interventions")
    if approved_recs:
        for r in approved_recs:
            with st.expander(f"📌 {r.get('title', 'Action')} (Owner: {r.get('owner', 'Operations')} | {r.get('timeframe', 'Immediate')})", expanded=True):
                st.markdown(f"**Action Steps:** {r.get('action', '')}")
                if r.get("expected_impact"):
                    st.markdown(f"**Expected Impact:** {r.get('expected_impact')}")
                if r.get("risk"):
                    st.caption(f"⚠️ **Implementation Risk & Mitigation:** {r.get('risk')}")
    else:
        st.info("No recommendations have been formally approved yet. Formulate and approve actions on 09_Recommendations.")
        
    st.markdown("---")
    
    # Section 11: Implementation Roadmap & Risks
    st.subheader("11. Implementation Roadmap & Risks")
    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown("##### 🚀 Horizon 1: Immediate (Days 1–30)")
        st.markdown("- Operational triage & daily bottleneck standups\n- Rebalancing intake queues across high-variance units\n- Immediate SOP standardization")
    with i2:
        st.markdown("##### ⚙️ Horizon 2: Medium-Term (Days 30–90)")
        st.markdown("- Capacity reallocation based on verified throughput rates\n- Workflow automation on high-volume sub-processes\n- Mid-point progress review")
    with i3:
        st.markdown("##### 📈 Horizon 3: Long-Term (90+ Days)")
        st.markdown("- Systematic process redesign & target recalibration\n- Predictive workload forecasting\n- Continuous quality audits")
        
    st.markdown("---")
    
    # Section 12: Data Limitations & Further Information Needed
    st.subheader("12. Data Limitations & Further Information Needed")
    st.markdown("""
    - **Confirmed Unit of Analysis:** Interpretations reflect the confirmed row granularity.
    - **Missing Variables:** Analysis is strictly bounded to available columns in the active dataset without fabricating unobserved causal variables.
    - **Recommended Follow-up Data:** Case complexity scores, sub-stage cycle timestamps, and caseworker leave data to enrich future capacity modeling.
    """)
    
    st.markdown("---")
    
    # Section 13: Assessor Q&A Defense Playbook
    st.subheader("13. Assessor Q&A Defense Playbook")
    with st.expander("🛡️ Q1: 'How do you know this variance isn't just random noise?'"):
        st.markdown("""
        **Candidate Response:**
        - I would first determine whether the apparent difference is persistent across periods or groups, assess sample size and variation, and avoid describing it as meaningful beyond the evidence available.
        - I verified data quality and completeness before running cohort comparisons.
        - Target directionality was explicitly verified so that measures requiring reduction are distinguished from those requiring growth.
        """)
    with st.expander("🛡️ Q2: 'What immediate interventions would you implement in initial stages?'"):
        st.markdown("""
        **Candidate Response:**
        - Focus initial actions on low-risk, high-clarity operational adjustments with clear ownership and measurable check-in milestones.
        - Establish operational monitoring and short-interval triage to address bottlenecks identified in the evidence.
        - Review standard processes for high-variance areas and confirm underlying data capture accuracy.
        """)
    with st.expander("🛡️ Q3: 'What data limitations did you identify in this dataset?'"):
        st.markdown(f"""
        **Candidate Response:**
        - Confirmed unit of analysis is `{gran}`.
        - Identified data completeness, null rates, and any recorded caveats during initial quality profiling.
        - Bounded conclusions strictly to verified observations, avoiding unevidenced assumptions about unrecorded causal factors.
        """)

# MODE 2: PROMPT CARD MODE
elif view_mode == "📇 Prompt Card Mode (Live Speaking Cues)":
    st.markdown("### 📇 Executive Speaking Prompt Cards")
    st.caption("Quick-reference cards designed for live delivery during assessment presentations.")
    
    c1, c2 = st.columns(2)
    with c1:
        with st.container():
            st.markdown("#### 1️⃣ The Problem & Context")
            st.markdown(f"**Core Question:** {st.session_state.get('assessment_question', 'Operational diagnostic.')}")
            st.markdown(f"**Unit of Analysis:** 1 Row = `{st.session_state.get('row_granularity', 'Records')}`")
            st.markdown(f"**Data Health:** {qa_rep.get('health_score', 100.0):.1f}/100 ({fitness.get('status', 'Fit for purpose')})")
            
        with st.container():
            st.markdown("#### 2️⃣ Diagnostic Findings")
            if approved_insights:
                for ins in approved_insights[:3]:
                    st.markdown(f"- **{ins.get('title')}:** {ins.get('finding')}")
            else:
                st.markdown("- *Review and approve findings on Page 08.*")
                
    with c2:
        with st.container():
            st.markdown("#### 3️⃣ Scorecard Highlights")
            if kpis:
                for k, v in list(kpis.items())[:4]:
                    val = v.get('actual')
                    val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
                    var_str = f" ({v['variance_pct']:+.1f}% vs Target)" if v.get('variance_pct') is not None else ""
                    st.markdown(f"- **{v.get('display_name', k)}:** {val_str}{var_str}")
            else:
                st.markdown("- *No KPIs confirmed yet.*")
                
        with st.container():
            st.markdown("#### 4️⃣ Priority Actions")
            if approved_recs:
                for r in approved_recs[:3]:
                    st.markdown(f"- **{r.get('title')}** ({r.get('owner')} | {r.get('timeframe')}): {r.get('action')}")
            else:
                st.markdown("- *Review and approve recommendations on Page 09.*")

# MODE 3: PLAIN-TEXT ASSESSMENT MEMO
elif view_mode == "📋 Plain-Text Assessment Memo":
    st.markdown("### 📋 Plain-Text Assessment Memo")
    st.caption("Clean formatted plain-text memo ready to copy into assessment portals or text editors.")
    
    memo_lines = [
        "=" * 70,
        "PRACTICAL ASSESSMENT BRIEFING MEMO",
        "=" * 70,
        f"CANDIDATE: DARAMOLA OMOYELE",
        f"DATE: {datetime.now().strftime('%d %B %Y')}",
        f"TARGET AUDIENCE: {st.session_state.get('target_audience') or 'Not specified'}",
        f"ROLE: Performance Analyst (HEO)",
        "-" * 70,
        "1. PROBLEM STATEMENT & OBJECTIVES",
        st.session_state.get('assessment_question', 'Operational diagnostic and performance analysis.'),
        "",
        "2. DATASET GOVERNANCE & FITNESS",
        f"- Active Dataset: {st.session_state.get('dataset_name', 'Operational Dataset')}",
        f"- Confirmed Unit of Analysis: 1 Row = {st.session_state.get('row_granularity', 'Not Confirmed')}",
        f"- Data Health Score: {qa_rep.get('health_score', 100.0):.1f} / 100",
        f"- Data Fitness Status: {fitness.get('status', 'Fit for purpose')}",
        "",
        "3. EXECUTIVE PERFORMANCE SCORECARD",
    ]
    
    if kpis:
        for k, v in kpis.items():
            val = v.get('actual')
            val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            delta = f" (Variance: {v['variance_pct']:+.1f}% vs Target)" if v.get('variance_pct') is not None else ""
            memo_lines.append(f"- {v.get('display_name', k)}: {val_str}{delta}")
    else:
        memo_lines.append("- No confirmed KPI metrics available.")
        
    memo_lines.extend([
        "",
        "4. ANALYST-APPROVED DIAGNOSTIC FINDINGS",
    ])
    
    if approved_insights:
        for ins in approved_insights:
            memo_lines.append(f"- [{ins.get('severity', 'INFO').upper()}] {ins.get('title')}: {ins.get('finding')}")
            if ins.get('evidence'):
                memo_lines.append(f"  Evidence: {ins.get('evidence')}")
    else:
        memo_lines.append("- No findings formally approved yet.")
        
    memo_lines.extend([
        "",
        "5. RECOMMENDED OPERATIONAL INTERVENTIONS",
    ])
    
    if approved_recs:
        for r in approved_recs:
            memo_lines.append(f"- {r.get('title')} (Owner: {r.get('owner')} | {r.get('timeframe')})")
            memo_lines.append(f"  Action: {r.get('action')}")
            if r.get('expected_impact'):
                memo_lines.append(f"  Impact: {r.get('expected_impact')}")
    else:
        memo_lines.append("- No recommendations formally approved yet.")
        
    memo_lines.extend([
        "",
        "6. LIMITATIONS & FURTHER INFORMATION",
        "- Findings strictly bounded to confirmed observations in the active dataset.",
        "- Further granularity (case-level cycle times) recommended for advanced modeling.",
        "=" * 70,
    ])
    
    full_memo = "\n".join(memo_lines)
    st.text_area("Plain-Text Assessment Memo", value=full_memo, height=450)
