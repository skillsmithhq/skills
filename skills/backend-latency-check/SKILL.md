---
name: backend-latency-check
description: "Find where time goes in a slow endpoint, job or service path by measuring it (p50, p95, p99) and breaking the time down into database, external calls, serialisation, CPU and waiting, then fix the biggest contributor and measure again. Use when an endpoint or job is slow, latency regressed, or an SLO is at risk."
---

# backend-latency-check

## Instructions

1. Detect the stack and the observability already in place: tracing (for example OpenTelemetry), APM, metrics, slow-query logs, and profilers for the language. Prefer existing traces and metrics to new instrumentation.
2. Establish a baseline for the specific path: p50, p95 and p99 latency, request rate and error rate, over a stated window. Use production metrics if available (read-only), otherwise a local or staging run with realistic data volume.
3. Break one slow request down by time spent: database queries (count and duration), calls to other services and third parties, serialisation, CPU-heavy code, lock or pool waits (database connections, thread pools), and queueing. Use a trace or a profiler, not guesswork.
4. Check the common causes: N+1 queries (use `query-audit`), missing indexes (`index-coverage-check`), unbounded results (`payload-size-check`), sequential calls that could run in parallel, missing or wrong timeouts (`timeout-budget-check`), chatty calls inside loops, cache misses, cold starts, and pool sizes that are too small.
5. Fix the largest contributor first, then measure again the same way. Stop when the target is met; do not optimise paths that are already within budget.

## Inputs

- `target`: endpoint, job, query or service path.
- `target_latency` (optional): the SLO or budget, for example "p95 under 300 ms".

## Outputs

Baseline and after numbers (percentiles, window, environment), a time breakdown of a representative slow request, and findings ordered by time saved, each with evidence and the fix.

## Constraints

- Averages hide tail latency; always report p95 and p99.
- Profiling or tracing in production must be read-only and low overhead; ask before enabling anything that changes production behaviour.
- A fix that moves work elsewhere (for example to a background job) must say where the time went.

## Examples

### Example 1

Input: "GET /orders p95 went from 250 ms to 1.4 s"

Output: Trace of a slow request: 1.1 s in 61 queries, one per order line (N+1 introduced by a new serializer field). Prefetching the lines reduces it to 3 queries. Staging with production-sized data: p95 260 ms after the fix, over 30 minutes.
