---
name: cross-module-data-mapping
description: Discovers and validates relationships between datasets from different business systems (billing with product usage, CRM with billing, support with retention, infrastructure cost with active customers), measuring match rates, cardinality, fan-out and identifier normalisation, and resolving duplicate entities before any cross-module analysis. Use before joining data from two or more systems.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Cross-module data mapping

## Purpose

Most valuable BI findings combine systems, for example "accounts whose usage fell also opened more tickets". They are also where analyses go wrong most often: joins on similar-looking fields, duplicate customers that double revenue, identifiers in different formats that silently drop records. This skill validates every relationship **before** it is used, and records each one with its evidence, its confidence and the risks of getting it wrong.

Shared rules (local copies): `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/saas-metric-definitions.md` (entity rules), `references/data-security-principles.md`.

## Activation conditions

Use when:

- an analysis needs data from two or more systems
- the inventory lists candidate relationships (HYP) that need validating
- numbers disagree between systems (for example CRM closed-won and billing new revenue)
- readiness reports a low foreign-key match rate
- a customer, account or user appears under several IDs or names

## Required inputs

| Input | If missing |
|---|---|
| The datasets to relate (files) | Cannot proceed. Document proposed relationships as HYP only |
| Inventory (grain and keys per dataset) | Establish the grain first ("one row per ..."). Never join without knowing the grain |
| The analytical question each relationship serves | Ask. Relationships are validated for a purpose, not in general |

## Optional inputs

- Readiness output (foreign-key match rates, duplicate keys)
- Client confirmation of entity identity (for example "C013 is the same company as C003")
- Control totals from one system to reconcile against another

## Execution procedure

1. **List candidate relationships** from the inventory: source dataset and field, target dataset and field, the entity each side represents (customer, account, user, subscription) and the question it serves. Fill `templates/join-register.md`.
2. **Confirm entity identity, not field names.** Check that both sides identify the same kind of thing. `account_id` in product data may mean workspace, while `customer_id` in billing means legal entity. `account_name` in CRM is free text typed by sales. Never join on names.
3. **Find duplicate entities:** `python3 scripts/suggest_duplicates.py <table.csv> <id_col> --name-column <name_col> --shared-key <col>`. Treat each candidate as a suggestion. Merge only after owner confirmation, and record it in an entity map (`raw_id,entity_id,reason`).
4. **Profile each join:** `python3 scripts/profile_join.py <left.csv> <left_key> <right.csv> <right_key> [--normalise ...] [--entity-map ...]`. Record row match rate, key match rate, duplicate keys, observed cardinality, fan-out and unmatched keys.
5. **Normalise identifiers only with a written rule,** starting with the least aggressive normaliser that works: `upper_trim`, then `alnum_upper`, then `digits:P:W`. Review every `normalisation_collisions` group: each group must be one entity. Record the rule and the match-rate gain (for example 60% to 95%).
6. **Explain unmatched records.** Classify each unmatched key as an expected non-match (prospects in CRM with no billing record), a data error (an ID that exists nowhere, such as a typo), or unknown. Never drop unmatched records silently. Report their count and, if relevant, their amount.
7. **Check cardinality against expectation.** If you expect 1:N (customer to tickets) and observe N:M, stop: entity resolution is incomplete. Fan-out greater than right rows means the join multiplies records and inflates sums.
8. **Reconcile across modules** where the same business event appears in two systems. For example: CRM closed-won ARR against billing new MRR × 12 for the same customers. Report agreement or the differences, with amounts.
9. **Rate confidence per relationship.** High: documented key, ≥ 98% match, expected cardinality, no unreviewed collisions. Medium: normalisation needed, 90–98% match, or reviewed collisions. Low: under 90% match, unexpected cardinality, or name-based matching. Analysis skills inherit this rating (see the caps in `references/confidence-scoring.md`).
10. **List the analytical questions** each validated relationship enables, and those it does not.

## Decision rules

