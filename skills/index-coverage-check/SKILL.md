---
name: index-coverage-check
description: "Check that new or changed queries are backed by suitable database indexes and that new indexes are worth their write cost. Use when reviewing queries, filters, sorts, joins, or migrations that add indexes."
---

# index-coverage-check

## Instructions

For each query in the change, list its filter, join, and sort columns. Check the schema or migrations for an index that covers them in a usable order, and run `EXPLAIN` (or the database's equivalent) on representative data where possible. For new indexes, check they aren't redundant with an existing one, and that creation won't lock a large table (use the database's concurrent/online option).

## Inputs

- `target`: the query, endpoint, or migration to check.

## Outputs

A per-query finding: covered, not covered (with the suggested index), or redundant index.

## Constraints

- An index that works on a 100-row dev table proves nothing; reason about production row counts.
- Every index slows writes; don't add one for a query that runs once a day.
- Use plain `EXPLAIN`, not `EXPLAIN ANALYZE`, for statements that write, since `ANALYZE` executes them. Never run queries against a production database without the user's approval.

## Examples

### Example 1

Input: a new dashboard filter on `orders` by `status` and `created_at`, sorted by `created_at`

Output: Not covered: only `status` is indexed, so the sort scans; suggest a composite index on `(status, created_at)` created concurrently.
