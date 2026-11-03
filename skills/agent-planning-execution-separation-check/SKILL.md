---
name: agent-planning-execution-separation-check
description: "Check whether a complex agentic task separates planning (decide the steps) from execution (carry them out), making the plan inspectable before real-world actions start. Use when reviewing an agent that takes consequential real-world actions."
---

# agent-planning-execution-separation-check

## Instructions

Read the agent's control flow in whatever framework it uses. Check whether the design can produce an explicit plan as a distinct artifact before execution, at least for consequential actions. Where a plan exists, check it's actually surfaced for review, not generated and immediately executed with no gap.

## Inputs

- `target`: the agent design to check for plan/execute separation.

## Outputs

A finding on conflated planning/execution for a consequential-action agent, or on a plan that's technically produced but never actually reviewable.

## Constraints

- Cross-reference `non-determinism-boundary-check` for which actions count as consequential enough to require this.

## Examples

### Example 1

Input: an agent that decides and immediately issues each customer refund with no separate plan step.

Output: Flagged — for refunds above a threshold, generate an explicit plan first and require a human review gate before execution.
