---
name: error-state-actionability-check
description: "Check that a UI error message tells the user what to do next, not just what failed — distinct from checking whether the message leaks sensitive data."
---

# error-state-actionability-check

## Instructions

For each user-facing error, check whether it implies an action: retry, check a specific field, wait, or contact support with a reference id. Cross-check against `pii-response-leak-check` when a message needs rewriting for both safety and actionability.

## Inputs

- `target`: error message or component to check.

## Outputs

A finding per non-actionable error message, with a suggested actionable rewrite.

## Constraints

- A safe message is not automatically a useful one — check both separately.

## Examples

### Example 1

Input: a toast reading "Failed to save."

Output: Flagged — rewrite to "Failed to save — check your internet connection and try again, or contact support with code ERR-2291."
