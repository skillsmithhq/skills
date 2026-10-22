---
name: webhook-receiver-check
description: "Check an incoming-webhook endpoint for signature verification, replay protection, idempotency, and fast acknowledgement. Use when building or reviewing a handler for webhooks from a payment provider, Git host, chat platform, or any third party."
---

# webhook-receiver-check

## Instructions

Confirm the signature is verified against the raw request body (before JSON parsing) with a constant-time comparison, using the provider's documented scheme. Check timestamp tolerance to block replays, and dedupe by the provider's event id so retries are safe. Confirm the handler acknowledges quickly and moves slow work to the repo's existing background mechanism. Check that unknown event types are acknowledged and ignored, not errored.

## Inputs

- `target`: the webhook handler to check.

## Outputs

A checklist (signature, replay window, idempotency, ack speed, unknown events) with a `file:line` finding per failure.

## Constraints

- Providers retry on timeouts and errors; assume every event can arrive more than once and out of order.
- Verifying against re-serialized JSON breaks on whitespace and key order; use the raw body.

## Examples

### Example 1

Input: "review our payment webhook handler"

Output: Flagged: the signature is computed over `JSON.stringify(req.body)` instead of the raw body, and duplicate deliveries create duplicate orders; verify the raw body and store processed event ids.
