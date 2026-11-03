---
name: pipeline-flakiness-check
description: "Check whether a CI pipeline failure is a real regression or environment/infra flakiness, and that a flaky step isn't silently retried/ignored in a way that masks genuine failures. Distinct from test-flakiness-root-cause-check (test logic, not pipeline/infra). Use when a CI job fails intermittently."
---

# pipeline-flakiness-check

## Instructions

Identify the CI system and read its pipeline config and the failing job's logs. Compare the failure across runs of the same commit: a failure that moves between steps or shows timeouts, network or runner errors points to infra; one that repeats in the same test points to code. Check whether a retry is scoped to genuinely transient failures or blanket-retries the whole job including the actual test/build step. Check that an allowed-to-fail step's failures are still visible somewhere, not silently disappearing.

## Inputs

- `target`: the flaky pipeline step to check.

## Outputs

A finding on overly broad retry scope or a silently-ignored failing step.

## Constraints

- A blanket retry on the whole job can mask a real intermittent code bug, not just infra flakiness.

## Examples

### Example 1

Input: a pipeline that retries the entire test job (not just a flaky network-dependent step) up to 3 times.

Output: Flagged — scope the retry to the specific flaky infra call; a blanket job retry gives a real intermittent test bug multiple chances to slip through.
