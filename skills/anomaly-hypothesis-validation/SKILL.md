---
name: anomaly-hypothesis-validation
description: Detects unusual movements in business metrics against an explicit baseline with a robust, documented method, checks data quality first, generates competing explanations and tests each against evidence (decomposition, cross-module checks), then rates confidence and states what evidence is still missing. Use when a metric jumps or drops unexpectedly, or when someone proposes an explanation for a change.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Anomaly and hypothesis validation

## Purpose

Stop unusual numbers from turning into stories. When a metric moves, this skill establishes whether the movement is real, whether it matters commercially and which explanations the evidence supports, **in that order**. It always considers more than one explanation, including "the data is wrong".

Shared rules (local copies): `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/saas-metric-definitions.md`, `references/data-security-principles.md`.

## Activation conditions

Use when:

- an analysis skill hands over an unusual movement (cost spike, usage drop, MRR swing)
- leadership asks "why did X change?"
- someone proposes a cause ("churn rose because of the price change") that needs testing
- a metric breaches an agreed threshold

## Required inputs

| Input | If missing |
|---|---|
| The metric series (period, value), from a skill output or a CSV | Cannot detect anomalies. Ask for the series. Never reconstruct it from memory |
| The metric's definition (dictionary ID) | Ask. An anomaly in an undefined metric cannot be interpreted |
| Detail data that can test explanations (the series broken down by dimension, related modules) | Detection only. Every explanation stays HYP with confidence Low |

## Optional inputs

- Readiness output for the source tables (known gaps, invalid values)
- Known events: releases, price changes, incidents, campaigns, with dates and sources
- A materiality threshold agreed with the client (an absolute amount or a percentage)

## Execution procedure

1. **Establish a valid baseline.** Choose baseline periods that are comparable (same definition, no known structural break) and state them. Note the sample size.
2. **Identify unusual movements:** `python3 scripts/detect_anomalies.py <series> [--path ...] [--baseline-from P --baseline-to P] [--materiality N]`. The method is robust z (median and MAD, threshold 3.5), with a percentage fallback when MAD is 0. Record the flagged periods, z values and warnings.
3. **Separate statistical from commercial significance.** A flag is unusual against the baseline. Material means it exceeds the agreed materiality. Report both. A 20-point z-score on a small cost line may not matter; a quiet 3% MRR decline might.
4. **Check data quality before business explanations.** Was the drop across all users, accounts and event types at once (pipeline gap)? Are there missing days, duplicates or late-arriving data? Did a definition change? Use the readiness output and the raw counts.
5. **Generate alternative explanations.** At least three, always including a data explanation and a "normal variation" explanation where plausible. Write each one as testable, using `templates/hypothesis-register.md`.
6. **Test each hypothesis** with deterministic evidence:
   - decomposition by dimension: `python3 scripts/decompose_change.py <data.csv> --period-col ... --value-col ... --dims ... --base P --target P`
   - cross-module checks (for example, did active customers or MRR change with cost?)
   - timing against known events (with sources)
   - for each test, state in advance what result would refute the hypothesis
7. **Determine confidence** per hypothesis with `references/confidence-scoring.md`. Supported means the evidence matched and the refutation test failed to refute. Not supported means refuted. Untested means no data to test.
8. **Identify missing evidence** that would raise or lower confidence, and who holds it (for example "platform team: was a load-test cluster started on 1 May?").
9. **Recommend next steps:** confirm with an owner, add monitoring, fix the data, or close as normal variation.

## Decision rules

- Never present a single explanation without alternatives.
- Data-quality explanations are tested first. A real business change is concluded only after they fail.
- Remove an outlier only after investigating it. Record the reason and its effect on results.
- Timing alone ("it happened after the release") is not causal evidence. It can make a hypothesis plausible but not supported.
- Small baselines (under 12 points) produce prompts for investigation, not findings.
- Never claim statistical significance without a stated test. The robust z is a screening rule, not a significance test.
- If no hypothesis survives, say "unexplained". Do not pick the least-bad story.

## Output structure

For each anomaly:

```markdown
### A-01 <metric> <period>: <direction and size>
- Observed anomaly: value, change against baseline, flagged by <method>
- Baseline and comparison period: periods, n, median, MAD
- Calculation: script, parameters, evidence ID
- Statistical vs commercial: flagged yes/no; material yes/no (threshold)
- Data-quality check: result
- Potential explanations: hypothesis register table
  | ID | Hypothesis | Test | Refuted if | Result | Evidence for | Evidence against | Status | Confidence |
- Limitations
- Missing evidence (item, holder)
- Recommended next steps
```

## Quality checks

- [ ] The baseline periods and n are stated.
- [ ] At least three hypotheses, including a data-quality one.
- [ ] Every hypothesis has a test with a refutation condition written before the result.
- [ ] Decomposition or cross-module numbers come from scripts.
- [ ] Statistical and commercial significance are reported separately.
- [ ] No causal claim rests on timing alone.
- [ ] The status uses supported, not supported, untested or unexplained, never "proven".

## Failure and escalation conditions

- **The series is too short** (under 3 points): no detection. Describe the change only.
- **The anomaly reveals possible fraud, data tampering or a security incident:** stop analysis and escalate to the human owner. Do not investigate individuals.
- **The client pushes for a specific explanation:** test it like any other and report the result.
- **An explanation needs data from another client or external benchmarks:** not permitted without approval (`references/data-security-principles.md`).

## Examples

**A-01 Infrastructure cost, May 2026: +4,200 USD against April** (synthetic fixture)

- Baseline Jan–Jun (n = 6): median 10,250, MAD 150. May robust z = 19.11, flagged [CALC:anom-infra-2026-05]. Material (threshold 1,000): yes. Small-sample warning.
- Data-quality check: no duplicate cost lines; all months complete.

| ID | Hypothesis | Test | Refuted if | Result | Status | Confidence |
|---|---|---|---|---|---|---|
| H1 | Customer growth raised production load | Active customers and production cost, Apr → May | Customers flat and production flat or down | Customers 9 → 9; production −100 | Not supported | Medium |
| H2 | Non-production resources left running | Decompose by environment | Staging share of change < 50% | Staging +4,300 = 102.38% of the change | Supported | Medium (owner not yet confirmed) |
| H3 | Billing error or duplicate line | Check for duplicate month/environment/service keys | Duplicates found | None found | Not supported | Medium |
| H4 | Price change by the provider | Compare unit prices | No price data | n/a | Untested | Insufficient |

Missing evidence: the platform team's confirmation of what ran in staging in May. Next step: confirm, then add a staging budget alert.

**A-02 Product events, week of 2026-05-11: 0 events against a median of 35.** Fallback method (MAD = 0). Data-quality hypothesis supported: every user, account and event type drops to zero at once, with no matching change in billing or support, and readiness shows 7 consecutive missing days. Business explanation (usage collapse) not supported. Recommendation: ask the product team about the collection outage, and exclude that week from usage trends.

## Related skills

- Upstream: `revenue-intelligence`, `product-intelligence`, `customer-intelligence`, `operational-technology-intelligence` (unusual movements), `data-readiness-assessment` (known gaps).
- Consumers: `bidim-opportunity-scoring` (evidence confidence), `executive-decision-intelligence`, `intelligence-report-builder`.
- `intelligence-quality-audit` checks causal claims against this skill's statuses.
