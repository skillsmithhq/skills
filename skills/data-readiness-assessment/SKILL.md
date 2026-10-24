---
name: data-readiness-assessment
description: Assesses whether business datasets can support reliable BI by checking completeness, validity, uniqueness, consistency, referential integrity, coverage and freshness with a published, reproducible scoring method, then states which proposed analyses are ready, usable with caveats or blocked. Use after a data inventory and before any metric calculation or analysis.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Data readiness assessment

## Purpose

Tell the team and the client, with evidence, which analyses the data can support now, which need caveats and which need remediation first. Every score is reproducible from the published method in `references/readiness-method.md`. No score is assigned by judgement alone.

Shared rules (local copies): `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`, `references/saas-metric-definitions.md`.

## Activation conditions

Use when:

- a data inventory exists and analysis is about to begin
- the user asks "is this data good enough?", "can we trust these numbers?" or "what needs fixing?"
- a new export arrives that replaces an earlier one (re-run and compare)
- an analysis skill needs a readiness level for its confidence rating

## Required inputs

| Input | If missing |
|---|---|
| Datasets as files, plus the inventory from `business-data-inventory` | Without the inventory, build a minimal one first (grain, keys, required fields). Do not guess the keys |
| The list of proposed analyses and the fields each needs (from the proposal or discovery) | Assess tables generically and state that suitability per analysis is not assessed |
| As-of date | Ask. Freshness and timestamp plausibility depend on it |

## Optional inputs

- Allowed values for categorical fields (status, segment, stage) from the client
- Expected period coverage (for example "billing from Jan 2024")
- Independent control totals for reconciliation (for example finance ledger revenue by month)

## Execution procedure

1. **Write the config.** For each table, declare the primary key, natural keys, required fields, currency fields, numeric fields, allowed values, date and datetime fields (including `future_ok` fields such as due dates), consistency rules, foreign keys, and coverage or freshness settings. Declare analyses with the table fields they require. Example: the collection's `fixtures/configs/readiness_config.json`.
2. **Run** `python3 scripts/assess_readiness.py <config.json>`. Save the output as evidence (`dq-readiness-<date>`).
3. **Read the critical flags first.** They cap levels regardless of score. Explain each in business terms. For example: "1 subscription has no start date, so 350 USD of MRR cannot be placed in any month."
4. **Quantify the business effect** of each issue where you can: the rows and amounts affected, and the periods affected. Use deterministic counts from the data, not estimates.
5. **Separate normalisable from invalid values.** The currency check reports `normalisable_by_case` values (`usd`) separately from invalid ones (`US$`). Propose a normalisation rule only for unambiguous cases, and record it for the metric dictionary.
6. **Note what the score cannot see:** accuracy (needs control totals), schema stability, field meaning, and identifiers that need normalisation before they match (`cross-module-data-mapping` measures normalised match rates).
7. **Reconcile against control totals** if they were provided. Report the differences as findings, with amounts.
8. **Write suitability per analysis:** level, blocking issues, caveats and remediation. Remediation names who must do what ("Billing owner: supply start date for S010, or confirm it is a test record").
9. **Hand off.** The analysis skills read `suitability`. `bidim-opportunity-scoring` uses the level as data readiness D.

## Decision rules

- Never present a score without its method and its flags.
- Never "fix" data silently. Every cleaning step (deduplication, case normalisation, exclusion) is recorded with the rows affected and handed to the analysis skills as an explicit rule.
- Investigate outliers before excluding them. An extreme value can be a real large customer.
- A dataset whose required fields are unknown cannot be rated above 3.
- If the as-of date is later than the latest data, report freshness as a limitation. Do not shift the as-of date.
- Re-assessments compare with the previous run and report deltas. Do not overwrite the history.

## Output structure

```markdown
# Data readiness: <client> (as of <date>)
## 1. Summary          (one line per analysis: level, label, top blocker)
## 2. Method           (link or copy references/readiness-method.md; weights and caps)
## 3. Dataset scores   (table | rows | score | level from score | final level | flags)
## 4. Critical limitations (issue | rows/amount affected | business effect | remediation owner)
## 5. Field-level findings (table.field | check | failing / applicable | detail)
## 6. Normalisation and exclusion rules proposed (rule | rows affected | needs client approval?)
## 7. Suitability for proposed analyses (analysis | level | blocking issues | caveats)
## 8. Not measured by this assessment (accuracy, schema stability, meaning)
## 9. Remediation requirements (ordered by which analyses they unblock)
```

## Quality checks

- [ ] Every number in the report matches the script output.
- [ ] Every critical flag is translated into a business effect with rows and amounts.
- [ ] Normalisable values are not reported as unusable, and invalid values are not quietly normalised.
- [ ] Suitability is stated for every proposed analysis.
- [ ] The limits of the score (accuracy, meaning) are stated.
- [ ] No row-level personal data appears in the findings. Refer to record IDs.

## Failure and escalation conditions

- **Keys unknown:** ask the data owner. Without a primary key, uniqueness cannot be assessed; say so.
- **A table fails to load:** report it as level 1 with the error. Do not drop it from the summary.
- **Control totals disagree materially with the data** (default: more than 1%): escalate before any revenue analysis is presented.
- **The data looks synthetic, test or sandbox** (when production was expected): stop and confirm with the owner.

## Examples

On the synthetic fixture, with as-of date 2026-06-30:

| Table | Score | From score | Final | Why |
|---|---|---|---|---|
| subscriptions | 99.03 | 5 | 3 | Critical: `start_date` 92.86% complete (S010). Major: currency `US$` and `usd` |
| invoices | 99.00 | 5 | 3 | Critical: `invoice_id` duplicated (1 exact duplicate row) |
| support_tickets | 92.72 | 4 | 3 | Critical: `customer_ref` exact match 60% (mixed ID formats) |
| product_events | 99.43 | 5 | 4 | Major: 7 missing days (2026-05-11..17), 2 implausible timestamps |

Business translation: "MRR can be calculated, but 800 USD of monthly revenue on two subscriptions cannot be included until a start date and a valid currency are supplied. The duplicate invoice would overstate H1 billing by 7,000 USD if it were not removed."

## Related skills

- Upstream: `business-data-inventory`.
- Next: `business-metric-dictionary` records the normalisation and exclusion rules; `cross-module-data-mapping` measures normalised join rates.
- Consumers: `revenue-intelligence`, `customer-intelligence`, `product-intelligence`, `operational-technology-intelligence` and `bidim-opportunity-scoring` (data readiness D).
