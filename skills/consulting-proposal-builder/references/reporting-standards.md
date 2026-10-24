# Reporting standards

Canonical copy: `shared/references/reporting-standards.md`.

## 1. Required sections for intelligence reports

In this order. A section may say "Not in scope for this report" but must not be silently dropped.

1. Executive summary
2. Business context
3. Data sources
4. Methodology
5. Metric definitions
6. Key findings
7. Cross-module insights
8. Opportunities
9. Risks
10. Recommendations
11. BIDIM prioritisation
12. Limitations
13. Next steps

Appendix A: evidence register (IDs, class, source, method). Appendix B: exclusions and data-quality notes.

## 2. Finding format

```
### F-03 SMB accounts with contraction also show zero product usage
- What we found: ... [CALC:cust-health-c006] [CALC:prod-zero-usage-2026-06]
- Why it matters: ...
- Decision it informs: ...
- Possible actions: ...
- Expected impact: not quantified | USD ... per month at risk [CALC:...]
- Confidence: Low. Why: one account; association only.
- Missing information: ...
```

## 3. Writing rules

- Lead with the decision-relevant point, then the evidence.
- Every number carries an evidence ID. Round only for display, and state the unit and period ("USD 22,250 MRR at 2026-06-30").
- Use "associated with", "coincides with" or "observed in" for correlations. Reserve "caused", "drove" and "because" for findings with causal evidence, and cite that evidence.
- State sample sizes beside rates ("50% activation, n = 4").
- No superlatives without a CALC ("largest", "fastest").
- No guarantees, no promised returns, no investment advice.
- Name the definition used for disputed metrics (churn, CAC, LTV).
- Separate what the client said (quote, attributed by role) from our interpretation.
- Readers are executives: plain language, short paragraphs, tables for numbers. Put the technical method in Methodology and the appendices.

## 4. Audience framing

| Audience | Lead with | Typical decisions |
|---|---|---|
| CEO / Founder | Business health, growth, risk, where to invest | Prioritise, fund, stop |
| CTO | Technology cost, reliability, technical debt, platform ROI | Re-architect, optimise, build vs buy |
| CBO / Commercial | Revenue performance, expansion, conversion, account risk | Target, price, retain |
| Investor / Fund manager | Revenue quality, concentration, unit economics, scalability | Diligence questions, risk flags. Never buy/sell advice |

## 5. Traceability

Each material finding links to evidence IDs. Each evidence ID resolves to an entry in Appendix A that names its dataset, fields, filters, period and method. `intelligence-quality-audit` rejects a report where any ID fails to resolve.

## 6. Status labels

Every report shows one status on its cover: `DRAFT – not audited`, `AUDITED – needs revision`, or `AUDITED – approved for client by <role>`. Only a human may set the last status.
