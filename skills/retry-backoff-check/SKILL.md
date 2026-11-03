---
name: retry-backoff-check
description: "Check that a new call to an external service has retry/backoff on transient failure and doesn't silently swallow errors. Use when reviewing code that adds or changes an HTTP, SDK, queue, or database call to another service."
---

# retry-backoff-check

## Instructions

Check for: no retry at all, retry with no backoff (worsens a struggling upstream), and silent failure swallowing (bare except with no surfaced error). Distinguish retryable failures (timeouts, connection errors, 5xx, and 429/408, honouring any `Retry-After`) from non-retryable ones (other 4xx) — don't retry the latter. Check that retried writes are idempotent (or use an idempotency key) so a retry can't apply the same change twice. Use the repo's existing retry library or helper if it has one.

## Inputs

- `target`: the integration call to check.

## Outputs

A finding naming which of the three failure modes applies, if any.

## Constraints

- Retrying a 4xx validation/auth error forever wastes calls and can trip provider rate limits.

## Examples

### Example 1

Input: `try: send_to_ocr_service(doc) except Exception: pass`

Output: Flagged on two counts — no retry on transient failure, and the exception is silently swallowed with no error trail.
