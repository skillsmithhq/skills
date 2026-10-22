---
name: non-determinism-boundary-check
description: "Check where a system draws the line between deterministic business logic and non-deterministic model output — money, permissions, and irreversible actions should be enforced in deterministic code, with model output as input to that logic, never the final authority."
---

# non-determinism-boundary-check

## Instructions

Classify each model-influenced decision: does deterministic code re-verify it against a real business rule, or is the model's output acted on directly? Check for a deterministic ceiling on any model-driven action (a hard cap independent of the model's own reasoning).

## Inputs

- `target`: the feature where model output drives a decision.

## Outputs

A finding naming any consequential decision (money, permissions, irreversible action) taken directly from model output with no deterministic re-check.

## Constraints

- Acceptable for low-stakes, reversible outcomes; a real risk for money, permissions, or irreversible actions.

## Examples

### Example 1

Input: an auto-moderation feature that publishes a user comment whenever the model says "safe".

Output: Flagged — the model's answer is the only gate on an irreversible action; route low-confidence and borderline results to human review and log every decision.
