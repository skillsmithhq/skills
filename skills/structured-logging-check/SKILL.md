---
name: structured-logging-check
description: "Check that new log lines are structured, carry the context needed to debug (request id, user or account id, operation), use the right level, and never contain secrets or personal data. Use when reviewing code that adds or changes logging."
---

# structured-logging-check

## Instructions

Identify the repo's logging library and conventions. Confirm new logs use structured fields rather than string concatenation, include the correlation/request id, and sit at the right level (errors that need action at error, expected conditions at info or debug). Check that exceptions are logged with the stack trace once, not at every layer. Scan for tokens, passwords, full card numbers, and personal data in log arguments.

## Inputs

- `target`: the diff or file to check.

## Outputs

A `file:line` finding per log line that's unstructured, missing context, mis-levelled, duplicated, or leaking data.

## Constraints

- Logging the whole request or user object is the usual way secrets leak.
- An error logged at every layer is noise that hides the real one.

## Examples

### Example 1

Input: a new payment retry loop that logs `"retry failed for " + str(payment)`

Output: Flagged: the full payment object (including card details) is logged as a string; log `payment_id`, `attempt`, and `error_code` as structured fields instead.
