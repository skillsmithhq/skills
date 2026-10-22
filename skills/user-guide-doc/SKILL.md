---
name: user-guide-doc
description: "Draft an end-user-facing guide (not a technical doc) for a feature, and save it under the User Guide folder. Use when asked to \"write a user guide for X\", \"document this for end users\", or to explain a feature to non-technical tenant admins/users."
---

# user-guide-doc

## Instructions

1. Write for the actual end user (e.g. an admin or an everyday user), not an engineer — no code references, no internal architecture, no jargon not visible in the UI.
2. Confirm the real UI flow (from the frontend code or by asking) before writing numbered steps — don't invent menu paths.
3. Save to the repo's existing user-docs folder if it has one; otherwise `docs/user-guides/<short-slug>.md`.

## Inputs

- `feature`: the feature to document.

## Outputs

A document with:

1. **What this feature does** — plain-language paragraph.
2. **Who it's for** — role(s) that can use it.
3. **How to use it** — numbered steps matching the verified UI flow.
4. **Screenshots** — placeholder callouts where one should go.
5. **Common questions / edge cases** — things users are likely to get confused by, based on actual feature behavior.

## Constraints

- No internal model names, statuses, or jargon unless literally shown in the UI.
- Verify the UI flow before writing steps; don't invent menu paths.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write a user guide for the team invitations feature"

Output: `docs/user-guides/team-invitations.md` with plain-language steps for an admin inviting a teammate, what the invitee sees, and a note on how invitation links expire after 7 days.
