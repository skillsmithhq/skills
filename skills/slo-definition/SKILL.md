---
name: slo-definition
description: "Define service level indicators, objectives, and an error budget for a service or user journey, grounded in the metrics that already exist. Use when asked to set SLOs, define reliability targets, or decide how reliable a service needs to be."
---

# slo-definition

## Instructions

1. Name the user journeys that matter (e.g. log in, check out, load dashboard).
2. For each, pick an SLI measurable from existing telemetry: success ratio or latency at a percentile, measured as close to the user as possible.
3. Propose an objective using recent data as the baseline, and state the error budget it implies per 28 or 30 days.
4. Define what happens when the budget is spent (freeze risky releases, prioritize reliability work).
5. List the telemetry gaps that block measuring an SLI.

## Inputs

- `service`: the service or journey to define SLOs for.
- `data` (optional): recent metrics or dashboards.

## Outputs

A table of journeys with SLI, objective, error budget, and data source, plus the budget policy and the gaps.

## Constraints

- Never set an objective above what current data shows is achievable without a plan to get there.
- 100% is not an objective.

## Examples

### Example 1

Input: "define SLOs for our checkout API"

Output: Checkout success ratio ≥ 99.5% and p95 latency < 800 ms over 28 days (current: 99.7%, 620 ms), giving a 0.5% error budget, with a release freeze once it is exhausted.
