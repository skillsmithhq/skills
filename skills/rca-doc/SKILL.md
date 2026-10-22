---
name: rca-doc
description: "Write a Root Cause Analysis document for a bug/incident that has already been diagnosed in this session, and save it under the RCA folder. Use when asked to \"write an RCA\", \"document this root cause\", \"create an RCA for X\", or after a bug's root cause has been confirmed and needs to be captured for the record."
---

# rca-doc

## Instructions

1. Confirm the root cause is actually established in the conversation — never speculate a cause just to fill out the template. If it isn't nailed down yet, say so and offer to investigate first.
2. Determine the target path: `docs/rca/<short-slug>.md` (or the repo's existing RCA/docs folder if it already has one; don't ask).
3. Write the eight required sections (see Outputs) using facts and evidence from the conversation, with a `file:line` code reference for the root cause.
4. Save the file. Keep it factual and terse — a record, not a narrative.

## Inputs

- `topic`: the bug/incident description, or "for the fix we just made" if it refers to the current session's work.

## Outputs

A markdown file containing these sections, in order:

1. **Symptom** — what was observed, by whom, how reported.
2. **Impact** — affected tenant(s)/users/data, severity.
3. **Timeline** — dated sequence: start, detection, fix.
4. **Root Cause** — the mechanism, with a `file:line` citation, not a guess.
5. **Evidence** — how the cause was confirmed.
6. **Fix** — what changed, with a commit/PR reference if one exists.
7. **Blast Radius** — other customers/paths that could hit the same bug, even unreported.
8. **Prevention** — test/monitoring added, or "none" with why.

## Constraints

- Never speculate a root cause to complete the template.
- Always save to the RCA folder, never elsewhere, unless told otherwise.
- No comment-style padding or restating the obvious.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write an RCA for the discount bug we just fixed"

Output: `docs/rca/discount-limit-bypass.md` containing all eight sections, citing the specific `file:line` where the per-order discount cap was skipped on one code path and the fix that routed it through the shared validator.
