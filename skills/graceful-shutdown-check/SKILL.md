---
name: graceful-shutdown-check
description: "Check that a service finishes in-flight work and releases resources cleanly when it receives a termination signal during deploys and scaling. Use when reviewing server, worker, or consumer startup and shutdown code, or deploy configuration."
---

# graceful-shutdown-check

## Instructions

Confirm the process handles the platform's termination signal (usually SIGTERM), stops accepting new requests or messages, finishes or requeues in-flight work within the grace period, and closes connections. Check the orchestrator's grace period exceeds the longest expected request or job, and that readiness flips to failing before shutdown so the load balancer drains traffic.

## Inputs

- `target`: service entrypoint, worker, or deploy config.

## Outputs

A finding per gap: unhandled signal, no drain, grace period too short, or work lost on shutdown.

## Constraints

- Workers that ack a message before processing lose it on every deploy.
- Default grace periods are often shorter than the slowest job.

## Examples

### Example 1

Input: a queue worker that acks messages on receipt and runs jobs up to 2 minutes, with a 30 s grace period

Output: Flagged: jobs in progress at deploy time are lost; ack after completion, handle SIGTERM by finishing the current job, and raise the grace period above the longest job.
