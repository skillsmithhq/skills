---
name: test-data-realism-check
description: "Check that test fixtures reflect realistic edge cases (nulls, boundary values, multi-tenant data) rather than only a clean happy-path shape."
---

# test-data-realism-check

## Instructions

Check fixtures include at least one null/empty optional field, a boundary value (zero, negative, very large, at a limit threshold), and — for multi-tenant systems — data for more than one tenant in the same test run.

## Inputs

- `target`: the test fixtures to check.

## Outputs

A finding naming the missing edge-case shape in the fixture data.

## Constraints

- A fixture with exactly one of everything and no nulls tests that the code runs, not that it's correct.

## Examples

### Example 1

Input: fixtures for a usage-quota test using only one tenant and round numbers well below the quota.

Output: Flagged — add a second tenant's data to the same test run to catch a missing tenant filter, and a value exactly at the quota boundary.
