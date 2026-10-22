---
name: idempotency-check
description: "Check whether an operation reachable via webhook, retry-prone API call, or an at-least-once task queue is safe to execute twice."
---

# idempotency-check

## Instructions

Check whether a second execution with the same input produces the same end state (safe) or a duplicated effect (unsafe — duplicate email, double debit, duplicate row). Where unsafe, add a dedup key checked inside the same transaction as the write it guards.

## Inputs

- `target`: webhook handler, endpoint, or task to check.

## Outputs

A finding stating whether the operation is idempotent, and if not, the dedup-key fix.

## Constraints

- Checking the dedup key in a separate step (not the same transaction) reintroduces a check-then-act race — see `check-then-act-race-check`.

## Examples

### Example 1

Input: a payment-webhook handler that credits an account on each call.

Output: Flagged — not idempotent; a redelivered webhook double-credits. Recommend storing the webhook event id and checking it inside the same transaction as the credit.
