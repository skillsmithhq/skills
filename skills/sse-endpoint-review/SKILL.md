---
name: sse-endpoint-review
description: "Check an SSE/streaming endpoint for an unbounded buffer, missing heartbeats, and leaked generators on disconnect, and state the connection-capacity implication in concrete worker-count terms."
---

# sse-endpoint-review

## Instructions

Check for a queue/buffer with no `maxsize`. Check for periodic heartbeats. Check that client disconnect actually tears down the generator/listener via a `finally`/context-manager. State capacity as "N concurrent connections ties up N of M workers."

## Inputs

- `target`: the SSE view/endpoint to review.

## Outputs

A finding per check, with the concrete capacity statement.

## Constraints

- Only applies to repos with actual SSE/streaming endpoints.

## Examples

### Example 1

Input: "review this new live-notifications SSE endpoint"

Output: Finding — the internal event queue has no `maxsize`, causing unbounded memory growth under a slow client; recommend `queue.Queue(maxsize=100)`.
