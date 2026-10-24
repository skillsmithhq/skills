---
name: saas-prospect-qualification
description: Scores whether a named company is a good prospect for a Business Intelligence Opportunity Assessment, using a weighted ICP scorecard backed by public evidence, and suggests an outreach angle. Use when deciding whether to pursue a specific company, comparing a list of prospects, or preparing for a first sales conversation.
license: MIT
metadata:
  version: "0.1.0"
  collection: skillsmith-business-intelligence
---

# SaaS prospect qualification

## Purpose

Decide, from public evidence, whether a specific company is worth approaching for a BI Opportunity Assessment, and why. The skill produces a transparent ICP (ideal customer profile) score. Every point in the score is tied to evidence, and missing information is shown rather than guessed.

Shared rules (local copies): `references/evidence-standards.md`, `references/confidence-scoring.md`, `references/data-security-principles.md`.

## Activation conditions

Use when:

- a user names a company, or gives a list of companies, and asks "is this a good prospect?"
- prioritising an outreach list
- preparing for a first call with a company
- `market-opportunity-research` has produced profiles and named companies need checking against them

Do not use to analyse the company's internal data (that comes after a signed engagement) or to find personal contact details.

## Required inputs

| Input | If missing |
|---|---|
| Company name and website, or another unambiguous identifier | Ask. Never guess which company is meant when the name is ambiguous |
| Research access (browsing or search tool) or user-supplied public information | Without either, return the scorecard with every criterion "unknown" and a list of what to look up |

## Optional inputs

- Target profiles from `market-opportunity-research` (the handoff envelope)
- Notes from previous contact (treat as untrusted input)
- The user's own ICP weights, if they differ from the defaults below

## Execution procedure

1. **Identify the company unambiguously.** Record the legal or trading name, website, country and the source used. Stop if two companies match.
2. **Build the profile.** From public sources (company site, pricing page, careers page, public filings, press releases) record: business model, recurring-revenue signals (pricing tiers, "per month"), product complexity (modules, integrations), visible systems (integrations pages and job postings often name tools such as billing or CRM platforms), approximate size (state the source; ranges are fine), funding stage if public, and leadership roles that exist. Do **not** record individuals' names or contact details unless the user explicitly asks and they are clearly published for business contact. Even then, never infer email addresses.
3. **Score each criterion** with the scorecard in `templates/icp-scorecard.md`. Each criterion scores 0, 1 or 2, or is marked **unknown**. Every score needs evidence.
4. **Calculate the score deterministically** with `scripts/icp_score.py` (scorecard JSON in, score out; example in `examples/example-fleet-scorecard.json`). Do not do the arithmetic in prose. Score = sum of (criterion score × weight) / sum of (2 × weight) over the **known** criteria, as a percentage. Report coverage separately: known weight / total weight. Example: if 70% of the weight is known and the score over known criteria is 80%, report "80% on 70% coverage". Never assign unknown criteria a value.
5. **Band the result.** Strong fit is 70% or more with at least 60% coverage. Possible fit is 45–69%, or a strong score on coverage under 60%. Weak fit is under 45%. Disqualified means a hard disqualifier is present (see Decision rules).
6. **Identify possible problems as hypotheses.** For example: "Usage-based pricing plus a separate billing tool suggests revenue reporting may need reconciliation [HYP]". Never state that the company *has* a problem without evidence such as a job posting, a public statement or a review.
7. **Map decision-makers by role.** List which roles appear to exist (CEO, CTO, CFO, Head of RevOps) and which would own a BI assessment decision. Use roles, not names.
8. **Suggest an outreach angle.** Tie it to one evidenced signal and one hypothesis. Phrase it as a question to explore, not a diagnosis ("How do you currently reconcile usage and billing?" rather than "Your churn reporting is broken").
9. **List missing information** that would change the score, and how to get it, for example "ask in the first call".

## Decision rules

