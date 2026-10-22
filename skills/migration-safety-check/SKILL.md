---
name: migration-safety-check
description: "Check whether code still running mid-rollout keeps working against a new migration, whether it locks a large table, and, for multi-schema or multi-tenant databases, whether it runs correctly in every schema, not just one."
---

# migration-safety-check

## Instructions

Check for a `NOT NULL` column with no default or a renamed/dropped column the previous release still reads. Check locking risk on large tables (default-triggered rewrite, non-concurrent index). Confirm a batched/async backfill rather than one bulk `UPDATE`. If per-tenant schemas exist, confirm the migration runs across all of them.

## Inputs

- `target`: migration file or description of the schema change.

## Outputs

A stated risk level (safe to ship / needs coordinated rollout / needs backfill first) with the specific reason.

## Constraints

- Validating in one schema and assuming it applies everywhere is the specific way this fails for multi-tenant schemas.
- Review only: never apply the migration to a shared or production database.

## Examples

### Example 1

Input: "is this migration safe to merge?" (adds a NOT NULL column with no default to a 2M-row table)

Output: "Needs backfill first — add nullable, backfill via a batched task, then add the NOT NULL constraint in a follow-up migration."
