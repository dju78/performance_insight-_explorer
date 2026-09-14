# 🎯 BSR PERFORMANCE ANALYST (HEO) PRACTICAL ASSESSMENT CARD
**Candidate / Author:** DARAMOLA OMOYELE  
**Role:** Performance Analyst (HEO)  
**System:** Performance Insight Explorer  

---

## 🏛️ 1. Core Operating Principles
1. **The Assessment Pack Determines the Question:** Always start by reading the brief carefully. What specific operational problem are you asked to diagnose?
2. **The Dataset Supplies the Evidence:** Rely strictly on verified data observations. Never invent unobserved variables or speculate without data backing.
3. **The Application Supports the Analysis:** Use Performance Insight Explorer for rapid aggregation, variance calculations, data hygiene profiling, and deck creation.
4. **The Analyst Makes the Judgement:** Accept, edit, or reject insights and recommendations. Your professional discernment is what the panel is assessing.

---

## ⏱️ 2. Rapid Practical Assessment Workflow

```
READ BRIEF 
  → CONFIRM REQUIREMENT 
  → UPLOAD 
  → GRANULARITY 
  → QA 
  → MAP 
  → SELECT ANALYSIS 
  → ANALYSE 
  → FINDINGS 
  → LIMITATIONS 
  → RECOMMENDATIONS 
  → DEFEND
```

*(Note: Total available time and per-stage pacing are determined entirely by the assessment pack instructions.)*

| Phase | Page / Step | Key Analytical Actions |
|---|---|---|
| **0. Rules & Intake** | `app.py` (Home) | Review assessment rules gate. Enter problem statement, audience, mandatory targets, and output format. |
| **1. Ingest & Unit** | `01_Upload` | Ingest `.csv` / `.xlsx` / `.xls`. **Confirm Row Granularity** (e.g., 1 row = 1 case vs 1 periodic aggregate). |
| **2. QA & Fitness** | `02_Quality` | Inspect Data Health Score, null rates, zero denominators, and record data fitness caveats. |
| **3. Mappings** | `03_Mapping` | Confirm semantic roles (`volume`, `target`, `fte`, `wait_time`, `dates`). Set **Target Directionality** (higher/lower is better). |
| **4. Diagnostic** | `04 - 07` | Inspect KPI variances, run chart trends (if longitudinal), cohort comparisons, and driver breakdowns. |
| **5. Governance** | `08 & 09` | Review, edit, and **Approve** evidence-based findings and actionable recommendations. |
| **6. Delivery & Defense** | `10 & 11` | Open **Assessment Summary** / Prompt Card Mode; download requested export (PowerPoint, PDF, Excel, Memo). |

---

## 🛡️ 3. Panel Q&A Defense Playbook

### Q1: "How do you know this variance isn't just normal random noise?"
- **Defense:** "I would first determine whether the apparent difference is persistent across periods or groups, assess sample size and variation, and avoid describing it as meaningful beyond the evidence available. Target directionality was explicitly verified so that measures requiring reduction are distinguished from those requiring growth."

### Q2: "What immediate interventions would you implement in initial stages?"
- **Defense:** "Focus initial actions on low-risk, high-clarity operational adjustments with clear ownership and measurable check-in milestones, establish operational monitoring on bottlenecks identified in the evidence, and review standard processes for high-variance areas."

### Q3: "What are the limitations of this dataset?"
- **Defense:** "Our unit of analysis is confirmed at [State Confirmed Granularity]. The analysis is strictly bounded to available columns in the dataset. While we have robust evidence for throughput and queue variance, further case-level complexity scoring and sub-stage timestamps would enrich future root-cause modeling."

---

## 💻 4. Local Execution & Offline Launch
If internet or cloud access is restricted during the assessment:
1. Double-click `run_windows.bat` in the project root folder.
2. Alternatively, open PowerShell and run:
   ```powershell
   streamlit run app.py --server.port 8501
   ```
3. The application will launch locally at `http://localhost:8501`.
4. All analytical, PowerPoint generation, and PDF export features function 100% offline without external API dependencies.
