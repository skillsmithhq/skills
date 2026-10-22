---
name: check-then-act-race-check
description: "Find read-then-write logic that checks a condition (a limit, a balance, a uniqueness rule) and writes without a DB-level lock or constraint, making it vulnerable to a race under concurrent requests."
---

# check-then-act-race-check

## Instructions

Identify any check-then-write sequence and confirm it's guarded by a `SELECT ... FOR UPDATE`, an atomic `F()`-expression update with a `WHERE` clause encoding the limit, or a DB-level constraint — not just a Python-level comparison before the write.

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
