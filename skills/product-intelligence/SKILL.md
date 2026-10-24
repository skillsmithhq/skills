---
name: product-intelligence
description: Measures product usage (activation, active users, feature adoption, usage frequency, zero-usage paying accounts, account-level adoption) from event data, linking it to subscription value through validated joins, and proposes experiments without claiming that features cause retention or revenue. Use when analysing engagement, onboarding, adoption or usage risk from product events.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Product intelligence

## Purpose

Show how paying accounts actually use the product, where adoption is thin, and where usage signals risk or opportunity. Calculations are deterministic. Interpretations are labelled. **Usage associated with renewal is reported as association, never as cause.** Causal claims need an experiment.

Shared rules (local copies): `references/saas-metric-definitions.md` (MAU-1, ADOPT-1, ZERO-1, ACT-1), `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`.

## Activation conditions

Use when the question involves:

- activation, onboarding, time to value
- active users, engagement or usage frequency
- feature adoption, under-used or abandoned capabilities
- account-level usage compared with subscription value (needs revenue output)
- usage patterns before churn or renewal
- product experiments to propose

## Required inputs

| Input | If missing |
|---|---|
| Users export (user ID, account or customer ID, created date) | Account-level metrics impossible. Report event-level counts only |
| Events export (event ID, user ID, event name, timestamp) | Cannot proceed |
| Analysis month and as-of date | Ask |
| Activation event and window, agreed with the product owner | Use the dictionary default if there is one; otherwise ask. Never pick an activation event yourself and present it as agreed |

## Optional inputs

- `revenue-intelligence` output (`--revenue`), required for "paying accounts" and value comparisons
- Entity map from `cross-module-data-mapping`
- Feature catalogue (event name to feature and plan)
- Readiness output for the event tables

## Execution procedure

1. **Check readiness** for events and users: coverage gaps, invalid timestamps, orphan users. A gap inside coverage makes trend analysis over that period unreliable.
2. **Run the engine:**
   `python3 scripts/product_adoption.py --data-dir <dir> --month YYYY-MM --as-of YYYY-MM-DD --revenue <revenue.json> [--activation-event E --activation-days N] [--weeks-from D --weeks-to D] [--entity-map map.csv]`.
3. **Report data validity first:** invalid events by reason, coverage dates and missing days. The engine fills weeks that have no events with 0, so gaps are visible rather than hidden.
4. **Engagement:** MAU, active users per account, and features used per account (`account_usage`). Frequency comes from event counts per user only if the event set is complete for that period.
5. **Feature adoption** at account level over **paying** accounts. Check the `adoption_basis` field. If no revenue input was used, the denominator is not paying accounts, and the output must say so.
6. **Activation:** report rate **with cohort size**, the cohort rule and the exclusions (users created before coverage, users whose window is incomplete). With n under 30, report "2 of 4 users" and avoid percentages in headlines.
7. **Usage and value:** compare usage with MRR per account using the revenue output (for example zero-usage paying accounts and their MRR). This is a **co-occurrence**; label it PATTERN or HYP.
8. **Usage and renewal:** if churn events exist, describe the usage of churned accounts before churn **as observations**. With fewer than 5 churn events, write no generalisation (confidence cap Low).
9. **Propose experiments** for promising hypotheses: hypothesis, change, population, metric, minimum sample or duration, success threshold set in advance, and guardrail metrics. Example: "Guided report creation in onboarding raises 14-day activation; A/B on new users; needs about N users per arm (compute it, or state it as unknown)".
10. **Hand off** zero-usage accounts and usage drops to `customer-intelligence` (health) and `anomaly-hypothesis-validation` (sudden drops).

## Decision rules

- "Feature X users retain better" is a correlation. Selection effects (engaged customers use more features) are the default explanation until an experiment says otherwise.
- A sudden drop affecting all users, all events and all accounts at once is a data-collection explanation until disproven. Check it before reporting a usage decline.
- Do not compute activation for users whose observation window lies outside event coverage.
- Do not infer intent ("users are frustrated") from event data.
- Personal data: analyse by user ID and account ID only. Never put user names or emails in outputs.

## Output structure

```markdown
# Product intelligence: <client>, <month>
## 1. Data validity          (valid and invalid events, coverage, missing days)
## 2. Engagement             (MAU, active users by account)
## 3. Feature adoption       (feature | accounts | of paying | %; basis stated)
## 4. Under-used capabilities (low adoption features; plan entitlement if known)
## 5. Activation             (rule, cohort n, activated, rate, exclusions)
## 6. Usage and subscription value (zero-usage paying accounts with MRR; co-occurrence only)
## 7. Usage-related risks    (PATTERN or HYP with confidence)
## 8. Onboarding opportunities
## 9. Recommended experiments (hypothesis | design | metric | threshold | sample | guardrails)
## 10. Business implications and limitations
```

## Quality checks

- [ ] Numbers match the engine output. Cohort sizes are shown beside every rate.
- [ ] The adoption denominator is paying accounts, or is labelled otherwise.
- [ ] Coverage gaps are disclosed beside any trend.
- [ ] No causal claims. Search for "drives", "causes", "leads to" and "because of" and rewrite them.
- [ ] Every experiment has a threshold set in advance and a guardrail.
- [ ] No user-level personal data in the output.

## Failure and escalation conditions

- **Event coverage shorter than the requested analysis:** analyse the covered period only and state the limit.
- **Activation event not agreed:** report candidates and ask the product owner.
- **Events cannot be linked to accounts** (no user-to-account mapping): stop account-level work and request the mapping.
- **The request involves monitoring identifiable individuals** (for example ranking employees of a client's customer): decline and escalate.

## Examples

Synthetic fixture, June 2026, with the revenue output as input:

- Invalid events: 2 implausible timestamps (2099 and 1970), 1 unknown user (U999). Coverage 2026-04-01 to 2026-06-30, with 7 missing days (2026-05-11..17).
- MAU 17 [CALC:prod-mau-2026-06].
- Feature adoption over 8 paying accounts: dashboard_view 7 (87.5%), report_created 6 (75.0%), export_csv 3 (37.5%), alert_configured 3 (37.5%) [CALC:prod-adoption-2026-06].
- Zero usage: C006, which pays 250 USD MRR in June after contracting from 500 in May [CALC:prod-zero-usage-2026-06; rev-mrr-2026-06].
- Activation: 2 of 4 users in the cohort created 2026-04-01..2026-06-16 [CALC:prod-activation]. Small sample. 20 users were created before coverage and cannot be measured.

Good interpretation: "Alerts are used by 3 of 8 paying accounts. Only one churned account (C012) falls inside event coverage. C004 churned before events were recorded, so its usage is unknown, not zero. One observed account cannot support any conclusion about alerts and retention [Insufficient]. Experiment: prompt alert set-up during onboarding for new accounts, measuring 60-day activity."

Bad: "Accounts that configure alerts never churn, so alerts drive retention."

## Related skills

- Upstream: `data-readiness-assessment`, `cross-module-data-mapping`, `revenue-intelligence` (paying accounts and MRR), `business-metric-dictionary` (activation definition).
- Consumers: `customer-intelligence` (`account_usage`, zero-usage accounts), `anomaly-hypothesis-validation` (`weekly_events`), `bidim-opportunity-scoring`, `intelligence-report-builder`.
