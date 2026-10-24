---
name: customer-intelligence
description: Segments customers and analyses retention, churn, revenue concentration, support burden, engagement and expansion potential by segment and account, combining revenue, product and support outputs through validated joins, and flags accounts with co-occurring risk signals. Profitability is assessed only when cost allocation data exists. Use when asking which customers or segments matter, are at risk, or could expand.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Customer intelligence

## Purpose

Answer "which customers, and which kinds of customer, are worth what, and where is the risk?" by combining the outputs of the revenue, product and support analyses at entity level. This skill **consumes** other skills' outputs. It does not recalculate MRR or usage, and it does not pretend those analyses ran if their outputs are missing.

Shared rules (local copies): `references/saas-metric-definitions.md`, `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`.

## Activation conditions

Use when the question involves:

- customer segments and how they differ (retention, value, support load)
- churn and retention by segment
- revenue concentration at account level
- support burden or cost to serve
- accounts at risk, or accounts with expansion potential
- customer profitability (only with cost allocation data)

## Required inputs

| Input | If missing |
|---|---|
| `revenue-intelligence` output JSON (per-customer MRR, receivables, exclusions) | Run that skill first. Do not estimate per-customer revenue |
| Customers table with segment attribute | Segments cannot be formed. Ask what attribute defines segments |
| Entity map from `cross-module-data-mapping` | Duplicate customers may split or double-count. State it and cap confidence at Low |

## Optional inputs

- `product-intelligence` output JSON (zero usage, account usage)
- Support tickets plus the validated normalisation rule (from mapping)
- Customer-level cost allocation (`customer_id,cost`) for profitability. It must come with a stated allocation method
- CRM opportunities for expansion pipeline (through the validated crm_account_id relationship)

## Execution procedure

1. **Confirm inputs and their provenance.** List the artefacts consumed (with IDs) in the envelope's `inputs`. Without the product output, zero-usage signals are absent and must be listed as `UNKNOWN`, not as "none".
2. **Run the engine:**
   `python3 scripts/customer_segments.py --customers <customers.csv> --revenue <revenue.json> [--product <product.json>] [--tickets <tickets.csv> --ticket-normalise <rule>] [--entity-map <map.csv>] [--segments A,B,C] [--costs <costs.csv>]`.
3. **Check the notes:** unknown segments, segment conflicts between merged records, unresolved tickets, and customers excluded from MRR (status `excluded-from-mrr` with reasons). These are data issues, not customer behaviour.
4. **Describe segments:** cohort NRR, logos retained, share of MRR and tickets per active account. With fewer than 5 customers in a segment, describe the individual accounts rather than "segment behaviour".
5. **Concentration:** link the revenue concentration to named accounts and their signals.
6. **Health signals.** For each account on the review list, give the signals with evidence IDs. Present them as a **co-occurrence for review by the account owner**, not a churn prediction. No churn model is fitted here.
7. **Churned against retained:** the engine provides descriptive means with n and a confidence cap. Report them with the cap. No significance claims without a test.
8. **Expansion opportunities:** accounts with growing usage, open expansion opportunities in CRM (validated join), or low adoption of features in their plan. Each is a HYP until validated with the account owner.
9. **Profitability:** only if `profitability.assessed` is true. Review the allocation method first (how support, infrastructure and staff costs were assigned). Otherwise write "Customer profitability not assessed: no cost allocation" and list what data would enable it.
10. **Recommend actions** tied to decisions (who acts, on which accounts, what is measured), each with confidence.

## Decision rules

- Customers are counted as de-duplicated entities. State the entity rule used.
- A health signal is an observation. Never write "C006 will churn".
- Support burden needs normalised ticket-to-customer resolution. Report the unresolved count beside it.
- No profitability, margin or "unprofitable customer" claims without cost allocation data and a stated method.
- Segment comparisons with fewer than 5 churn events: Low confidence at most.
- Account-level outputs go to the client's leadership only. Do not include individual end-user data.

## Output structure

```markdown
# Customer intelligence: <client>, <period>
## 1. Inputs consumed        (artefact IDs; anything missing marked UNKNOWN)
## 2. Data notes             (excluded-from-MRR accounts, unresolved tickets, segment conflicts)
## 3. Customer segments      (segment | cohort | NRR | logos retained | active | MRR share | tickets per account)
## 4. Segment characteristics (what distinguishes each; sample-size notes)
## 5. Retention and revenue patterns
## 6. Support and cost patterns (support burden; profitability only if assessed)
## 7. Accounts for review    (account | signals | evidence IDs | suggested owner action)
## 8. Potential opportunities (expansion HYPs with evidence)
## 9. Potential risks
## 10. Recommended actions   (decision | action | owner | measure | confidence)
```

## Quality checks

- [ ] Every figure matches the engine output, which in turn matches the revenue and product outputs.
- [ ] Excluded-from-MRR accounts are not described as inactive or churned.
- [ ] No prediction language for health signals.
- [ ] Profitability is absent or explicitly assessed with its method.
- [ ] Sample-size notes appear wherever a segment has fewer than 5 customers.
- [ ] The inputs list shows the actual artefacts consumed.

## Failure and escalation conditions

- **No revenue output:** stop and run `revenue-intelligence`.
- **Segment attribute missing or ambiguous:** ask. Do not invent segments from MRR bands without saying so (MRR-band segmentation is allowed if labelled as such).
- **Cost allocation supplied without a method:** do not compute profitability. Ask for the method.
- **Requests to rank individual end users or employees:** decline. This skill works at account level.

## Examples

Synthetic fixture, Jan–Jun 2026, with revenue, product and tickets inputs, and C013 merged into C003:

| Segment | Cohort | NRR | Logos | Active Jun | Share of MRR | Tickets per active account |
|---|---|---|---|---|---|---|
| Enterprise | C001, C002, C009 | 112.50% | 3/3 | 3 | 80.90% | 1.67 |
| Mid-Market | C003, C004, C012 | 31.91% | 1/3 | 2 | 14.83% | 1.50 |
| SMB | C005, C006 | 68.75% | 2/2 | 3 | 4.27% | 1.33 |

Every segment has fewer than 5 customers, so describe accounts rather than segments.

Account for review: **C006**, with signals contraction (500 to 250), zero usage in June, overdue 250 USD and 4 tickets in 60 days [CALC:cust-health-c006]. Suggested action: account owner review this month. Measure: renewal outcome and usage over the next 60 days. Confidence: the signals are measured (High). What they mean for retention is unknown.

Data note: C010 and C011 are `excluded-from-mrr` (missing start date; `US$` currency), not inactive.

Churned vs retained tickets: 3.5 (n = 2) against 1.83 (n = 6). Descriptive only; confidence capped at Low.

## Related skills

- Upstream: `revenue-intelligence` (required), `product-intelligence`, `cross-module-data-mapping` (entity map, ticket normalisation), `business-metric-dictionary`.
- Consumers: `bidim-opportunity-scoring`, `executive-decision-intelligence` (the CBO and CEO perspectives), `intelligence-report-builder`.
- `anomaly-hypothesis-validation` tests explanations for segment-level shifts.
