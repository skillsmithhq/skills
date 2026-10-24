# SaaS metric definitions (defaults and variants)

Canonical copy: `shared/references/saas-metric-definitions.md`.

These are **default** definitions, not universal truths. For each client, `business-metric-dictionary` records which definition was chosen, who approved it and why. Every calculation cites the definition ID it used (for example `MRR-1`).

All money amounts are in one reporting currency per engagement. Never add amounts in different currencies without an approved FX table, and record the FX source and date when you convert.

## Recurring revenue

| ID | Metric | Default definition | Common variants (record which one) |
|---|---|---|---|
| MRR-1 | MRR | Sum of the normalised monthly recurring amount of every subscription active at the period end. Active means `start_date <= period_end` and (`end_date` is empty or `end_date > period_end`). Excludes one-off fees, usage overages, taxes and credits | Active at period start; average daily MRR; includes contracted-but-not-started; net of discounts or gross |
| ARR-1 | ARR | MRR-1 × 12 at the same period end | Sum of annual contract values; excludes monthly plans |
| MOV-1 | MRR movements | For each customer, compare MRR at the previous period end with MRR at this period end. **New**: previous 0, current > 0, and the customer never had MRR before. **Reactivation**: previous 0, current > 0, and the customer had MRR before. **Expansion**: current > previous > 0. **Contraction**: 0 < current < previous. **Churn**: previous > 0, current 0 | Subscription-level rather than customer-level movement |
| GROWTH-1 | Revenue growth | (MRR end − MRR start) / MRR start for a stated period | Compound monthly growth; year over year |

## Retention

| ID | Metric | Default definition | Variants |
|---|---|---|---|
| NRR-1 | Net revenue retention | Cohort = customers with MRR > 0 at the start date. NRR = cohort MRR at the end date / cohort MRR at the start date. Equals (start + expansion − contraction − churn) / start. New customers are excluded | Trailing 12-month standard; monthly NRR compounded |
| GRR-1 | Gross revenue retention | Same cohort. GRR = (start − contraction − churn) / start. Expansion is ignored, so GRR ≤ 100% | Capped per customer at their start MRR |
| CHURN-L1 | Customer (logo) churn | Customers in the start cohort with MRR 0 at the end date, divided by the cohort size | Monthly average; includes paused customers |
| CHURN-R1 | Gross revenue churn | (Contraction + churned MRR) / start MRR, same cohort | Churn only, without contraction |

Label the period. NRR measured over fewer than 12 months is labelled for example "NRR (Jan–Jun, 5-month window)" and is not compared with 12-month benchmarks.

## Revenue quality and collections

| ID | Metric | Default definition |
|---|---|---|
| ARPA-1 | Average revenue per account | MRR-1 / number of customers with MRR > 0 at the same period end. Customers are de-duplicated entities, not raw rows |
| CONC-1 | Customer concentration | The largest customer's share of MRR, and the top-3 share. Report both |
| RECUR-1 | Recurring share | Recurring invoiced amount / total invoiced amount over the period, after removing duplicate and void invoices |
| COLL-1 | Collection rate | Paid amount / invoiced amount for invoices issued in the period, measured at a stated as-of date |
| AR-1 | Outstanding receivables | Sum of unpaid, non-void invoice amounts at the as-of date. Overdue = outstanding and `due_date < as_of` |

## Unit economics (strict prerequisites)

| ID | Metric | Default definition | Do not calculate when |
|---|---|---|---|
| GM-1 | Gross margin | (Revenue − cost of revenue) / revenue. Cost of revenue covers hosting, third-party services, and support and onboarding staff serving customers | Cost-of-revenue data is incomplete. Infrastructure cost alone is not cost of revenue: report "infrastructure cost ratio" instead (OPS-2) |
| CAC-1 | Customer acquisition cost | Sales and marketing spend in the period / new customers acquired in the period. State whether spend is lagged | Spend data is unavailable. Never approximate it from headcount guesses |
| LTV-1 | Lifetime value | ARPA × gross margin % / monthly revenue churn rate | Gross margin is unavailable, churn is measured over fewer than 12 months, or there are fewer than 30 churn events. Report "LTV not calculable" with the reason |
| PAYBACK-1 | CAC payback | CAC / (ARPA × gross margin %) in months | Same prerequisites as CAC-1 and GM-1 |

## Product

| ID | Metric | Default definition |
|---|---|---|
| ACT-1 | Activation rate | Share of users created in a cohort window who perform the activation event (agreed per client, for example first report created) within N days (default 14) of creation. Only users whose full N-day window lies inside event-data coverage are counted |
| MAU-1 | Monthly active users | Distinct users with at least one valid event in the calendar month. Events with invalid timestamps or unknown users are excluded and counted separately |
| ADOPT-1 | Feature adoption (account level) | Share of paying accounts (MRR > 0 at month end) with at least one event of the feature in the month |
| ZERO-1 | Zero-usage paying accounts | Paying accounts with no valid events in the month |

## Operations and technology

| ID | Metric | Default definition |
|---|---|---|
| OPS-1 | Infrastructure cost per active customer | Infrastructure cost for the month / customers with MRR > 0 at month end. State whether non-production environments are included |
| OPS-2 | Infrastructure cost ratio | Infrastructure cost for the month / MRR at month end. Not a gross margin |
| SUP-1 | Support burden | Tickets per paying account per period, after resolving ticket customer references to de-duplicated customer entities. Report unresolvable tickets separately |
| SUP-2 | Resolution time | Median hours from `created_at` to `resolved_at` for resolved tickets with valid timestamps (resolved after created) |

## Entity rules that affect every metric

1. Count customers as de-duplicated **entities**. Record the entity-resolution map (which raw IDs were merged and why) in the cross-module map.
2. Exclude a record from a calculation only for a documented reason. Report the excluded count and amount next to the result.
3. Normalise currency codes only for case or whitespace (`usd` becomes `USD`). Anything that is not a valid ISO 4217 code (`US$`, `XXX`, blank) is excluded and reported, not guessed.
4. Store timestamps in UTC. Record the client's reporting timezone in the metric dictionary. Period boundaries use the reporting timezone.
