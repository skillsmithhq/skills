---
name: test-isolation-check
description: "Check that tests don't leak state between runs — shared DB rows, module-level caches, or global singletons not reset — causing order-dependent pass/fail."
---

# test-isolation-check

## Instructions

Check for a DB row created by one test and read by another with no explicit setup, an unreset module-level cache/singleton, or a mock/patch left applied after its test finishes. Check parallel-execution races against shared external state specifically if the suite runs concurrently.

## Inputs

- `target`: the test suite or failing test to check.

## Outputs

A finding naming the specific leaked state and which tests it connects.

## Constraints

- The tell is a test passing alone but failing in the full suite, or passing in one run order but not another.

## Examples

### Example 1

Input: a test suite where test order matters — running test B before test A causes A to fail.

Output: Flagged — test B leaves a cached value unreset that test A implicitly depends on; add explicit teardown resetting the cache.
