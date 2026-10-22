---
name: health-check-endpoint-check
description: "Check that liveness and readiness endpoints report what the orchestrator needs and don't cause outages themselves. Use when adding or changing health checks, probes, or load-balancer checks."
---

# health-check-endpoint-check

## Instructions

Confirm liveness checks only that the process is responsive (no dependency calls), so a database blip doesn't restart every instance. Confirm readiness checks the dependencies required to serve traffic, with short timeouts. Check the endpoint is cheap, unauthenticated or internally scoped, and doesn't leak versions or config. Check probe intervals, thresholds, and startup grace against real startup time.

## Inputs

- `target`: the health endpoint and probe configuration.

## Outputs

A finding per probe that could cause cascading restarts, false readiness, slow recovery, or information leaks.

## Constraints

- A liveness probe that checks the database turns a database outage into a restart storm.
- A readiness check that always returns 200 sends traffic to instances that can't serve it.

## Examples

### Example 1

Input: a `/health` endpoint used for both liveness and readiness that queries the database

Output: Flagged: split into `/livez` (process only) and `/readyz` (database with a 1 s timeout), and point the liveness probe at `/livez`.
