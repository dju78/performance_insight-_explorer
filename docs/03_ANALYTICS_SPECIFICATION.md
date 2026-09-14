# Analytics Specification

## 1. General rule

Every metric must document:

- definition
- formula
- required fields
- denominator
- interpretation
- limitations

## 2. Descriptive statistics

For numeric variables support:

- count
- non-missing count
- sum
- mean
- median
- standard deviation
- minimum
- maximum
- quartiles

For categorical variables support:

- count
- unique count
- frequency
- percentage distribution

## 3. Target achievement

Required:
- Actual
- Target

Formula:

`Target Achievement % = Actual / Target * 100`

Rules:

- If target = 0, do not calculate.
- If target is missing, mark metric unavailable.
- Never automatically interpret >100% as positive because some targets represent maximum thresholds.

## 4. Target variance

`Variance = Actual - Target`

`Variance % = (Actual - Target) / Target * 100`

Apply the same zero-denominator protection.

## 5. Productivity

Preferred formula:

`Productivity = Cases Completed / Available FTE`

Alternative denominators may be:

- headcount
- staff hours
- productive hours

The denominator label must be visible.

Limitation:
Productivity may be affected by case complexity, experience, process design and data completeness.

## 6. Utilisation

`Utilisation % = Hours Used / Hours Available * 100`

High utilisation must not automatically be described as good performance.

## 7. Backlog

Observed change:

`Closing Backlog - Opening Backlog`

Expected close:

`Opening Backlog + Received - Closed`

Reconciliation difference:

`Reported Closing Backlog - Expected Closing Backlog`

A non-zero difference should trigger review.

## 8. Net flow

Where backlog fields are absent:

`Net Flow = Received - Completed`

Label:
**Estimated pressure on workload / flow balance**

Do not label as actual backlog change.

## 9. Completion rate

Where received and completed are measured on a compatible cohort or period:

`Completion Rate = Completed / Received * 100`

The system must warn where period flows do not represent the same cohort.

## 10. Processing time

Show:

- mean
- median
- 25th percentile
- 75th percentile
- 90th percentile where sample size permits
- distribution
- trend
- group comparison

Prefer median when strongly skewed.

## 11. Trend analysis

Where date is available:

- aggregate to appropriate period
- sort chronologically
- calculate absolute and percentage period change
- identify largest increase/decrease
- distinguish single-period movement from repeated direction

## 12. Comparison

For group comparison:

- show raw values
- show rate/normalised value where a valid denominator exists
- show sample size

Avoid ranking tiny groups without warning.

## 13. Outliers

Default approach may include IQR or robust z-score.

Outlier status means:
**review required**

It does not mean:
**delete**

## 14. Correlation

Use Pearson only where approximately linear and numeric conditions are reasonable.

Provide Spearman as an alternative for monotonic/non-normal relationships.

Display:

`Association does not demonstrate causation.`

## 15. Statistical testing

Version 1 may optionally support:

- t-test
- Mann–Whitney
- chi-square
- ANOVA

Only expose tests where assumptions and the business question justify them.

Do not run tests merely because numeric fields exist.

## 16. Root-cause exploration

Root-cause categories:

### Demand
- incoming volume
- case mix
- seasonality
- growth rate

### Capacity
- FTE
- staff hours
- utilisation
- absences if available

### Process
- processing time
- stages
- rework
- queue accumulation

### Complexity
- case type
- risk category
- complexity indicator

### Data quality
- missingness
- inconsistent definitions
- reporting changes
- duplicates

## 17. Insight rule

An insight must be supported by a reproducible calculation or clearly labelled qualitative interpretation.

Structure:

**Finding → Evidence → Interpretation → Implication → Recommendation → Limitation**

## 18. Recommendation rule

Recommendations should be one of:

- Act
- Investigate
- Monitor
- Improve reporting

The application must not invent interventions unsupported by evidence.


