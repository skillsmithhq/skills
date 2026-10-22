---
name: loading-state-consistency-check
description: "Check for a race between a loading flag and stale data — a component that clears \"loading\" before new data has actually replaced the old, showing outdated content as if it were current."
---

# loading-state-consistency-check

## Instructions

Check for a request-id/AbortController guard discarding a stale response. Check that an artificial minimum-loading-time delay doesn't itself introduce a different misleading state.

## Inputs

- `target`: component or hook fetching async data.

## Outputs

A finding on the specific race condition and the missing guard.

## Constraints

- A fast response should not be blocked by a fixed minimum-loading delay just to avoid a flash.

## Examples

### Example 1

Input: a search box firing a request on every keystroke with no request-id check.

Output: Flagged — a stale response for an earlier keystroke can resolve after a newer one and overwrite it; add a request-id guard that discards out-of-order responses.
