---
name: load-test-plan
description: "Plan and run a safe load test: targets taken from the SLO or expected traffic, an approved non-production environment, a realistic traffic model, ramp and stop rules, and a report of throughput, latency percentiles, errors and the first bottleneck found. Uses the load-testing tool already in the repo. Use before a launch, a traffic event, or a capacity change, or when asked how much load a service can take."
---

# load-test-plan

## Instructions

1. Detect any load-testing tool already in the repo (for example k6, Locust, Gatling, JMeter or Artillery) and use it. Ask before adding one.
2. Agree the goal with the user: expected peak traffic, growth margin, and pass criteria such as "p95 under 400 ms and errors under 0.5 % at 300 requests per second".
3. Choose the environment and get explicit approval for it. The default is a staging environment sized like production. Never load-test production, a shared environment, or anything the user does not own without written approval from its owner. Replace third-party dependencies (payments, email, model APIs) with stubs or their sandbox modes, because load on them may breach their terms or cost money.
4. Model realistic traffic: the mix of endpoints, think time, data variety (avoid cache-only hits), authentication, and a ramp-up profile. Include a soak run if memory or connection leaks are a concern.
5. Set stop rules before starting: abort on error rate, latency, or resource limits, and have someone able to stop the test. Warn the team or on-call that the test is running.
6. Run it in steps: smoke run at low load, ramp to target, then beyond target to find the breaking point if agreed. Watch server-side metrics (CPU, memory, database connections, queue depth) as well as the client results.
7. Clean up test data and stop any load generators afterwards.

## Inputs

- `target`: service or endpoints to test.
- `goal`: expected peak and pass criteria (asked if not given).
- `environment`: where to run (asked; must be approved).

## Outputs

A test plan (goal, environment, traffic model, ramp, stop rules, approvals) and, after the run, a report: throughput, p50/p95/p99 latency and error rate per step, the first bottleneck with evidence, pass or fail against the criteria, and recommended fixes.

## Constraints

- Load generated from one laptop may limit itself before the server does; check the load generator's CPU and network.
- Results from an environment smaller than production do not scale linearly; say so.
- Unapproved load testing can look like a denial-of-service attack. Do not run without approval.

## Examples

### Example 1

Input: "can checkout survive the sale next week?"

Output: Plan: staging with production-sized database, payments stubbed, 70 % browse, 25 % cart, 5 % checkout, ramp to 3x last sale's peak over 15 minutes, abort above 2 % errors. Result: passed at 2x; at 2.6x, p95 for checkout reached 2.8 s due to database connection-pool exhaustion (pool of 20, all busy). Recommend pool 50 and retest.
