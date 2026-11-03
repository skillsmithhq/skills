---
name: sse-endpoint-review
description: "Check an SSE/streaming endpoint for an unbounded buffer, missing heartbeats, and leaked generators on disconnect, and state the connection-capacity implication in concrete worker-count terms. Use when reviewing a server-sent events or other long-lived streaming endpoint."
---

# sse-endpoint-review

## Instructions

Identify the server framework and concurrency model (sync workers, threads, async event loop). Check for a per-connection queue/buffer with no size bound. Check for periodic heartbeats. Check that client disconnect actually tears down the generator/listener via a `finally`/context-manager. State capacity in that model's terms, e.g. "N concurrent connections ties up N of M workers" for sync workers, or open file descriptors and memory per connection for async servers.

## Inputs

- `target`: the SSE view/endpoint to review.

## Outputs

A finding per check, with the concrete capacity statement.

## Constraints

- Only applies to repos with actual SSE/streaming endpoints.

## Examples

### Example 1

Input: "review this new live-notifications SSE endpoint"

Output: Finding — the internal event queue has no size bound, causing unbounded memory growth under a slow client; bound it (e.g. `queue.Queue(maxsize=100)` in Python) and drop or disconnect when full.
