---
name: revenue-intelligence
description: Calculates and interprets revenue metrics (MRR, ARR, new, expansion, contraction and churned revenue, NRR, GRR, growth, ARPA, concentration, recurring share, collections and outstanding invoices) with a deterministic script, documenting formulas, source fields, periods, exclusions and assumptions. Use when analysing a client's revenue health, quality or trends from billing data.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Revenue intelligence

## Purpose

Produce revenue numbers leadership can rely on, and explain what they mean for decisions. **The script calculates and the analyst interprets.** No revenue figure in an output may come from estimation, mental arithmetic or recall.

Shared rules (local copies): `references/saas-metric-definitions.md`, `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`.

## Activation conditions

Use when:

- the question is about revenue level, growth, retention, movements, revenue quality, concentration or collections
- a board, investor or leadership report needs revenue metrics
- another skill (customer, operational, anomaly, BIDIM) needs per-customer MRR or revenue totals
- revenue numbers from two sources disagree

## Required inputs

| Input | If missing |
|---|---|
| Subscriptions export (ID, customer, recurring amount, currency, start, end, status) | Cannot calculate MRR. Stop |
| Invoices and payments exports | Calculate MRR metrics only; mark collections `UNKNOWN` |
| Period (start and end month) and as-of date | Ask |
| Readiness output covering these tables | Run `data-readiness-assessment` first, or proceed in degraded mode with confidence capped at Low (see `references/skill-workflow-map.md`) |
| Approved definitions (metric dictionary) | Use the defaults (MRR-1 and others) and label the results "definition not yet approved" |

## Optional inputs

- Entity map from `cross-module-data-mapping` (duplicate customers)
- Segments or plan attributes, for segment cuts (or hand them to `customer-intelligence`)
- Finance control totals for reconciliation

## Execution procedure

1. **Prepare a working copy** with the expected column names (see the script docstring). Record any renaming.
2. **Run the engine:**
   `python3 scripts/revenue_metrics.py --data-dir <dir> --start YYYY-MM --end YYYY-MM --as-of YYYY-MM-DD [--currency USD] [--entity-map map.csv]`.
   Save the JSON output as an artefact. Its `evidence` array holds ready-made CALC items.
3. **Report the exclusions first:** subscriptions excluded (with MRR and reason), currency normalisations, duplicate invoices removed (with amount), and invalid-currency invoices. Express the excluded MRR as a share of the total.
4. **Describe the trend** from `monthly`: level, direction, and movements by type, naming the customers behind each movement. Separate one-off events from patterns. With a few dozen customers, a single account can make a month.
5. **Retention:** report NRR, GRR, logo churn and gross revenue churn with their **window label**. If the window is under 12 months, say so beside every figure and do not compare with 12-month benchmarks.
6. **Revenue quality:** recurring share, concentration (top 1 and top 3), collections, outstanding and overdue amounts, and receivables by customer. A high concentration is a risk finding even when growth is positive.
7. **Segment cuts** (optional): only from computed per-customer MRR (`customer_mrr`), joined to segments through a validated relationship.
8. **Unusual movements:** list the months or customers with movements far from the norm, and hand them to `anomaly-hypothesis-validation`. Do not explain them yourself without testing.
9. **Reconcile** with finance totals if they were provided. Billing MRR is not recognised revenue; explain any difference rather than forcing agreement.
10. **Interpret.** For each finding, answer the eight questions in `references/evidence-standards.md`. Label every interpretation and give at least one alternative reading.
11. **Recommend investigations,** not conclusions, where the evidence is thin.

## Decision rules

- Every number cites its evidence ID from the script output (for example `rev-nrr`).
- Never sum different currencies. No FX conversion without an approved FX table and date. The engine excludes non-reporting currencies and reports them.
- Never include a subscription with no start date "by assumption". Exclude it, report it, and ask the billing owner.
- MRR is a contract measure, not cash and not recognised revenue. Do not call it "revenue" without qualification in financial contexts.
- Fewer than 5 churn events: no statements comparing groups' churn above Low confidence.
- No forecasts from fewer than 12 monthly points. With more history, any forecast needs explicit assumptions and stays at Medium confidence or below.
- Do not attribute a movement to a cause (pricing, a feature, a salesperson) without evidence. Write "coincides with" and hand it to the anomaly or hypothesis skill.

