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

## ⏱️ 2. Rapid 10-Minute Assessment Workflow

| Phase | Page | Key Actions | Time |
|---|---|---|---|
| **0. Intake** | `app.py` (Home) | Paste problem statement, mandatory SLA targets, audience, and required comparisons. | 1 min |
| **1. Ingest & Unit** | `01_Upload` | Ingest `.csv` / `.xlsx` / `.xls`. **Confirm Row Granularity** (e.g., 1 row = 1 case vs 1 month aggregate). | 1 min |
| **2. QA & Fitness** | `02_Quality` | Inspect Data Health Score, null rates, zero denominators, and record data fitness caveats. | 1 min |
| **3. Mappings** | `03_Mapping` | Confirm semantic roles (`volume`, `target`, `fte`, `wait_time`, `dates`). Set **Target Directionality** (higher/lower is better). | 1 min |
| **4. Diagnostic** | `04 - 07` | Inspect KPI variances, run chart trends, team/cohort comparisons, and bottleneck drivers. | 3 mins |
| **5. Governance** | `08 & 09` | Review, edit, and **Approve** evidence-based findings and actionable recommendations. | 2 mins |
| **6. Delivery** | `10 & 11` | Open **13-Section Assessment Summary** / Prompt Card Mode; download 16:9 Widescreen PowerPoint. | 1 min |

---

## 🛡️ 3. Panel Q&A Defense Playbook

### Q1: "How do you know this variance isn't just normal random noise?"
- **Defense:** "I began by establishing data fitness and completeness. The observed variance is systematic across distinct operational cohorts and consistent across observation periods rather than a single anomalous outlier. Furthermore, target directionality was verified to ensure processing times and error rates were judged on reduction rather than increase."

### Q2: "What immediate actions would you take in Week 1?"
- **Defense:** "Establish a daily 15-minute operational triage standup to balance intake queues across high-variance units, implement standardized operating procedures on sub-processes with the highest error rates, and institute weekly lead-time tracking against our agreed SLA."

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
