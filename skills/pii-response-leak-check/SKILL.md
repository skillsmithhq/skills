---
name: pii-response-leak-check
description: "Check that error responses returned to API clients don't leak PII, internal stack traces, or DB error text — distinct from logging PII checks, since this is about what the client receives."
---

# pii-response-leak-check

## Instructions

Find every place a caught exception's `str(e)`/`.args` reaches the response body directly. Replace with a generic message plus a correlation id; keep the real detail server-side in the log only.

## Inputs

- `target`: endpoint or exception handler to check.

## Outputs

A `file:line` finding for each exception-to-response leak.

## Constraints

- Passing a "don't log PII" review does not mean the response body is also clean — check both separately.

## Examples

### Example 1

Input: `return Response({"error": str(e)}, status=400)` where `e` is a DB `IntegrityError`.

Output: Flagged — the DB error text can contain another record's data; return a generic message and a correlation id instead, logging the real error server-side.