## Output structure

```markdown
# Revenue intelligence: <client>, <period>
## 1. Headline metrics       (MRR, ARR, growth, NRR, GRR, logo churn, ARPA; each with evidence ID and window label)
## 2. Exclusions and data rules (excluded subscriptions and MRR, normalisations, duplicates removed)
## 3. Monthly trend and movements (table: month | MRR | new | expansion | contraction | churn | customers)
## 4. Retention              (cohort definition, NRR, GRR, churn; warnings)
## 5. Revenue quality        (recurring share, concentration, collections, outstanding, overdue by customer)
## 6. Segment analysis       (if done)
## 7. Unusual movements      (handed to anomaly-hypothesis-validation)
## 8. Opportunities and risks (each: evidence, why it matters, decision, confidence)
## 9. Recommended investigations
## 10. Formulas, source fields, periods, assumptions
```

Handoff: the script JSON in the envelope. Consumers use `customer_mrr`, `retention`, `collections.customer_receivables` and `evidence`.

## Quality checks

- [ ] Each figure in the text equals the script output, with the same rounding.
- [ ] MRR movements reconcile: previous MRR + new + reactivation + expansion − contraction − churn = current MRR for every month.
- [ ] The window label appears next to every retention metric.
- [ ] Exclusions are quantified and shown before the headline metrics are interpreted.
- [ ] No causal language without causal evidence.
- [ ] Concentration risk is reported when the top customer exceeds 20% of MRR or the top 3 exceed 50% (defaults; adjust per engagement and record the change).
- [ ] Customers are referred to by ID or approved name. No personal data.

## Failure and escalation conditions

- **Readiness level ≤ 2 for subscriptions:** do not publish revenue metrics. Report the blockers.
- **Excluded MRR above 5% of the total:** results are provisional. Escalate for data fixes before any client-facing use.
- **Reconciliation with finance differs by more than 1%:** escalate before presenting.
- **The data contains several currencies with no FX table:** report per currency, or ask for an approved FX source.
- **The client asks for a valuation or revenue projection:** out of scope. Offer the drivers and assumptions instead, with no number.

## Examples

Synthetic fixture, Jan–Jun 2026, as of 2026-06-30, with C013 merged into C003:

| Metric | Value | Evidence |
|---|---|---|
| MRR 2026-06 | 22,250 USD | rev-mrr-2026-06 |
| ARR | 267,000 USD | derived from rev-mrr-2026-06 |
| Growth Jan→Jun | 3.49% | rev-growth |
| NRR (5-month window) | 93.26% | rev-nrr |
| GRR (5-month window) | 83.95% | rev-grr |
| Logo churn | 25.0% (2 of 8) | rev-logo-churn |
| Top customer / top 3 | 31.46% / 80.90% | rev-concentration |
| Collection rate | 97.57%; outstanding 3,500; overdue 250 | rev-collections |

Exclusions: S010 (no start date, 350) and S011 (`US$`, 450) total 800 USD of MRR (3.5% of June MRR), and the duplicate invoice INV-1029 (7,000) was removed.

Finding (good): "Revenue is concentrated: C009 is 31.46% of MRR and the top 3 customers are 80.90% [CALC:rev-concentration]. Losing any one of the top 3 would cut MRR by 22–31%. Decision: whether to prioritise account management for the top 3 [REC]. Confidence: High for the measurement; the risk of loss itself is not measured."

Bad: "Growth slowed in June because Kestrel churned over support issues." (A causal claim; the support link is untested.)

## Related skills

- Upstream: `data-readiness-assessment`, `business-metric-dictionary`, `cross-module-data-mapping`.
- Consumers: `customer-intelligence` (per-customer MRR, receivables), `operational-technology-intelligence` (active customers, MRR), `anomaly-hypothesis-validation` (unusual movements), `bidim-opportunity-scoring`, `executive-decision-intelligence`, `intelligence-report-builder`, `intelligence-quality-audit` (recomputes figures).
