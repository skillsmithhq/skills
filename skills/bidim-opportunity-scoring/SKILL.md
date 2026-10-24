---
name: bidim-opportunity-scoring
description: Scores and ranks BI and decision opportunities with the BIDIM matrix (impact, strategic fit, evidence confidence, effort, risk, data readiness, time to value) using a transparent formula, evidence guards, missing-value ranges and sensitivity checks, producing an opportunity register with rationale and next actions. Use when several findings or ideas compete for attention and need a defensible priority order.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# BIDIM opportunity scoring

## Purpose

Turn a list of findings and ideas into a priority order that a client can inspect, challenge and change. Every score has a written rationale and evidence. The ranking is produced by a script, not by judgement. Guards stop an opportunity from ranking highly just because it is described confidently.

**BIDIM is a prioritisation heuristic, not a financial valuation.** Full method: `references/bidim-framework.md`.

Shared rules (local copies): `references/bidim-framework.md`, `references/confidence-scoring.md`, `references/evidence-standards.md`, `references/opportunity.schema.json`.

## Activation conditions

Use when:

- the analysis skills have produced several opportunities or risks, and leadership must choose
- a roadmap (the AI and Analytics Roadmap) needs an ordered backlog
- someone asks "what should we do first?"
- a proposed initiative needs comparing against the evidence-backed alternatives

## Required inputs

| Input | If missing |
|---|---|
| Opportunities with a decision attached, a description and evidence IDs | An opportunity without a decision is not scored. Ask what decision it informs |
| Impact basis and bands, fixed before scoring (default: % of ARR) | Agree it with the user first. Never change the bands after scoring |
| The analysis outputs the evidence IDs refer to | Without them, evidence cannot be classed CALC or FACT, and the evidence guard caps confidence at 2 |

## Optional inputs

- Data readiness levels (from `data-readiness-assessment`) for D
- The decision inventory and stated objectives (from `client-discovery-synthesis`) for S
- Effort and risk views from client owners (record the role)

## Execution procedure

1. **Build the register** in the shape of `examples/opportunities.example.json` (schema: `references/opportunity.schema.json`). One entry per opportunity: id, title, the decision it informs, scores, a rationale **per score**, evidence (id and class), assumptions, missing evidence, owner and next action.
2. **Score each input on the scales** in `references/bidim-framework.md`:
   - **I** from a CALC impact basis (for example "9,600 ARR = 3.6% of ARR gives band 3"). With no basis, leave it `null`. Never guess.
   - **C** from `references/confidence-scoring.md`, with its reason.
   - **S** from stated objectives in discovery, citing the statement.
   - **E, R, T** with a stated basis, preferably from the client owner.
   - **D** from the readiness level of the data the opportunity depends on.
3. **Run** `python3 scripts/bidim_score.py <register.json>`. The script applies the evidence guard, the confidence-reason guard, the data gate, missing-value ranges, the tiebreak and the sensitivity check.
4. **Read the guard notes.** If a confidence was capped, the opportunity needs evidence gathering before investment. Say so; do not argue the cap away.
5. **Interpret the ranking with its labels:** `quick-win`, `strategic-bet`, `investigate-first`, `blocked-data`, `incomplete`, `rank-sensitive`.
6. **Discuss rank-sensitive items with the client.** Their position depends on a judgement call, so show which input would change it.
7. **Write next actions** per opportunity: who decides, what happens next, what evidence would change the score.
8. **Re-score when evidence changes,** keeping the history (date, changed input, reason).

## Decision rules

- No decision, no score.
- Impact without a CALC basis is `null`. The range is shown, and the item ranks on its lower bound.
- Persuasive language is not evidence. Confidence follows the evidence classes, enforced by the evidence guard.
- Data readiness ≤ 2 blocks an opportunity. Its first action is data remediation.
- Do not present the normalised score as a probability, a return on investment or a valuation.
- Do not compare BIDIM scores across clients.
- Use the scales as published. If the client wants different weights or bands, record the change and re-run everything.

## Output structure

```markdown
# Opportunity register and BIDIM prioritisation: <client> (<date>)
Impact basis: <basis and bands> | Formula: (I × C × S) / (E × R) | Heuristic, not a valuation

## 1. Priority ranking
| Rank | ID | Opportunity | Decision | I | C | S | E | R | D | T | Priority (or range) | Labels |

## 2. Scoring rationale (per opportunity: each input, its basis, evidence IDs)
## 3. Guard notes (caps applied, missing values)
## 4. Sensitivity (best and worst rank; rank-sensitive items and the inputs that drive them)
## 5. Missing evidence (per opportunity: what would change the score, and who holds it)
## 6. Recommended next actions (owner, action, timing)
```

## Quality checks

- [ ] Every input has a written rationale, and confidence has a reason.
- [ ] Every impact score cites a CALC basis, or is null.
- [ ] The table values equal the script output. No hand-calculated priorities.
- [ ] Guard notes are reported, not hidden.
- [ ] Rank-sensitive items are explained.
- [ ] The disclaimer (heuristic, not a valuation) appears with the ranking.

## Failure and escalation conditions

- **The client asks to "boost" a favoured initiative:** re-score it only on new evidence, and record the request.
- **Most opportunities are incomplete:** report that prioritisation is premature, and list the evidence needed.
- **An opportunity carries regulatory, safety or personal-data risk (R = 5):** flag it for the human owner whatever its rank.

## Examples

`examples/opportunities.example.json`, scored:

| Rank | ID | Priority | Labels | Note |
|---|---|---|---|---|
| 1 | OPP-01 Fix billing data gaps | 36.0 | quick-win | I = 3: 9,600 ARR = 3.6% of ARR |
| 2 | OPP-02 Staging cost guardrail | 12.0 | quick-win | Recurrence unproven, so C = 3 |
| 3 | OPP-03 Account review (C006) | 9.0 | quick-win, rank-sensitive | Rank 2–4 under ±1 changes |
| 4 | OPP-05 Onboarding alert experiment | 6.0 | investigate-first, rank-sensitive | Evidence guard: C 3 → 2 (only HYP and INTERP evidence) |
| 5 | OPP-04 Top-3 account programme | range 3.75–18.75 | incomplete | Impact not quantifiable from this data |
| 6 | OPP-06 AI churn prediction platform | 2.67 | blocked-data, investigate-first | Proposed with C = 5 and only INTERP evidence, so capped at 2; D = 2 blocks it |

Without the evidence guard, OPP-06's confident wording alone would lift its score from 2.67 to 6.67, above OPP-05. It still ranks last because the data gate (D = 2) blocks it. The two guards act independently: either one alone prevents a confidently described but unsupported idea from leading the list.

## Related skills

- Upstream: all analysis skills (evidence), `anomaly-hypothesis-validation` (tested explanations), `data-readiness-assessment` (D), `client-discovery-synthesis` (S).
- Consumers: `executive-decision-intelligence`, `intelligence-report-builder` (the BIDIM prioritisation section), `intelligence-quality-audit` (recomputes priorities from the stated inputs).
