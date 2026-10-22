---
name: pr-description
description: "Generate a PR description for the current branch's diff, using a fixed section template and an evidence-backed depth bar (measured query counts, equivalence proofs, before/after tables — not asserted claims). Use when asked for \"a PR description\", \"describe this PR\", or before opening a pull request."
---

# pr-description

## Instructions

1. If the repo has a PR/MR template (`.github/pull_request_template.md`, `.gitlab/merge_request_templates/`, or similar), follow its headings and fold the sections below into it.
2. Derive the description from the actual diff (`git diff` against the base branch, or a named PR's diff) — never from memory of what was intended.
3. Write each required section (see Outputs), scaling depth to the size of the change.
4. For the Query/Performance section: state measured before/after numbers for any DB-query, hot-path, or loop change; write "not applicable" explicitly if there's none — never omit the section.
5. For Security/data-access impact: call out anything touching permissions, auth, secrets, or data-access scoping (per-user or per-tenant filters), or state "none".

## Inputs

- `target` (optional): a PR number or branch to describe; defaults to the current branch's diff against its base.

## Outputs

A PR description with these sections:

1. **Summary** — 1-3 bullets, why not what.
2. **Changes** — grouped bullet list of substantive changes.
3. **Query/Performance impact** — measured before/after, or "not applicable".
4. **Security/data-access impact** — or "none".
5. **Test plan** — checklist of what was verified and how.
6. **Rollout notes** — migration safety, backward compatibility, incremental-ship safety.

## Constraints

- Never assert "optimized" without a measured number.
- Match depth to change size — a one-line fix gets a short description, not the full template padded out.
- Don't omit the Query/Performance or Security section; state "not applicable"/"none" instead.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write a PR description for this branch"

Output: A description with Summary ("Fixes N+1 in the order list endpoint"), Changes (added eager loading of the related customer), Query/Performance impact ("47 queries → 3 queries for a 20-item page, measured with the test suite's query counter"), Security/data-access impact ("none"), Test plan, Rollout notes ("safe to ship independently, no migration").
