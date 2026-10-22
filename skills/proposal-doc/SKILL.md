---
name: proposal-doc
description: "Draft a technical/architecture proposal document and save it under the Proposal folder (not RCA). Use when asked to \"write a proposal for X\", \"draft an architecture proposal\", or to document a new service/feature design before it's built."
---

# proposal-doc

## Instructions

1. State the problem in concrete terms — not "it would be nice to have."
2. Write each required section (see Outputs), naming the actual stack/layers involved — verify the repo's real stack rather than assuming a pattern from another repo in the workspace.
3. Include at least one alternative considered and why it was rejected.
4. Save to the repo's existing proposals/RFC folder if it has one; otherwise `docs/proposals/<short-slug>.md`.

## Inputs

- `system_or_feature`: the system or feature to propose.

## Outputs

A document with:

1. **Problem** — the concrete gap or need.
2. **Goals / Non-goals** — explicit scope boundary.
3. **Proposed architecture** — the design, naming the real stack/layers.
4. **Alternatives considered** — at least one, with rejection reason.
5. **Tradeoffs** — performance, complexity, coupling, migration cost.
6. **Rollout plan** — phased delivery, what can ship independently.
7. **Open questions** — decisions needed before starting.

## Constraints

- Never default to the RCA folder for a proposal.
- Name the actual verified stack, not an assumed one.
- Write for a reader who wasn't in the conversation — the doc outlives the chat.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "draft a proposal for a standalone report service"

Output: `docs/proposals/report-service-architecture.md` covering the proposed stack, the core data model, alternatives considered (extending the existing monolith vs. a new service), and a phased rollout plan.
