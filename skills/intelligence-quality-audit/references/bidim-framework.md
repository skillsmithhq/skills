# BIDIM: Business Intelligence & Decision Intelligence Matrix

Canonical copy: `shared/references/bidim-framework.md`. Scoring script: `bidim-opportunity-scoring/scripts/bidim_score.py`.

BIDIM is a **prioritisation heuristic**. It orders opportunities for discussion. It is not a financial valuation, a forecast or an investment recommendation.

## 1. Inputs and scales (integers 1–5)

| Input | Symbol | 1 | 2 | 3 | 4 | 5 | Evidence required |
|---|---|---|---|---|---|---|---|
| Financial impact | I | < 0.5% of ARR per year, or not quantifiable | 0.5–2% | 2–5% | 5–10% | > 10% | A CALC giving the impact basis. If no basis exists, leave I missing; do not guess |
| Strategic fit | S | No link to stated objectives | Indirect link | Supports a stated objective | Directly serves a top-3 stated objective | Top-3 objective, and leadership named it as a decision this quarter | Discovery output (decision inventory) |
| Evidence confidence | C | Insufficient | Low | Medium | High | Very high | Levels from `confidence-scoring.md` |
| Implementation effort | E | ≤ 1 person-week | ≤ 1 month | ≤ 1 quarter | ≤ 2 quarters | > 2 quarters or a new platform | Stated basis, for example "needs 2 new data sources" |
| Business risk | R | Negligible | Minor, reversible | Moderate | Significant (customer-facing or financial) | Severe (regulatory, irreversible, safety) | Named risks |
| Data readiness | D | Data unusable | Major remediation first | Usable with caveats | Minor issues | Ready | `data-readiness-assessment` suitability |
| Time to value | T | < 2 weeks | < 1 month | < 1 quarter | < 2 quarters | Longer | Stated basis |

The impact bands are defaults. An engagement may set absolute bands (for example USD thresholds) instead, recorded in the opportunity register header. Bands must be fixed **before** scoring.

## 2. Formula

```
Priority = (I × C × S) / (E × R)
```

- Range: 1/25 = 0.04 up to 125.
- Normalised score = Priority / 125 × 100, rounded to 1 decimal place.
- Data readiness and time to value are **not** in the formula. They act as gates and tiebreakers, so they are not double-counted against effort.

## 3. Gates and guards (applied in this order)

1. **Evidence guard.** If an opportunity has no evidence item of class `CALC` or `FACT`, C is capped at 2, whatever the value proposed. Persuasive wording does not raise C.
2. **Confidence-reason guard.** A C value without a written reason is treated as missing.
3. **Data gate.** If D ≤ 2, status is `blocked-data`: the opportunity is ranked after every unblocked one and its next action is remediation.
4. **Missing values.** A missing input is never imputed silently. The script computes the priority range by setting the missing inputs to their least favourable value (I, C, S = 1; E, R = 5) and their most favourable value (I, C, S = 5; E, R = 1). Opportunities are ranked on the **lower bound** and flagged `incomplete`.
5. **Tiebreak.** Equal priority: shorter time to value first, then higher confidence, then ID.

## 4. Sensitivity check

For each opportunity, each of I, C, S, E and R is moved by ±1 (kept within 1–5), one input at a time, with every other opportunity held fixed. Record the best and worst rank reached. If the rank moves by more than one place, flag it `rank-sensitive`. That means the ordering depends on a judgement call that must be discussed with the client, not presented as settled.

## 5. Labels

| Label | Rule |
|---|---|
| `quick-win` | Unblocked, complete, E ≤ 2, T ≤ 2 and C ≥ 3 |
| `strategic-bet` | Unblocked, I ≥ 4 and S ≥ 4 and E ≥ 4 |
| `investigate-first` | C ≤ 2 (the next action is evidence gathering, not implementation) |
| `incomplete` | One or more of I, C, S, E, R missing; ranked on the lower bound |
| `rank-sensitive` | Rank moves more than one place under the ±1 sensitivity check |
| `blocked-data` | D ≤ 2 |

## 6. Opportunity register fields

See `references/opportunity.schema.json`. Each entry needs: id, title, description, the decision it informs, the scores above with a rationale per score, evidence IDs, assumptions, missing evidence, owner, and the next action.

## 7. Misuse to avoid

- Presenting the normalised score as a probability or a return on investment.
- Changing scales after seeing the results.
- Comparing BIDIM scores across different clients.
- Scoring an opportunity that has no decision attached. If no one would decide anything differently, it is not an opportunity.