- Never join on names, emails or other free text when an ID exists. If no ID exists, name matching is Low confidence and needs human review of every match.
- Never join until the grain of both sides is known.
- An entity merge needs a recorded reason and owner confirmation. The assistant may suggest merges; it may not decide them.
- Normalisation rules must be deterministic and documented, and applied identically by every downstream skill.
- A relationship under 90% match can be used only with its unmatched share disclosed beside every result that depends on it.
- If reconciliation differences exceed the agreed tolerance (default: 1% of the amount), escalate before the relationship is used for revenue figures.

## Output structure

```markdown
# Cross-module map: <client> (as of <date>)
## 1. Relationship summary (relationship | purpose | match rate | cardinality | confidence)
## 2. Join register        (templates/join-register.md, one row per relationship)
## 3. Entity resolution map (raw_id | entity_id | evidence | confirmed by (role) | date)
## 4. Normalisation rules  (rule | applies to | match before → after | collisions reviewed)
## 5. Unmatched records    (relationship | count | class: expected / error / unknown | amount)
## 6. Reconciliations      (system A vs B | measure | A | B | difference | verdict)
## 7. Join risks           (what would go wrong if misused, for example fan-out inflating revenue)
## 8. Analytical questions enabled / not enabled
```

Handoff payload: `relationships[]` (profile JSON plus confidence), `entity_map`, `normalisation_rules[]`.

## Quality checks

- [ ] Every relationship states the entity on each side and its grain.
- [ ] Every normaliser's collisions were reviewed and found to be one entity per group.
- [ ] Every merge has a reason and a confirming role (or is marked "pending confirmation").
- [ ] Unmatched records are counted and classified.
- [ ] Fan-out is checked for every join used in a sum.
- [ ] Confidence ratings follow the stated criteria.

## Failure and escalation conditions

- **No shared identifier between systems:** report that the relationship is not possible without a mapping table from the client. Propose the mapping request. Do not fuzzy-match on names for financial analysis.
- **N:M where 1:N was expected:** stop dependent analyses until it is resolved.
- **Reconciliation failure beyond tolerance:** escalate to the data owner.
- **Joining would combine personal data from several systems into a richer profile of individuals:** check that the purpose and permission cover it. Default to account-level aggregates.

## Examples

On the synthetic fixture (run from `fixtures/synthetic_saas/`):

| Relationship | Normaliser | Match | Cardinality | Confidence | Note |
|---|---|---|---|---|---|
| customers.customer_id → support_tickets.customer_ref | none | 12/20 (60%) | 1:N | Low | Mixed formats: c003, C-009, CUST-0009 |
| same | digits:C:3 plus entity map | 19/20 (95%) | 1:N | Medium | Collisions reviewed; C099 is an ID that exists nowhere (data error); C013 merged into C003 |
| customers.crm_account_id → crm_opportunities.crm_account_id | none | 5/8 opportunities | 1:1 on matched keys | Medium | 0015A003 duplicated on the customer side (fan-out risk); 3 unmatched are prospects (expected) |
| customers.customer_id → subscriptions.customer_id | none | 14/14 | 1:N | High | C002 and C006 each have 2 subscriptions (upgrade or downgrade) |

Reconciliation: CRM closed-won new ARR 26,400 USD against billing new MRR × 12 = 26,400 USD, which agrees. Expansion 24,000 against 24,000 also agrees.

Join risk: summing MRR after a customers ↔ CRM join without merging C013 would double-count Bluefin Logistics whenever it has a CRM record.

## Related skills

- Upstream: `business-data-inventory` (candidate relationships), `data-readiness-assessment` (exact-match foreign-key rates).
- Parallel: `business-metric-dictionary` records the entity and normalisation rules that metrics depend on.
- Consumers: `revenue-intelligence`, `customer-intelligence`, `product-intelligence`, `operational-technology-intelligence` and `anomaly-hypothesis-validation`; `intelligence-quality-audit` checks for incorrect joins.
