---
name: timeout-budget-check
description: "Check that every outbound call (HTTP, database, cache, queue, third-party SDK) has an explicit timeout, and that nested timeouts fit inside the caller's own deadline. Use when reviewing code that calls other services or adds a new dependency."
---

# timeout-budget-check

## Instructions

List the outbound calls in the request path. For each, find the configured connect and read timeouts; many clients default to none. Add up the worst case including retries and compare it with the upstream deadline (load balancer, gateway, client). Flag calls with no timeout, retries that exceed the budget, and timeouts longer than the caller is willing to wait.

## Inputs

- `target`: the request path, handler, or client configuration.

## Outputs

A table of calls with timeout, retries, and worst-case time, plus the total against the caller's deadline.

## Constraints

- A call with no timeout can hang a worker forever and exhaust the pool.
- Retries multiply worst-case latency; count them.

## Examples

### Example 1

Input: a checkout handler calling tax, fraud, and payment services behind a 30 s gateway timeout

Output: Flagged: the fraud client has no timeout and the payment client retries 3× at 10 s each; worst case exceeds 30 s, so the user sees a gateway error while the payment may still go through.
