---
name: query-audit
description: "Find related-object access inside a loop or serializer method, check it against actual select_related/prefetch_related coverage, and measure the real query count before/after."
---

# query-audit

## Instructions

Identify the repo's data-access layer first, then measure the query count with that stack's own tooling (e.g. Django `CaptureQueriesContext`, Rails `ActiveSupport::Notifications`, SQLAlchemy event listeners, Prisma/TypeORM query logging, Hibernate statistics, or database statement logs) — a number, not an assertion. Look for per-row lazy loads inside loops and serializers, and fix them with the ORM's eager-loading or batching idiom. If the system is multi-tenant, watch for an eager-load fix that widens a query across tenants by joining a cross-tenant relation.

## Inputs

- `target`: endpoint, handler, serializer, or file path to audit.

## Outputs

A before/after query-count table with each fix as a `file:line`.

## Constraints

- Never claim "optimized" without a measured number.

## Examples

### Example 1

Input: "check for N+1s in the order list endpoint"

Output: Finding at `orders/serializers.py:42` (per-row `order.customer.address` access with no eager load) — before: 61 queries for 20 rows, after: 3 queries.
