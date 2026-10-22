---
name: single-point-of-failure-check
description: "Check a new architecture/design for a component with no redundancy that everything depends on, and confirm whether that's a deliberate, accepted tradeoff or an oversight."
---

# single-point-of-failure-check

## Instructions

Trace the design's dependency graph for anything every flow passes through with no fallback. Name each SPOF, state what happens when it's down, and confirm it was an explicit decision rather than an unexamined side effect.

## Inputs

- `target`: the design/proposal to check.

## Outputs

A list of identified SPOFs, each with the failure impact and whether it's confirmed as an accepted tradeoff.

## Constraints

- The goal is making the tradeoff explicit, not eliminating every SPOF regardless of cost.

## Examples

### Example 1

Input: a new integration proposal routing all requests through a single third-party API with no cached fallback.

Output: Flagged — if that API is down, the entire feature fails with no degraded mode; confirm this is an accepted v1 tradeoff before shipping.
