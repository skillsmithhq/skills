---
name: agent-context-window-budget-check
description: "Check that an agent's prompt construction doesn't blindly dump full documents/history into context without a size budget, risking silent truncation of exactly the part that mattered."
---

# agent-context-window-budget-check

## Instructions

Check that variable-length input is size-checked before insertion. Confirm truncation, when it happens, deliberately drops the least important content (oldest turns, summarized overflow) rather than an arbitrary cut. In a tool-use loop, confirm accumulated tool results are capped or summarized, not kept verbatim forever.

## Inputs

- `target`: the prompt-assembly code to check.

## Outputs

A finding on missing size budgeting or unbounded accumulation, with the specific risk.

## Constraints

- Silent truncation is the failure mode to catch — the response looks plausible even when reasoning over incomplete input.

## Examples

### Example 1

Input: an agent that appends every tool call's full result to the running prompt with no cap.

Output: Flagged — recommend summarizing or dropping older tool results once the running context approaches a defined budget.
