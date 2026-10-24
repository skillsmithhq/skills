---
name: executive-decision-intelligence
description: Translates verified analysis and BIDIM priorities into decision briefs for a CEO or founder, CTO, CBO or commercial lead, or investor, each stating the decision, evidence, impact, confidence, alternatives, risks, dependencies, next action and measurement, with no guarantees, investment advice or unsupported predictions. Use when findings must become decisions for a specific leadership audience.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Executive decision intelligence

## Purpose

Leaders do not need more metrics. They need to know **which decision is in front of them**, what the evidence says, how sure we are, and what the options are. This skill reframes verified outputs for one audience at a time, without adding claims the evidence does not support.

It never creates new numbers. Every figure comes from an upstream artefact's evidence.

Shared rules (local copies): `references/reporting-standards.md` (audience framing), `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/bidim-framework.md`, `references/saas-metric-definitions.md`.

## Activation conditions

Use when:

- an assessment's analysis is complete and leadership needs recommendations
- the user asks "what should the CEO / CTO / CBO / investor take from this?"
- a board pack, leadership offsite or diligence meeting needs decision framing
- BIDIM ranking exists and needs converting into decisions per owner

## Required inputs

| Input | If missing |
|---|---|
| Verified outputs from the analysis skills (with evidence arrays) | Cannot write briefs. Do not summarise from memory or from draft notes |
| Audience (CEO, CTO, CBO, Investor) | Ask, or produce one section per audience |
| BIDIM output, when there are several competing opportunities | Briefs may be written, but must not imply a priority order |

## Optional inputs

- Decision inventory from discovery (decisions leadership already named)
- Audit results for upstream outputs (use only passed or corrected items)
- Known constraints: budget, capacity, timing

## Execution procedure

1. **Collect the evidence register** from the artefacts consumed, and list them in the envelope inputs.
2. **Choose the decisions per audience** (see `references/reporting-standards.md`, section 4):
   - **CEO / Founder:** growth, business health, strategic opportunities, risk, investment priorities
   - **CTO:** technology ROI, infrastructure cost, reliability, architecture, technical debt, platform investment
   - **CBO:** revenue performance, sales efficiency, expansion, commercial operations, conversion, customer profitability (only if assessed)
   - **Investor / Fund manager:** revenue quality, growth sustainability, unit economics (only those calculable), concentration, scalability, portfolio risk. The output is **diligence questions and risk flags, never buy/sell/hold advice**
3. **Write each recommendation** in `templates/decision-brief.md` form, or as JSON like `examples/decision-briefs.example.json`. Every recommendation needs:
   - decision required
   - evidence (IDs and classes)
   - business impact (quantified only from CALC, otherwise "not quantified")
   - confidence (level and reason)
   - alternatives (including doing nothing or deferring)
   - risks and dependencies
   - suggested next action (owner role and timing)
   - measurement criteria
4. **Lint:** `python3 scripts/decision_brief_lint.py <briefs.json> --evidence <artefact.json> ...`. It blocks missing fields, promise language, investment advice, unsupported confidence and evidence IDs that do not resolve.
5. **Order the briefs** by BIDIM rank where one exists. Otherwise order by decision urgency stated by the client, and say which ordering was used.
6. **State what is not known.** For each audience, list the decisions that cannot be supported yet (for example CAC payback: no spend data).

## Decision rules

- No new numbers. If a figure is not in an upstream evidence item, it does not appear.
- No guarantees, promised returns, valuations, price targets, or buy/sell/hold advice.
- No predictions beyond what the evidence supports. Exposure ("31.46% of MRR is one customer") is not likelihood ("this customer will leave").
- Confidence cannot exceed the supporting evidence (enforced by the lint).
- Every recommendation offers at least one alternative, including doing nothing or deferring.
- Sensitive decisions (layoffs, pricing that affects individuals, legal exposure) are flagged for the human owner. This skill frames them; it does not recommend them.

## Output structure

```markdown
# Decision brief: <client>, <audience>, <date>
## Decisions in front of you (ordered; ordering basis stated)
### R-01 <decision>
- Evidence: ...
- Business impact: ...
- Confidence: <level>. Why: ...
- Alternatives: ...
- Risks: ...
- Dependencies: ...
- Suggested next action: <owner role, timing>
- How we will know: <measurement>
## Decisions we cannot yet support (and the data needed)
```

## Quality checks

- [ ] The lint reports 0 blocking issues.
- [ ] Every number traces to an evidence ID from an upstream artefact.
- [ ] The investor section contains questions and risk flags only.
- [ ] Each brief's ordering basis is stated.
- [ ] "Decisions we cannot yet support" is present.
- [ ] No causal claim beyond the anomaly or hypothesis statuses.

## Failure and escalation conditions

- **Upstream outputs failed audit:** do not brief on the failed items.
- **The audience asks for a forecast or valuation:** decline the number. Offer the drivers, assumptions and data needed.
- **The evidence conflicts across artefacts:** surface the conflict to the analyst before briefing.
- **The decision affects individuals' employment or pay:** escalate to the human owner.

## Examples

From `examples/decision-briefs.example.json` (synthetic fixture):

- **CEO, R-01:** whether to treat revenue concentration as a board-level risk. Top 3 customers are 80.90% of MRR [CALC:rev-concentration]. High confidence for exposure; likelihood of loss not measured. Alternatives: an account programme, diversification, or monitoring only.
- **CTO, R-02:** whether to add non-production budget alerts. Staging accounts for 4,300 USD of the 4,200 USD May increase [CALC:ops-cost-2026-05]. Medium confidence until the platform team confirms.
- **Investor, R-04:** diligence questions: 12-month cohort retention (current NRR is 93.26% over a 5-month window [CALC:rev-nrr]), and top-3 contract terms.

Bad: "Investors should buy in at the current valuation; NRR will grow to 110% once account management is in place." (Investment advice, and an unsupported prediction.)

## Related skills

- Upstream: `bidim-opportunity-scoring`, `revenue-intelligence`, `customer-intelligence`, `product-intelligence`, `operational-technology-intelligence`, `anomaly-hypothesis-validation`.
- Next: `intelligence-report-builder` (the Recommendations section), then `intelligence-quality-audit`.