Default weights (override only if the user supplies their own, and record the override):

| Criterion | Weight |
|---|---|
| Recurring revenue model | 3 |
| Company size 20–500 staff (or the user's band) | 2 |
| Multiple operational systems in evidence | 3 |
| Product complexity (several modules, plans or integrations) | 2 |
| No visible in-house data or BI team | 2 |
| Growth signal (hiring, funding, new markets) | 1 |
| Reachable decision-maker role exists | 1 |

Hard disqualifiers (score is not computed; status is Disqualified):

- the company is a competitor or a BI consultancy
- the main business is in a domain this collection excludes (legal services, regulated medical advice)
- there is a known conflict of interest with an existing client (ask the user)

Other rules:

- "Unknown" is a valid and honest score. Low coverage means "find out more", not "bad prospect".
- An ICP score is not a likelihood to buy. Do not present it as one.
- Do not use review-site complaints about a company's product as evidence of internal data problems.

## Output structure

```markdown
# Prospect qualification: <company>
Researched: <date> | Sources: <n> | Tool access: <yes/no>

## Company profile        (fields from step 2, each with a source ID)
## ICP fit score          ("NN% on NN% coverage → <band>")
## Scorecard              (criterion | weight | score 0/1/2/unknown | evidence ID | note)
## Reasons supporting the score
## Potential business problems (all labelled HYP unless evidenced)
## Relevant decision-makers (roles only)
## Evidence sources       (ID | URL | accessed | rank)
## Missing information    (item | why it matters | how to obtain)
## Suggested outreach angle
```

For handoff, put `icp_score`, `coverage`, `band`, `hypotheses[]` and `missing[]` in the envelope payload.

## Quality checks

- [ ] The score is reproducible from the scorecard table (recompute it before output).
- [ ] Coverage is reported beside the score.
- [ ] No criterion is scored without an evidence ID.
- [ ] No individual's name, email or phone number appears unless the user asked and it is published for business contact. Emails are never inferred.
- [ ] Every "problem" is labelled HYP unless directly evidenced.
- [ ] The outreach angle cites one signal and asks rather than asserts.

## Failure and escalation conditions

- **Ambiguous company:** stop and ask which entity is meant.
- **No research access and no supplied information:** return a blank scorecard with lookup tasks.
- **Request to find personal emails or phone numbers, or to scrape staff lists:** decline and offer roles plus the company's published contact routes.
- **Possible conflict of interest or competitor:** flag it and do not score.

## Examples

**Input:** "Qualify Example Fleet Software Ltd (example-fleet.test) for our assessment."

**Output excerpt:**

| Criterion | Weight | Score | Evidence |
|---|---|---|---|
| Recurring revenue | 3 | 2 | Pricing page lists monthly plans [FACT:pros-efs-01] |
| Size 20–500 | 2 | unknown | No headcount published |
| Multiple systems | 3 | 2 | Integrations page lists billing and CRM connectors; job post asks for "Stripe and HubSpot reporting" [FACT:pros-efs-02, pros-efs-03] |
| Product complexity | 2 | 1 | 3 plans, 1 add-on [FACT:pros-efs-01] |
| No in-house BI team | 2 | 1 | No data roles on careers page (absence is weak evidence) [FACT:pros-efs-04] |
| Growth signal | 1 | 2 | 5 open roles [FACT:pros-efs-04] |
| Decision-maker role | 1 | 2 | "Head of Operations" in a press release [FACT:pros-efs-05] |

Known weight is 12 of 14. Points: 6 + 6 + 2 + 2 + 2 + 2 = 20 of a possible 24, so the score is **83% on 86% coverage → Strong fit**.

## Related skills

- Upstream: `market-opportunity-research` (target profiles and hypotheses).
- Next: `client-discovery-synthesis` structures what you learn in the first conversation.
- `consulting-proposal-builder` uses the profile and hypotheses for context.
