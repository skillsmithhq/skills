---
name: test-coverage-gap-check
description: "Check that new/changed business logic has a test covering the specific behavior change — not just that overall coverage percentage didn't drop."
---

# test-coverage-gap-check

## Instructions

For each new conditional, edge case, or error path in the diff, check whether a test actually exercises that specific path. Check sad paths (error handling, validation failures, boundaries) especially, since these are most often left untested.

## Inputs

- `target`: the diff and its accompanying tests to check.

## Outputs

A finding per untested branch/edge case introduced by the diff.

## Constraints

- Overall coverage percentage staying flat does not mean the new code is tested.

## Examples

### Example 1

Input: a new validation branch rejecting a negative amount, with tests only for the valid-amount path.

Output: Flagged — add a test for the negative-amount rejection branch; coverage % may look fine while this specific path is untested.
