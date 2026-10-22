---
name: empty-state-check
description: "Check that a list/table/dashboard view has a designed empty state for both cases — genuinely no data yet, and a filter/search returning zero results — since these need different messaging and are commonly conflated or missed entirely."
---

# empty-state-check

## Instructions

Check that "first-run" (no data ever) shows a call-to-action, and "filtered-to-zero" (data exists, filter excludes it) shows a way to clear the filter — not the same generic message for both. Check for a flash of the empty state before the first fetch resolves.

## Inputs

- `target`: view or component to check.

## Outputs

A finding on which empty-state case is missing or conflated.

## Constraints

- The two empty states need different actions, not just different wording.

## Examples

### Example 1

Input: a projects list showing "No projects found" both on first login and when a filter matches nothing.

Output: Flagged — the first-run state should prompt "Create your first project"; the filtered-to-zero state should offer "Clear filters" instead.
