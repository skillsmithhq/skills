---
name: operational-technology-intelligence
description: Analyses operational and technology economics (infrastructure and cloud cost, cost per customer and per transaction, support workload, reliability and downtime, resource utilisation, technical-debt implications) against revenue and activity, and frames cost-optimisation ideas as hypotheses with stated baselines and assumptions. Use when a CTO or COO question involves technology cost, efficiency, reliability or operational load.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Operational and technology intelligence

## Purpose

Connect what the business spends on technology and operations to what it serves (customers, transactions, revenue) and to how reliably it serves them. Optimisation ideas are **hypotheses**: every savings figure states its baseline, its assumptions and what would make it false.

Shared rules (local copies): `references/saas-metric-definitions.md` (OPS-1, OPS-2, SUP-1, SUP-2), `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`.

## Activation conditions

Use when the question involves:

- cloud or infrastructure spend, its trend and drivers
- cost per customer, per transaction or per active account
- support workload and resolution time as an operational cost
- reliability, incidents, downtime and their business exposure
- resource utilisation (idle, over-provisioned or non-production spend)
- whether technical debt is creating measurable cost or risk

## Required inputs

| Input | If missing |
|---|---|
| Cost data by month with environment and service (cloud bill export, finance cost lines) | Cannot analyse cost. Request it with the minimum fields: month, environment, service, cost, currency |
| `revenue-intelligence` output (MRR, active customers by month) | Report absolute costs only. Unit costs are `UNKNOWN` |
| Period and reporting currency | Ask |

## Optional inputs

- Transaction or usage volumes (for cost per transaction)
- Incident log (start, end, severity, affected service) for reliability
- Support tickets (from the validated mapping) for workload and resolution time
- Utilisation metrics (CPU, memory, storage) by resource
- Engineering time logs or estimates for technical-debt cost (an estimate must be labelled ASSUME)

## Execution procedure

1. **Check the cost data:** currencies (the engine skips lines in other currencies and counts them), duplicate lines, complete months, and environment labels. Treat credits and refunds as separate lines.
2. **Run the engine:** `python3 scripts/unit_costs.py --costs <costs.csv> --revenue <revenue.json> [--scenario <scenario.json>]`. Save the output.
3. **Describe cost structure and trend:** by environment and service, with month-over-month changes. Separate production from non-production.
4. **Unit costs:** cost per active customer (all environments and production only) and the cost-to-MRR ratio. **Never call the ratio gross margin.** Gross margin needs the full cost of revenue.
5. **Hand unusual movements** (for example a month-over-month jump) to `anomaly-hypothesis-validation`. Do not explain them by assertion.
6. **Support workload:** tickets per active account, median resolution time (exclude tickets with invalid intervals and report how many), and workload per segment if needed.
7. **Reliability** (if there is an incident log): minutes of downtime by service, incidents by severity, and customers or revenue exposed. Use revenue exposure only through validated account-to-service relationships.
8. **Build optimisation hypotheses.** Each one needs a baseline month, the cost lines affected, assumptions, a saving computed by the engine's scenario (never mental arithmetic), risks (performance, reliability) and a validation step. Use `examples/staging-scenario.json` as the format.
9. **Implementation considerations:** owners, effort, reversibility, monitoring needed, and whether savings recur.
10. **Technical debt:** connect it to measured cost or risk (incident frequency in a component, support tickets by category). Without measurement, technical debt is an `INTERP` and is not scored as impact.

## Decision rules

- No savings estimate without a baseline month, specific cost lines and written assumptions. The engine refuses a scenario with no assumptions.
- Annualise a saving only when the baseline lines would recur. Say why you believe they would.
- The cost-to-MRR ratio is not gross margin, contribution margin or profitability.
- Cost allocation to customers requires a stated allocation method. Without one, report company-level unit costs only.
- Utilisation-based rightsizing recommendations need utilisation data over a representative period (default: at least 30 days including peaks).
- Never recommend changes to production systems as fact. Recommendations go to the client's engineering owner for decision.

## Output structure

```markdown
# Operational and technology intelligence: <client>, <period>
## 1. Operational metrics      (support workload, resolution time, reliability if available)
## 2. Technology cost analysis (monthly by environment and service; MoM changes)
## 3. Unit costs               (per active customer; production only; ratio to MRR, not gross margin)
## 4. Unusual movements        (handed to anomaly-hypothesis-validation; result if returned)
## 5. Efficiency opportunities (HYP: baseline | lines | assumptions | saving (engine) | risks | validation)
## 6. Potential risks          (reliability, concentration of spend, vendor lock-in where evidenced)
## 7. Cost optimisation hypotheses
## 8. Implementation considerations (owner, effort, reversibility, recurrence, monitoring)
## 9. Limitations              (what cost of revenue excludes; data gaps)
```

## Quality checks

- [ ] Every cost figure matches the engine output.
- [ ] No "gross margin" or "profitability" wording attached to the infrastructure ratio.
- [ ] Every saving has a baseline, assumptions and an engine calculation.
- [ ] Production and non-production costs are shown separately.
- [ ] Movements are explained only with evidence (decomposition, hypothesis tests), not assertion.
- [ ] Recurrence is justified for any annualised figure.

## Failure and escalation conditions

- **Cost data in several currencies with no FX table:** analyse per currency, or request an approved FX source.
- **No environment or service breakdown:** analyse the total only, and state that drivers cannot be identified.
- **Requests for guaranteed savings or a vendor recommendation:** give hypotheses with validation steps. No guarantees, no vendor endorsements.
- **Access to cloud consoles or production systems requested:** require written approval and read-only access (`references/data-security-principles.md`). Prefer the billing exports.

## Examples

Synthetic fixture, linked to the revenue output:

| Month | Total | Production | Staging | Per active customer | Ratio to MRR |
|---|---|---|---|---|---|
| 2026-04 | 10,300 | 10,300 | 0 | 1,144.44 | 43.46% |
| 2026-05 | 14,500 | 10,200 | 4,300 | 1,611.11 | 61.83% |
| 2026-06 | 10,400 | 10,400 | 0 | 1,300.00 | 46.74% |

Finding: the May increase (+4,200 against April) sits entirely in staging compute, and production was 100 lower [CALC:ops-cost-2026-05]. Explanation tested in `anomaly-hypothesis-validation`.

Hypothesis (from `examples/staging-scenario.json`): if the 4,300 USD staging compute line in May was a load-test cluster left running, stopping such clusters between tests would avoid 4,300 USD in any month where it recurs. Not annualised: staging appears in 1 of 6 months, so recurrence is unproven. Validation: confirm with the platform team and add a cost alert on staging.

Limitation: a 46.74% infrastructure-to-MRR ratio is high, but it is not gross margin. Support staff and third-party costs are unknown.

## Related skills

- Upstream: `revenue-intelligence` (MRR, active customers), `cross-module-data-mapping` (support and account links), `data-readiness-assessment`.
- Parallel: `anomaly-hypothesis-validation` tests cost movements.
- Consumers: `bidim-opportunity-scoring`, `executive-decision-intelligence` (CTO perspective), `intelligence-report-builder` (Technology Intelligence Report).
