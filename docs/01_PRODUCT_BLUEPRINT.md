# Product Blueprint

## 1. Product name

**Performance Insight Explorer**

Subtitle:

**Operational Performance • Data Quality • Analysis • Insight**

## 2. Product vision

Create a reusable analytical decision-support application that can accept unfamiliar operational datasets and guide an analyst from raw data to transparent, defensible insight.

## 3. Problem

Performance analysts often receive data with little preparation time and inconsistent structures.

The analyst must rapidly answer:

- What data have I received?
- Can I trust it?
- What is happening?
- Where is performance changing?
- Which groups are different?
- What may explain the differences?
- What should happen next?
- What cannot yet be concluded?

## 4. Product objectives

The application should enable the user to:

- upload CSV, XLS or XLSX
- select a worksheet
- profile the dataset
- identify quality issues
- map unknown columns to analytical roles
- calculate supported KPIs
- analyse trends and comparisons
- inspect potential drivers
- record assumptions and limitations
- generate key findings
- generate evidence-linked recommendations
- create interview and management views
- export PowerPoint, charts, tables and audit records

## 5. Product principles

### 5.1 Reliability over complexity
The application should prefer a smaller number of correct, transparent calculations over many opaque features.

### 5.2 Transparency over automation
Every calculation should be explainable.

### 5.3 Analyst in control
The system may suggest, but the user confirms.

### 5.4 Conditional analysis
Only run a metric when its required fields are mapped and valid.

### 5.5 Preserve evidence
The raw uploaded dataset remains unchanged.

### 5.6 No false certainty
The system should use wording such as:

- may indicate
- is associated with
- appears consistent with
- requires further investigation

when the evidence does not support causation.

## 6. Primary users

- Performance Analysts
- Data Analysts
- Business Analysts
- Operational Managers
- Research Analysts

## 7. Initial use case

A timed Performance Analyst assessment where the file structure is unknown before receipt.

## 8. Core workflow

**Purpose → Upload → Profile → QA → Map → Analyse → Interpret → Recommend → Review → Export**

## 9. In scope

- local file upload
- profiling
- quality assessment
- flexible mapping
- KPI calculations
- trend analysis
- segment comparison
- backlog analysis
- productivity
- utilisation
- target performance
- processing time analysis
- outlier flagging
- root-cause exploration
- communication views
- audit trail
- PowerPoint export

## 10. Out of scope for Version 1

- automated causal inference
- machine-learning forecasting
- automatic data correction
- direct cloud publishing
- live databases
- external AI APIs
- automated decisions
- direct Power BI integration

## 11. Success definition

The product succeeds when an analyst can receive an unfamiliar operational dataset and reach a defensible, presentation-ready analysis without rewriting the application for the dataset.


