---
name: cache-key-scoping-check
description: "Check that a cache key includes every dimension the cached value actually varies by (tenant, user, locale, permission level) — a key missing one dimension serves one caller's data to another."
---

# cache-key-scoping-check

## Instructions

For each dimension the cached value depends on, confirm it's present in the key. Also check invalidation: a correctly scoped key that's never invalidated on write becomes a scoped-but-stale leak of the previous state.

## Inputs

- `target`: cache read/write to check.

## Outputs

A finding naming the specific missing dimension in the key, or the missing invalidation path.

## Constraints

- A staleness bug and a cross-caller data leak are different severities — don't conflate them.

## Examples

### Example 1

Input: `cache_key = f"dashboard_summary_{user_id}"` in a multi-tenant app.

Output: Flagged — the key has no tenant component; if user ids aren't globally unique across tenants, one tenant's summary can be served to another.
