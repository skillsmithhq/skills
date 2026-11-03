---
name: migration-safety-check
description: "Check whether code still running mid-rollout keeps working against a new migration, whether it locks a large table, and, for multi-schema or multi-tenant databases, whether it runs correctly in every schema, not just one. Use when reviewing a database migration before merge."
---

# migration-safety-check

## Instructions

Identify the database engine and version and the migration tool first; locking behaviour differs between them, so check that engine's docs rather than assuming. Check for a `NOT NULL` column with no default or a renamed/dropped column the previous release still reads. Check locking risk on large tables (a table rewrite from adding a column with a default, where the engine/version does that; a non-concurrent index build). Confirm a batched/async backfill rather than one bulk `UPDATE`. If per-tenant schemas exist, confirm the migration runs across all of them.

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
