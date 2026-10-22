---
name: agent-loop-termination-check
description: "Check that an autonomous agent's plan→act→observe loop has a hard termination condition — max iterations, a cost/time budget, or an explicit success/failure signal — rather than relying on the model to decide on its own when it's done."
---

# agent-loop-termination-check

## Instructions

Check for an explicit hard cap independent of the model's judgment. Check what happens when the cap is hit: fails loudly with partial state preserved, or silently stops mid-action with no record — the latter compounds into `agent-state-recovery-check`'s concern.

## Inputs

- `target`: the agent loop or orchestration code to check.

## Outputs

A finding on missing termination cap, or on what happens when the cap is reached.

## Constraints

- A stuck loop with side-effecting actions repeats those actions each pass, not just burns cost.

## Examples

### Example 1

Input: an agent loop that calls tools until the model says "task complete," with no iteration cap.

Output: Flagged — add a max-iteration/cost-budget cap, and ensure hitting it preserves partial progress rather than failing silently.
