# Confidence scoring

Canonical copy: `shared/references/confidence-scoring.md`.

Confidence describes how strongly the evidence supports a statement. It does not describe how important the statement is or how sure the writer feels.

## 1. Levels

Assign the highest level whose every condition holds.

| Level | BIDIM value | Conditions (all must hold) |
|---|---|---|
| Very high | 5 | Deterministic CALC on data that passed readiness for the fields used; corroborated by a second independent source or module; the result is stable under reasonable definition changes; adequate sample |
| High | 4 | Deterministic CALC on data that passed readiness for the fields used; the definition is agreed in the metric dictionary; adequate sample; known limitations do not change the direction of the finding |
| Medium | 3 | CALC or FACT exists, but with disclosed limitations: some exclusions, partial history, small but non-trivial sample, or a definition not yet confirmed by the client |
| Low | 2 | Single source, anecdote or interview statement only; or a small sample; or data with material quality issues; or a hypothesis with some supporting signal but no test |
| Insufficient | 1 | No usable evidence, data unavailable, or the evidence contradicts itself. State "cannot conclude" |

## 2. Automatic caps

These caps apply whatever the other conditions:

| Condition | Maximum level |
|---|---|
| No `CALC` or `FACT` evidence at all (only interpretation, hypothesis or interview opinion) | Low |
| Sample size under 30 units for a rate or average, unless the full population is under 30 and all of it is measured | Medium (and the sample size must be stated) |
| Fewer than 5 events in a group being compared (for example 2 churned customers) | Low for any comparison between groups |
| A required field fails readiness (see `data-readiness-assessment`) | Low |
| A join used in the calculation is rated low-confidence in the cross-module map | Low |
| The claim is causal and no experiment or quasi-experimental design was used | Low for the causal part; the correlation itself may rate higher |
| History shorter than the metric's normal period (for example NRR over fewer than 12 months) | Medium, and the period must be labelled |
| Forecast or projection | Never above Medium; always show assumptions |

## 3. Statistical discipline

- Correlation does not establish causation. Say "associated with", not "drives" or "causes".
- Do not claim statistical significance without running and recording an appropriate test (test name, statistic, p-value or interval, and assumptions checked).
- Report sample sizes next to every rate.
- Investigate outliers before removing them. Record every exclusion with its reason and its effect on the result.
- Disclose missing data: how much is missing, where, and whether it is likely to bias the result.
- Do not forecast when the history cannot support it (rule of thumb: fewer than 2 full seasonal cycles for a seasonal metric, or fewer than 12 points for a trend).

## 4. Writing confidence down

Use the form: `Confidence: Medium. Why: 6 months of history only; 2 subscriptions excluded for missing dates (3.5% of MRR).`

A confidence label without a reason is incomplete and must be flagged in quality checks.
