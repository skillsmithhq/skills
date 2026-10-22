---
name: transaction-boundary-check
description: "Check that multi-step writes that must succeed or fail together run in one transaction, and that side effects (emails, events, API calls) fire only after commit. Use when reviewing code that writes several rows or tables, or that writes and then notifies."
---

# transaction-boundary-check

## Instructions

Identify the repo's transaction mechanism (decorator, context manager, unit of work). Find write sequences that must be atomic and confirm they share a transaction. Find side effects inside the transaction and move them to an after-commit hook or outbox. Check that long-running work (network calls, file processing) isn't holding a transaction open.

## Inputs

- `target`: the function, handler, or diff to check.

## Outputs

A `file:line` finding per non-atomic sequence or pre-commit side effect, with the fix.

## Constraints

- A side effect sent before commit can announce data that a rollback then erases.
- Holding a transaction across a network call turns a slow dependency into lock contention.

## Examples

### Example 1

Input: an order-creation handler that inserts the order, sends a confirmation email, then inserts line items

Output: Flagged: the email is sent before the line items are written, so a failure there leaves a confirmed order with no items; wrap both inserts in one transaction and send the email after commit.
