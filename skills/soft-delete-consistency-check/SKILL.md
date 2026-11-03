---
name: soft-delete-consistency-check
description: "Check that a soft-deleted record is excluded everywhere it needs to be — the ORM's default scope or manager, raw queries, aggregations, serializers, and any cache built before the deletion. Use when reviewing a model with soft delete or a new query or report over soft-deletable data."
---

# soft-delete-consistency-check

## Instructions

Identify how the repo implements soft delete (e.g. a `deleted_at` column with a Django manager, Rails `default_scope`, or Hibernate filter). Check each access path separately: raw SQL or an "include deleted" scope or manager call, aggregations run against an unfiltered base queryset, related-object traversal that bypasses the soft-delete-aware default scope, and a cache entry never invalidated on delete.

## Inputs

- `target`: model, query, or serializer to check.

## Outputs

A `file:line` finding per gap, labeled "missing filter" or "stale cache" since the fix differs.

## Constraints

- Don't assume the default scope's filtering covers every access path.

## Examples

### Example 1

Input: a new revenue report aggregating `SUM(amount)` over a raw SQL query on the `orders` table.

Output: Flagged — the raw query doesn't exclude rows with `deleted_at` set, unlike the default scope used elsewhere, so deleted orders inflate revenue.
