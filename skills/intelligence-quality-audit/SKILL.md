---
name: intelligence-quality-audit
description: Independently reviews intelligence reports and analytical outputs by recomputing figures from upstream artefacts, re-reading key metrics from the text rather than trusting the claims file, and checking traceability, joins, causal language, statistical limits, BIDIM consistency, privacy, contradictions and missing caveats, returning pass, needs-revision or fail with required corrections. Use before any report or analysis output is shared outside the team.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Intelligence quality audit

## Purpose

Act as the sceptical reviewer the other skills cannot be for themselves. The audit **starts from the assumption that the report may be wrong** and looks for evidence that it is. It recomputes figures from the upstream artefacts. It re-reads headline metrics from the text itself, so a mislabelled number cannot hide behind a correct claims file. And it checks the non-numeric failure modes: causal leaps, missing caveats, privacy leaks and unsupported recommendations.

A pass is a recommendation for human approval, never an approval.

Shared rules (local copies): `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/reporting-standards.md`, `references/bidim-framework.md`, `references/saas-metric-definitions.md`, `references/data-security-principles.md`, `references/audit-result.schema.json`.

## Activation conditions

Use when:

- a report from `intelligence-report-builder` is ready for review
- any analysis output (revenue, customer, BIDIM, decision briefs) is about to be shared
- a client disputes a number
- after corrections, for the re-audit

## Required inputs

| Input | If missing |
|---|---|
| The report or output to audit | Cannot audit |
| The upstream artefacts it relies on (JSON outputs) | Calculation checks are impossible. The verdict cannot be better than needs-revision, and the audit must say "figures not verified" |
| `claims.json` and `evidence_register.json` from the report builder | The independent text scan and traceability still run. Claim-level recomputation is skipped and reported |

## Optional inputs

- The cross-module map (to check that joins used in findings were validated)
- The metric dictionary (to check definitions and calculability)
- Readiness output (to check that limitations were disclosed)
- An earlier audit (to confirm that corrections were made)

## Execution procedure

1. **Run the automated audit:**
   `python3 scripts/audit_report.py <report.md> --artefact revenue=<path> --artefact customer=<path> --artefact product=<path> --artefact bidim=<path> [...] --claims <claims.json> --evidence-register <evidence_register.json>`.
   Supply every artefact the report cites. The script fails claims it cannot resolve.
2. **Read the issues by severity.** Critical: wrong numbers, unresolved evidence, privacy leaks, BIDIM inconsistencies. Major: uncited numbers, causal wording, missing sections, calculability, contradictions. Minor: missing caveats. Causal flags are deliberately strict; judge each one, but resolve it rather than ignore it.
3. **Manual review: what the script cannot see.** Use `templates/audit-checklist.md`:
   - **Incorrect joins:** does a finding combine modules through a relationship that `cross-module-data-mapping` rated Low, or did not validate?
   - **Statistical limits:** small samples, short windows, comparisons with fewer than 5 events, significance claims without tests.
   - **Forecasts and projections:** stated assumptions, and confidence no higher than Medium.
   - **Recommendation feasibility:** owner, dependencies, effort basis; nothing that needs production access or credentials without approval.
   - **Scope honesty:** exclusions, metrics that could not be calculated, data gaps, all disclosed in Limitations.
   - **Confidentiality:** no other client's data; aggregation level appropriate for the audience.
   - **Interpretations:** labelled, with an alternative reading.
4. **Spot-check calculations** that the script did not cover, by tracing at least three further numbers to their artefacts.
5. **Decide the verdict.** **Fail** if any critical issue (from the script or the manual review). **Needs revision** if any major issue. **Pass** otherwise. Record the manual findings in the same issue format.
6. **Write required corrections** per issue: what to change and how to verify it.
7. **Re-audit after corrections.** Confirm each earlier issue is resolved; do not only check new text.

## Decision rules

- Never upgrade a verdict because the report is "mostly right" or the deadline is close.
- A number that cannot be recomputed is unverified, not "probably fine".
- A correct number with the wrong scope (segment NRR presented as company NRR) is a critical calculation error.
- Causal language without a causal design is at least a major issue.
- Any personal data, credential or other-client data is critical, whatever its size.
- The auditor does not fix the report. It states the corrections. The report owner makes them.
- The auditor may audit its own team's work, but must not have written the report it audits in the same session without saying so.

## Output structure

JSON (schema: `references/audit-result.schema.json`) plus a narrative:

```markdown
# Quality audit: <report> (<date>)
Verdict: PASS | NEEDS REVISION | FAIL
Automated checks: <n> calculation checks, <n> matched | Manual review: done by <role>

## Critical issues
## Major issues
## Minor issues
## Unsupported claims    (text, location, why unsupported)
## Calculation checks    (claim | stated | recomputed | match)
## Required corrections  (issue → change → how to verify)
## Final approval recommendation
```

## Quality checks

- [ ] The script ran with every artefact the report cites.
- [ ] The manual checklist is completed, including joins and statistical limits.
- [ ] At least three numbers beyond the script's coverage were traced by hand.
- [ ] Every issue has a location and a required correction.
- [ ] The verdict follows the rules; there are no exceptions without a written reason from the engagement owner.
- [ ] The final recommendation never says "approved". Approval belongs to a named human role.

## Failure and escalation conditions

- **Artefacts are missing or inconsistent with each other:** the verdict cannot be pass. Escalate to the analyst.
- **Possible misconduct** (numbers deliberately altered, limitations removed on request): escalate to the engagement owner.
- **A privacy breach in a shared draft:** escalate immediately. Recall the draft where possible.
- **The audit itself is challenged:** re-run with the challenger present, and record both views.

## Examples

**Deliberately flawed report** (the collection's `fixtures/flawed_report/`): verdict **FAIL**, with 6 critical, 2 major and 2 minor issues:

| Severity | Issue |
|---|---|
| critical | "Net revenue retention was 112.5%": recomputed company NRR is 93.26%. 112.5% is Enterprise-only (caught both from `claims.json` and by the independent text scan) |
| critical | "13 customers" matches neither active customers (8) nor de-duplicated entities (12). The duplicate C013 was not merged |
| critical | Email address in the Recommendations section |
| critical | OPP-01 priority stated 60.00; its own inputs give 45.0, and the BIDIM output says 36.0 (two findings) |
| major | "alert configuration drives retention": causal wording, with 2 churn events and no experiment |
| major | "Churn fell to 2% last quarter": no evidence |
| minor | NRR without a window label; "Confidence: High" without a reason |

Accepted as correct: MRR USD 22,250 and growth 3.49% (recomputed, matched).

**The correct example report** (built from `fixtures/report_inputs/report_spec.json`): verdict **PASS**, with all calculation checks matched. Recommendation: human review and approval.

## Related skills

- Upstream: `intelligence-report-builder` (report, claims, evidence register) and every analysis skill (artefacts).
- Feeds back to: `intelligence-report-builder` (corrections) and the engagement owner (approval decision).
- Also audits `executive-decision-intelligence` briefs (use its lint first), `bidim-opportunity-scoring` registers and `market-opportunity-research` reports (manual checklist only).
