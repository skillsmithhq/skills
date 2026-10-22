---
name: pagination-consistency-check
description: "Check that a new list endpoint has pagination, and that offset-based pagination combined with concurrent writes can't produce skipped or duplicated rows across pages."
---

# pagination-consistency-check

## Instructions

Confirm any unbounded list endpoint is paginated. If offset-based, check what happens when a row is inserted/deleted between page fetches while the underlying data is actively written. Prefer cursor-based pagination on a stable monotonic field where consistency matters more than simplicity.

## Inputs

- `target`: the list endpoint to check.

## Outputs

A finding on missing pagination, or on offset-based pagination's skip/duplicate risk for actively-written data.

## Constraints

- This only matters where the underlying data is actively written during pagination — a static report doesn't need cursor-based pagination.

## Examples

### Example 1

Input: an offset-paginated "bulk upload progress" list where rows are being inserted as processing continues.

Output: Flagged — a row inserted before the current page's offset shifts every later page, causing a skipped or duplicated row; recommend cursor-based pagination keyed on `created_at`/id.
