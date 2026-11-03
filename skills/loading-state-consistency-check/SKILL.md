---
name: loading-state-consistency-check
description: "Check for a race between a loading flag and stale data — a component that clears \"loading\" before new data has actually replaced the old, showing outdated content as if it were current. Use when reviewing a UI component or hook that fetches data asynchronously."
---

# loading-state-consistency-check

## Instructions

Identify the repo's UI framework and data-fetching approach (e.g. a query/cache library, a state store, or hand-written fetch calls) and use its own idioms. Check that the loading flag is cleared only after the new data has replaced the old, and that old data is hidden or marked stale while a new request is in flight. Check for a guard that discards a stale response (a request id, or cancellation such as `AbortController` on the web). Check that an artificial minimum-loading-time delay doesn't itself introduce a different misleading state.

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
