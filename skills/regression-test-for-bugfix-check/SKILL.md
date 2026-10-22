---
name: regression-test-for-bugfix-check
description: "Check that a bug-fix PR includes a test that would have failed before the fix and passes after — without it, the bug can silently reappear."
---

# regression-test-for-bugfix-check

## Instructions

Confirm the added test actually fails against the pre-fix code (not just passes both before and after). If the bug was found via a specific real-world scenario, check the test reproduces that scenario closely rather than a simplified version.

## Inputs

- `target`: the bug-fix PR to check.

## Outputs

A pass/fail on whether a genuine regression test exists, naming the gap if not.

## Constraints

- A test that passes both before and after the fix isn't testing the bug.

## Examples

### Example 1

Input: a PR fixing a rounding bug with no new test added.

Output: Flagged — add a test using the specific input values that exposed the rounding error, confirming it fails on the pre-fix code path.
