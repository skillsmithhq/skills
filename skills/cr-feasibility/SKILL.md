---
name: cr-feasibility
description: "Answer a fixed set of feasibility questions for a Change Request, and save the result under the Change Request folder. Use whenever asked for a \"CR\", \"change request\", or \"feasibility check\" on a proposed feature or change."
---

# cr-feasibility

## Instructions

1. Restate the request in one paragraph, in the requester's own terms.
2. Answer every required question in full (see Outputs) — never skip one because the answer seems obvious; a skipped question reads as "not checked," not "not applicable."
3. Give an explicit go / no-go / needs-more-info recommendation with the single deciding tradeoff.
4. Save the result to the repo's existing change-request docs folder if it has one; otherwise `docs/change-requests/<short-slug>.md`.

## Inputs

- `change_description`: a description of the proposed change or feature.

## Outputs

A document answering, in order:

1. What is being requested.
2. Feasibility with the current architecture (or what new pattern it needs).
3. What it touches (services, models, endpoints, migrations).
4. Data/schema impact.
5. Multi-tenancy impact.
6. Security impact.
7. Performance impact (name the profiling point that would confirm it).
8. Effort estimate (S/M/L) and what drives it.
9. Risks/open questions.
10. Recommendation: go / no-go / needs-more-info, with the deciding tradeoff.

## Constraints

- Answer every question — no silent skips.
- Save to the Change Request folder, not RCA.
- Recommendation must name one deciding tradeoff, not a generic "it depends."
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "CR feasibility check for letting each workspace set its own file-upload size limit"

Output: A saved doc answering all 10 questions, ending with "Go — add a per-workspace limit to the existing settings model with the current global limit as the default; main tradeoff is enforcing it consistently in both the web upload and the API."
