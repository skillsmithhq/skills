---
name: data-backfill-safety-check
description: "Check a one-off data backfill or correction script for batching, idempotency, dry-run support, and rollback before it runs against production. Use when reviewing any script or migration that rewrites existing rows."
---

# data-backfill-safety-check

## Instructions

Confirm the script processes in bounded batches with progress logging and can resume after interruption. Confirm it's idempotent (safe to run twice) and has a dry-run mode that reports what would change. Check that it captures enough of the old values to roll back. Check its load on the database (batch size, sleeps, off-peak timing) and whether it fires triggers, callbacks, or events that send notifications.

## Inputs

- `target`: the backfill script or data migration.

## Outputs

A go/no-go with findings for batching, idempotency, dry run, rollback data, load, and side effects.

## Constraints

- A backfill that sends one email per row is an incident, not a fix.
- Test against a production-sized copy if one exists; row counts change the risk.
- Review only: never run the script against a real database.

## Examples

### Example 1

Input: "review this script that recalculates every customer's balance"

Output: No-go: it loads all rows into memory in one query and has no dry run; batch by id range, add `--dry-run`, and log old balances for rollback.
