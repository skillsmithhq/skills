---
name: effort-estimation
description: "Estimate the effort for a feature, ticket, or project as a range with explicit assumptions and risks, grounded in the actual codebase rather than the description alone. Use when asked \"how long will this take\", to size tickets, plan a sprint or roadmap item, or sanity-check an existing estimate."
---

# effort-estimation

## Instructions

1. Restate the scope in concrete deliverables, and list what is explicitly out of scope.
2. Read the code the work touches to find the real change surface: files, modules, migrations, integrations, and tests that must change. Note anything that already exists and can be reused.
3. Break the work into tasks small enough to estimate (roughly half a day to three days each), including the often-forgotten ones: tests, code review, migrations and backfills, docs, deploy and rollout, and QA.
4. Give each task a best / likely / worst estimate. Combine them as a range (e.g. three-point PERT: (best + 4 × likely + worst) / 6), not a single number.
5. List the assumptions the range depends on and the top risks that would push it toward worst case, each with a way to reduce it (spike, prototype, early question to a stakeholder).
6. If the team uses story points, map the range onto their scale using past tickets of similar size when available; otherwise give it in ideal engineering days and say so.

## Inputs

- `work`: the feature, ticket, or project description.
- `team_context` (optional): team size, velocity, or point scale.

## Outputs

A task breakdown table (task, best, likely, worst), the combined range, assumptions, top risks with mitigations, and confidence (low/medium/high) with the reason.

## Constraints

- Never give a single-number estimate without a range and assumptions.
- Estimate engineering effort, not calendar time; say what calendar time would depend on (people, meetings, review wait, dependencies).
- If key information is missing, estimate with an explicit assumption and list the question, rather than refusing or guessing silently.

## Examples

### Example 1

Input: "how long to add SSO login with Google and Microsoft?"

Output: 8 tasks totalling 6-11 ideal days (likely 8): OAuth flow, account linking for existing users, two provider configs, session changes, admin toggle, tests, docs, staged rollout. Main risk: existing users with the same email on different auth methods; a half-day spike on account linking would narrow the range. Confidence: medium.
