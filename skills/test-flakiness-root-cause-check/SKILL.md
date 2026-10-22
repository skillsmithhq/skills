---
name: test-flakiness-root-cause-check
description: "Find the actual cause of a flaky test (timing/order dependence, shared mutable state, unmocked clock/network) instead of retrying or skipping it."
---

# test-flakiness-root-cause-check

## Instructions

Check for an async/assertion race, order/state dependence on a previous test, or an unmocked clock/random seed. Distinguish "badly written test" from "correctly catching a real race in the code" before quarantining.

## Inputs

- `target`: the flaky test to diagnose.

## Outputs

A diagnosis naming the specific cause, and whether quarantining would hide a real bug.

## Constraints

- Never quarantine a test that's correctly exposing a real race in the code under test.

## Examples

### Example 1

Input: a test that fails roughly 1 in 20 runs with no code change.

Output: Diagnosed — an async write isn't awaited before the following assertion reads; fix the race instead of adding a retry wrapper.
