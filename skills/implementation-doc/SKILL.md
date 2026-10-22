---
name: implementation-doc
description: "Draft an implementation document for an already-approved Change Request, and save it under the Implementation folder (not RCA, not Proposal). Use when asked to \"write the implementation doc for CR X\", \"document how we built this\", or once a CR has moved from feasibility to build."
---

# implementation-doc

## Instructions

1. Link to the originating CR.
2. Describe what was actually built, referencing real files/modules (`file:line` where useful) — not the originally proposed design if it changed during build.
3. Call out any deviation from the CR/proposal, and why.
4. Save to the repo's existing implementation/design docs folder if it has one; otherwise `docs/implementation/<short-slug>.md`.

## Inputs

- `cr_or_feature`: a CR reference or feature name.

## Outputs

A document with:

1. **CR reference** — link/name of the originating Change Request.
2. **What was built** — actual implementation, with real file references.
3. **Deviations from the CR/proposal** — what changed during build, and why.
4. **Data/migration changes** — actual migrations run, with rollback notes.
5. **Testing performed** — what was actually verified.
6. **Known limitations** — anything intentionally deferred.
7. **Follow-ups** — ticket references, if any.

## Constraints

- Describe the actual build, not the original plan, when they diverge.
- Save to the Implementation folder, not RCA or Proposal.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write the implementation doc for the saved-searches CR"

Output: A doc referencing `PROJ-4620`, describing the actual model and API changes shipped, noting a deviation (sharing saved searches was descoped), and listing a follow-up ticket for it.
