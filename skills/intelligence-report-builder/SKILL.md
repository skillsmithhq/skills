---
name: intelligence-report-builder
description: Assembles professional intelligence deliverables (BI Opportunity Assessment, Executive, Revenue, Customer, Product and Technology Intelligence Reports, AI and Analytics Roadmap) with the 13 standard sections, a BIDIM table and an evidence appendix, refusing to build when any cited evidence ID does not trace to an upstream output. Use when analysis is complete and a client-ready report draft is needed.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Intelligence report builder

## Purpose

Package verified analysis into a report an executive can read in ten minutes and an analyst can verify line by line. The narrative is written by the analyst or agent. The assembly script enforces structure and **traceability**: every evidence tag must resolve to an upstream artefact or a sourced evidence item, or the report is not built.

Reports leave this skill as `DRAFT – not audited`. The next step is always `intelligence-quality-audit`.

Shared rules (local copies): `references/reporting-standards.md` (sections, finding format, writing rules), `references/evidence-standards.md`, `references/bidim-framework.md`, `references/saas-metric-definitions.md`.

## Activation conditions

Use when:

- analysis outputs exist and a deliverable is due
- the user asks for an assessment, a report, an executive summary or a roadmap document
- an audited report needs revising after audit findings

## Required inputs

| Input | If missing |
|---|---|
| Upstream artefacts (JSON outputs with `evidence` arrays) | Cannot build. Never write findings from memory of the analysis |
| Report type, audience and period | Ask. Default type: BI Opportunity Assessment |
| Narrative per section and the findings (written in the spec) | Draft them from the artefacts, citing evidence IDs, then build |

## Optional inputs

- The BIDIM output (renders the prioritisation table)
- Decision briefs from `executive-decision-intelligence` (Recommendations section)
- Extra evidence items (client statements as FACT, interpretations as INTERP), each with a source
- An earlier audit result, so corrections can be tracked

## Execution procedure

1. **Choose the report type:** BI Opportunity Assessment, Executive Intelligence Report, Revenue, Customer, Product or Technology Intelligence Report, or AI and Analytics Roadmap. A single-domain report keeps all 13 sections; sections outside its scope say "Not in scope for this report".
2. **Write the spec** in the shape of the collection's `fixtures/report_inputs/report_spec.json`: artefacts, extra evidence (with sources), section narratives, findings (the eight-question format in `references/reporting-standards.md`) and claims (the numeric claims with their artefact paths, for the audit).
3. **Write with discipline.** Every sentence that contains a number carries an evidence tag. Use association language. State the window and sample size beside rates. Put interpretations in INTERP items that give an alternative reading. Name the definitions used.
4. **Assemble:** `python3 scripts/assemble_report.py <spec.json> --out <dir>`. It writes `report.md`, `evidence_register.json` and `claims.json`. It fails, listing the IDs, if any tag does not resolve or its class does not match.
5. **Self-check** against `templates/report-checklist.md` before handing over.
6. **Hand to `intelligence-quality-audit`** with the artefacts, `claims.json` and `evidence_register.json`. Fix, re-assemble and re-audit until the verdict is pass. Approval is a human decision.

## Decision rules

- No tag, no number. No artefact, no tag.
- Do not soften or drop limitations to make the report read better.
- The executive summary may only contain what the findings contain.
- Do not remove a section because it is empty. Write "Not in scope for this report", or state what is missing.
- Report types differ in emphasis, not in standards. A Product Intelligence Report still needs data sources, methodology and limitations.
- Status stays `DRAFT – not audited` until an audit has run. Only a human writes "approved".

## Output structure

`report.md` with:

1. Executive summary
2. Business context
3. Data sources
4. Methodology
5. Metric definitions
6. Key findings (F-xx in the finding format)
7. Cross-module insights
8. Opportunities
9. Risks
10. Recommendations
11. BIDIM prioritisation (table from the BIDIM artefact, with the heuristic disclaimer)
12. Limitations
13. Next steps

Appendix A: evidence register (every cited ID, its class, statement and producer). Alongside it: `evidence_register.json` and `claims.json`.

## Quality checks

- [ ] The assembler succeeded (traceability enforced).
- [ ] Every finding answers the eight questions or says why one is not applicable.
- [ ] Limitations include the data exclusions, window lengths, sample sizes and metrics that could not be calculated.
- [ ] `claims.json` covers every headline number.
- [ ] The audit verdict is pass before anyone outside the team sees the report.

## Failure and escalation conditions

- **Traceability failure:** fix the tag or the claim. Never invent an evidence item to make the build pass.
- **Upstream artefacts are older than the latest data:** re-run the pipeline first.
- **Audit failed:** correct and re-audit. Do not release a partially corrected report.
- **The audience requests removal of a limitation or risk:** escalate to the engagement owner. Record the request.

## Examples

Build the synthetic example from the repository root:

```
python3 tools/run_pipeline.py
python3 skills/intelligence-report-builder/scripts/assemble_report.py fixtures/report_inputs/report_spec.json --out <dir>
```

The result has 13 sections, 4 findings, a 6-row BIDIM table and 27 cited evidence items. An excerpt:

> ### F-02 Three customers hold most of the revenue
> - **What we found:** The top-3 customers are 80.90% of June MRR and C009 alone is 31.46% [CALC:rev-concentration].
> - **Confidence:** High for the measurement; likelihood of loss not measured.

If the spec cites `[CALC:rev-ltv]`, which no artefact produces, the build stops with `"unresolved_ids": ["rev-ltv"]`.

## Related skills

- Upstream: all analysis skills, `bidim-opportunity-scoring`, `executive-decision-intelligence`, `business-metric-dictionary` (the Metric definitions section).
- Next: `intelligence-quality-audit` (required before release).
- `consulting-proposal-builder` defines which report types were sold as deliverables.
