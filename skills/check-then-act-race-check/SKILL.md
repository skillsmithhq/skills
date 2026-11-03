---
name: check-then-act-race-check
description: "Find read-then-write logic that checks a condition (a limit, a balance, a uniqueness rule) and writes without a DB-level lock or constraint, making it vulnerable to a race under concurrent requests. Use when reviewing code that enforces a limit, balance, or uniqueness rule."
---

# check-then-act-race-check

## Instructions

Identify the repo's datastore and data-access layer first. Identify any check-then-write sequence and confirm it's guarded at the database: a row lock (e.g. `SELECT ... FOR UPDATE`), an atomic conditional update whose `WHERE` clause encodes the limit (e.g. `UPDATE ... SET used = used + 1 WHERE used < max_uses`, or Django `F()` expressions), a unique or check constraint, or the datastore's equivalent (conditional writes, compare-and-set) — not just an application-level comparison before the write.

## Inputs

- `target`: code implementing a limit/balance/uniqueness check.

## Outputs

A `file:line` finding naming the unguarded check-then-act sequence and the recommended DB-level guard.

## Constraints

- The check "looking correct" in isolation is not sufficient — the bug only appears under concurrency.

## Examples

### Example 1

Input: a coupon with a usage limit, checked in application code and then redeemed with a separate insert if still under the limit.

Output: Flagged — two concurrent checkouts can both pass the check and both redeem; enforce the limit atomically with a conditional update or a database constraint.
