---
name: business-metric-dictionary
description: Creates and maintains a client-specific dictionary of business metrics (MRR, ARR, growth, gross margin, NRR, GRR, churn, CAC, LTV, ARPA, activation, adoption, concentration, support burden) with formulas, source fields, grain, inclusion and exclusion rules, currency and timezone handling, owners and approval status. Use before calculating metrics for a client, or when definitions are disputed.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Business metric dictionary

## Purpose

Fix, for one client, exactly what each metric means and how it is calculated, and record who agreed. Metrics such as churn, CAC and LTV have no universal definition. This skill makes the chosen definition explicit, so every number in every report can be traced to an approved formula.

It also records which metrics **cannot** be calculated yet, and why. That prevents a later skill from approximating them.

Shared rules (local copies): `references/saas-metric-definitions.md` (default definitions and variants), `references/evidence-standards.md`, `references/confidence-scoring.md`.

## Activation conditions

Use when:

- an engagement reaches the analysis phase and no approved dictionary exists
- someone asks "how do we define churn / NRR / CAC here?"
- two reports or people disagree on a number, which is often a definition difference
- a new metric is requested, or the data changes in a way that affects a definition
- readiness or mapping produced normalisation and exclusion rules that need recording

## Required inputs

| Input | If missing |
|---|---|
| Field inventory from `business-data-inventory` | Write definitions without `required_fields` validation, and mark them draft |
| The metrics needed by the proposed analyses | Start with the default SaaS set in `references/saas-metric-definitions.md` |
| A business owner per metric (a role) who can approve it | Status stays `draft`. Every result using a draft definition is labelled "definition not yet approved" |

## Optional inputs

- The client's existing definitions (board pack, investor reports, finance policies)
- Readiness output (exclusion and normalisation rules)
- Cross-module map (entity-resolution rules)

## Execution procedure

1. **Collect existing definitions** the client already uses. Copy them exactly, with their source. Where they conflict (the finance pack against the board deck), record both and raise the conflict.
2. **Choose a definition per metric.** Start from the default ID in `references/saas-metric-definitions.md` (for example `NRR-1`). If the client's practice differs, either pick the listed variant or set `definition_id: custom` and write the full formula.
3. **Fill every attribute:** name, business definition (plain language), formula (with dataset.field names), source systems, required fields, calculation grain, time period, inclusions, exclusions, currency handling, timezone handling, known limitations, business owner, appropriate use cases and status. Use `examples/metric-dictionary.example.json` as the shape.
4. **Record data rules** that affect the metric: entity de-duplication, currency normalisation (case only), exclusions for missing fields. Link them to the readiness and mapping evidence IDs.
5. **Test calculability.** For each metric, check that its required fields exist (run the validator with `--inventory`) and that readiness permits it. If it cannot be calculated, set `status: not-calculable` with `not_calculable_reason`, and name a substitute if one is honest. Example: "infrastructure cost ratio (OPS-2), which is not gross margin".
6. **Validate:** `python3 scripts/validate_dictionary.py <dictionary.json> [--inventory <inventory.json>]`. Fix every error. Draft warnings are acceptable but must be visible in reports.
7. **Seek approval.** Present the definitions to the owners. Record `approved_by` (role) and `approved_on`. Never mark a metric approved on the client's behalf.
8. **Version it.** Add a `change_log` entry for every change. Results always cite the dictionary version.

## Decision rules

- One metric ID has one definition per client at a time. If two are needed (for example board churn and product churn), give them separate IDs.
- If a definition is changed after results were published, the old results are labelled with the old version. Do not silently restate them.
- Short history is a limitation, not a reason to change the definition. Label the window ("NRR, 5-month window").
- Never fill in a definition for a metric whose inputs do not exist. Mark it not calculable.
- Use cases matter. An activation definition approved for onboarding work is not automatically suitable for investor reporting.
- Never set an approval yourself. Approval comes from the named client role.

## Output structure

1. Dictionary JSON (machine-readable; validated by `scripts/validate_dictionary.py`)
2. Human-readable table:

```markdown
| Metric | Definition ID | Formula | Grain / period | Exclusions | Owner | Status | Limitations |
```

3. Not-calculable register: metric, reason, what data would enable it, any honest substitute
4. Open definition questions (with the owner who must answer)
5. Change log

## Quality checks

- [ ] The validator reports `valid: true`.
- [ ] Every formula names dataset.field inputs, not vague terms.
- [ ] Currency and timezone handling is stated for every money and time metric.
- [ ] CAC, LTV and gross margin are either fully supported by data or marked not calculable with a reason.
- [ ] Every approved metric has a role and a date. Nothing is approved by the assistant.
- [ ] Draft metrics are listed so reports can label them.
- [ ] Conflicts between existing client definitions are recorded, not resolved silently.

## Failure and escalation conditions

- **The owner will not or cannot approve:** keep the metric draft and escalate if it blocks a deliverable.
- **The client insists on a definition that misleads** (for example GRR including expansion): record their definition under its own ID, explain the difference in writing, and show the standard version alongside it.
- **The definition depends on accounting policy** (revenue recognition, deferred revenue): mark it outside scope unless finance supplies the policy. Do not give accounting advice.

## Examples

**Entry, abridged from `examples/metric-dictionary.example.json`:**

```json
{"id": "nrr", "definition_id": "NRR-1",
 "formula": "cohort_mrr(end) / cohort_mrr(start); cohort = customers with MRR > 0 at start",
 "time_period": "Jan-Jun 2026 (5-month window); 12-month standard not yet possible",
 "known_limitations": ["window shorter than 12 months: do not compare with 12-month benchmarks"],
 "status": "approved", "approved_by": "CFO", "approved_on": "2026-10-20"}
```

**Not calculable:**

```json
{"id": "ltv", "status": "not-calculable",
 "not_calculable_reason": "Gross margin unavailable; churn history under 12 months and fewer than 30 churn events"}
```

## Related skills

- Upstream: `business-data-inventory` (fields), `data-readiness-assessment` (exclusion and normalisation rules).
- Parallel: `cross-module-data-mapping` (entity-resolution rules referenced by definitions).
- Consumers: `revenue-intelligence`, `customer-intelligence`, `product-intelligence`, `operational-technology-intelligence`, `intelligence-report-builder` (the Metric definitions section), `intelligence-quality-audit` (recomputes against these definitions).
