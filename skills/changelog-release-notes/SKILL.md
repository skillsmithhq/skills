---
name: changelog-release-notes
description: "Write release notes or a changelog entry from the actual commits and merged PRs between two versions, grouped for the intended reader. Use when asked to write release notes, update CHANGELOG.md, or summarise what shipped."
---

# changelog-release-notes

## Instructions

1. Find the range: the previous tag or release to the current one (ask if ambiguous).
2. Read the commits and merged PRs in that range; ignore pure chores unless they affect users or operators.
3. Group into Added, Changed, Fixed, Deprecated, Removed, and Security (Keep a Changelog style), or follow the repo's existing CHANGELOG format.
4. Write each entry in terms of user-visible effect, with a PR or issue reference.
5. Call out breaking changes and required upgrade steps at the top.

## Inputs

- `range` (optional): two tags, commits, or dates; defaults to the last tag through HEAD.
- `audience` (optional): end users, developers, or operators.

## Outputs

A changelog section or release-notes document for the range, with breaking changes first.

## Constraints

- Only include changes that are actually in the range.
- Describe the effect, not the implementation.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write release notes for v2.4.0"

Output: Breaking: the `/v1/export` endpoint is removed (use `/v2/export`). Added: CSV import for contacts (#412). Fixed: timezone shift on invoices dated at midnight (#398).
