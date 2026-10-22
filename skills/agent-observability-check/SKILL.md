---
name: agent-observability-check
description: "Check that an agentic pipeline logs each decision point — tool calls, reasoning/plan, results — in enough detail to reconstruct after the fact why the agent took a given action."
---

# agent-observability-check

## Instructions

Check each step records its input context, chosen tool and arguments, and raw result — not just a final summary. Check this is captured on failure paths too, not only the happy path. Check logged traces don't leak sensitive data into a less-protected trace store.

## Inputs

- `target`: the agentic pipeline's logging/tracing to check.

## Outputs

A finding on missing per-step trace detail, especially on failure paths, or on trace-store data exposure.

## Constraints

- Cross-reference `pii-response-leak-check` for sensitive data captured verbatim in traces.

## Examples

### Example 1

Input: an agent pipeline that only logs "task failed" with no record of which tool call failed or why.

Output: Flagged — add per-step logging of tool name, arguments, and raw result, especially on the failure path where this detail matters most.
