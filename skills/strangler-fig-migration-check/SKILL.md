---
name: strangler-fig-migration-check
description: "Check that a legacy-to-new migration routes traffic incrementally rather than a big-bang cutover with no rollback path."
---

# strangler-fig-migration-check

## Instructions

Check whether the plan routes traffic by tenant/percentage/feature area with the old system kept as fallback. Check what happens to data written by the new path if a rollback is needed after some traffic has gone through it.

## Inputs

- `target`: the migration plan to check.

## Outputs

A finding on whether the plan is incrementally reversible, and specifically what happens to new-path data on rollback.

## Constraints

- A "gradual" migration that can't roll back already-written data isn't actually reversible.

## Examples

### Example 1

Input: a plan to cut over the entire notification-delivery engine in one release.

Output: Flagged — route a small share of traffic (by customer or percentage) to the new engine first, keep the old engine live as fallback, and define what happens to notifications already queued by the new engine if a rollback is triggered.
