---
name: consulting-proposal-builder
description: Drafts a commercial proposal for a BI assessment or advisory engagement, covering context, scope, deliverables, timeline, client responsibilities, data request, exclusions, pricing assumptions, acceptance criteria and risks, without inventing prices, guarantees or testimonials. Use when turning discovery findings into a proposal, statement of work or engagement letter draft.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# Consulting proposal builder

## Purpose

Produce a clear, honest proposal that a client can say yes or no to. The proposal must make scope, responsibilities and limits explicit, so the engagement can be delivered as written.

This skill drafts commercial text. A human sets the price, approves the commitments and sends the proposal. The draft is never sent automatically.

Shared rules (local copies): `references/evidence-standards.md`, `references/reporting-standards.md`, `references/data-security-principles.md`.

## Activation conditions

Use when:

- a discovery synthesis exists and the user asks for a proposal, SOW, quote or engagement outline
- an existing proposal needs revising after client feedback
- the user wants a standard offer (for example a fixed-scope BI Opportunity Assessment) adapted for a prospect

## Required inputs

| Input | If missing |
|---|---|
| Client context: the discovery output from `client-discovery-synthesis`, or equivalent notes | Ask for it. A proposal without discovery must be labelled "pre-discovery outline" and must not state client problems as facts |
| Pricing inputs from the user: fee or rate, currency, payment terms | Leave `[PRICE: to be set by <owner>]` placeholders. Never invent a price or "typical market rate" |
| Engagement type: assessment, advisory retainer or report | Default to "BI Opportunity Assessment" and mark it `ASSUME` |

## Optional inputs

- The user's standard terms, rate card or past proposal template
- Preferred timeline and team roles
- Client procurement requirements (format, security questionnaire)

## Execution procedure

1. **Check the basis.** Confirm that the discovery output exists and note its date. List the client statements the proposal relies on by statement ID.
2. **Write the context and problem** using only the client's stated objectives and problem statements. Attribute them ("You told us that ...").
3. **Define the engagement.** Pick the engagement shape and phases. A typical assessment runs: kick-off and access; data inventory and readiness; metric definitions; cross-module analysis; opportunity scoring; report and readout.
4. **Write the scope as testable statements:** "Analyse billing, subscription and product-event data for the period Jan 2025 – Jun 2026", not "analyse your data".
5. **List the deliverables.** Each one gets a name, a format, an acceptance criterion and the phase it belongs to. Map them to the `intelligence-report-builder` report types where relevant.
6. **Build the timeline in elapsed weeks,** starting from data receipt rather than signature, and show dependencies ("Week 1 starts when exports are received").
7. **Set client responsibilities:** named-role owners for data exports, an access approver, interview availability, a decision-maker for metric definitions and a response time for questions.
8. **Write the data request** as a table of system, dataset, minimum fields, history, format and whether personal data is needed (default: no; pseudonymous IDs). State how the data will be handled. Align the handling with `references/data-security-principles.md` and the user's actual practices; ask the user if those practices are unknown.
9. **List exclusions explicitly:** for example production implementation, dashboards built in the client's tools, ongoing monitoring, legal or tax advice, and accuracy of the client's source data.
10. **Write pricing assumptions** around the placeholder: what the fee covers, what triggers a change request, expenses, and validity period.
11. **Write acceptance criteria:** what the client checks and how long they have, for example "Report delivered with all 13 standard sections; client has 5 working days to raise factual errors".
12. **List risks and dependencies:** data quality, access delays, stakeholder availability, and definitions not agreed. Give each a mitigation.
13. **Run the honesty pass:** `python3 scripts/proposal_lint.py <draft.md>` flags guarantee language, social-proof claims, money amounts outside placeholders and missing sections. Resolve or justify every flag and complete the manual Quality checks, then mark the draft `DRAFT – requires owner approval`.

## Decision rules

- **No invented commercial facts:** no prices, discounts, testimonials, client logos, case-study results, certifications, team credentials or insurance cover unless the user provided them.
- **No guarantees** of outcomes ("we will reduce churn by 10%"). Describe what we will deliver and how quality is checked.
- **Scope follows discovery.** If the client asked for something not supported by the data they have, include a readiness check first, or exclude it.
- If timeline pressure conflicts with scope, propose a phased scope rather than compressing silently.
- Fixed-fee scope must include a change-request mechanism.

## Output structure

Use `templates/proposal-template.md`. Sections:

1. Title page (client, engagement, date, version, status)
2. Your context (attributed client statements)
3. Problem statement
4. Proposed engagement and approach
5. Scope (in and out)
6. Deliverables (name | format | acceptance criterion | phase)
7. Timeline (weeks from data receipt)
8. Client responsibilities
9. Data requirements and handling
10. Exclusions
11. Fees and pricing assumptions (placeholders unless supplied)
12. Acceptance criteria
13. Risks and dependencies
14. Next steps
Appendix: source statements used (IDs)

## Quality checks

- [ ] Every client problem in the proposal traces to a discovery statement ID.
- [ ] No price, rate or discount appears unless the user supplied it. Otherwise a placeholder is present.
- [ ] No guarantee language. Search the draft for "guarantee", "will increase", "will reduce", "ensure" and "proven" and rewrite each hit.
- [ ] No testimonials, logos or credentials that the user did not supply.
- [ ] Every deliverable has an acceptance criterion.
- [ ] The data request asks for the minimum fields and states personal-data handling.
- [ ] Exclusions are explicit and include implementation, unless implementation was explicitly sold.
- [ ] Status is "DRAFT – requires owner approval".

## Failure and escalation conditions

- **No discovery basis:** produce a pre-discovery outline only, with problems written as questions.
- **The user asks to "add a guarantee" or "add some testimonials":** explain the risk; offer measurable deliverables or a satisfaction-based review clause instead; never fabricate testimonials.
- **Contract, liability, IP or data-protection terms:** draft only as headings with placeholders, and recommend the user's own legal review. This skill does not give legal advice.
- **The client wants production system access:** add an access-approval step and a read-only requirement, and flag it for the human owner.

## Examples

**Deliverable row (good):**

| Deliverable | Format | Acceptance criterion | Phase |
|---|---|---|---|
| Data readiness assessment | PDF and CSV appendix | Covers every dataset in the data request; each dataset scored with the published method | 2 |

**Pricing section (good, no price supplied):**

> **Fee:** [PRICE: to be set by engagement owner], fixed, for the scope in section 5. Assumes data exports for up to 6 systems and up to 3 stakeholder interviews. Additional systems are handled by change request.

**Bad:** "Our proven methodology guarantees at least 3x ROI, as Acme Corp found." (A guarantee, an invented claim and an invented reference.)

## Related skills

- Upstream: `client-discovery-synthesis` (context, decisions, data requirements), `saas-prospect-qualification` (profile).
- Next: `business-data-inventory` once the proposal is accepted and data arrives.
- `intelligence-report-builder` defines the report types listed as deliverables.
