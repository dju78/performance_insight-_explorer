# Changelog - Performance Insight Explorer

All notable changes to the Performance Insight Explorer application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-14

### Added
- **Core Architecture:**
  - Built schema-flexible operational analytics engine with 15 modular components under `src/`.
  - Created 12-page Streamlit application with intuitive, professional UI.
  - Implemented session state management with persistent audit logging.
- **Data Ingestion & Profiling:**
  - Support for CSV, XLSX, XLS with automatic encoding detection (`utf-8`, `latin1`, `iso-8859-1`, etc.).
  - Excel sheet inspection and selective worksheet loading.
  - Deep dataset profiling (row count, memory footprint, data type inference, candidate dates, candidate numerics, uniqueness, sample previews).
- **Data Quality Engine (6 Dimensions):**
  - Automated scanning for Completeness (missingness), Uniqueness (duplicate rows & IDs), Validity (date parsing, negative values, zero denominators), Consistency (category casing/whitespace), Plausibility (constant columns, IQR outliers), and Integrity (Backlog reconciliation balance).
  - Severity classification: Critical, Warning, Information.
  - Non-destructive preservation policy (raw source data is never modified).
- **Flexible Role Mapping:**
  - 24 standardized analytical roles across Identity, Time, Dimensions, Performance, Capacity, and Other.
  - AI/Heuristic keyword suggestion algorithm with confidence scoring.
  - Dynamic KPI activation logic (only activates metrics supported by mapped inputs).
- **KPI Calculation Engine:**
  - Guarded mathematical formulas for Target Achievement %, Target Variance, Productivity (Completed / FTE or Staff), Utilisation %, Observed Backlog Change, Expected Closing Backlog, Backlog Reconciliation Gap, Estimated Net Flow Pressure, and Median Processing Times.
  - Safe division protection (`safe_divide`) against zero denominators.
  - Clear labelling of estimated vs observed measures.
- **Analytical & Diagnostic Modules:**
  - Trend analysis engine with period differences, percentage changes, rolling averages, peak/trough detection, and sustained direction flags.
  - Segment comparison engine with normalised rates and small-sample size warnings.
  - 5-Pillar Root Cause Workspace (Demand, Capacity, Process, Complexity, Data Quality).
  - Pearson and Spearman correlation matrices with mandatory non-causation governance notices.
  - Traceable 6-part structured insight cards (Finding, Evidence, Interpretation, Business Implication, Recommendation, Limitation).
  - Four-category recommendation matrix (Act, Investigate, Monitor, Improve Reporting).
  - Interactive Assumptions Register and Limitations Register.
  - Interview View (concise 1-page oral presentation aid).
- **Export & Reporting:**
  - 6-slide executive PowerPoint deck generator (`python-pptx`) matching exact specification.
  - Multi-tab formatted Excel summary workbook generator (`openpyxl`).
  - CSV analytical tables and CSV session audit trail export.
- **Synthetic Test Datasets:**
  - `Dataset A`: Team-Month aggregated operational data (48 rows, 12 columns).
  - `Dataset B`: Case-level operational dataset (600 rows, 12 columns).
  - `Dataset C`: Deliberately faulty operational data for rigorous QA engine testing.
- **Automation & Testing:**
  - `setup_windows.bat` and `run_windows.bat` scripts for seamless Windows execution.
  - Comprehensive Pytest test suite covering unit tests, edge cases (empty data, single row, zero denominator), and full end-to-end integration workflows.

---

### Product Owner
**DARAMOLA OMOYELE**
