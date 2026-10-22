---
name: multi-agent-handoff-check
description: "Check that when one agent delegates to another, the handoff carries enough context to act correctly, and that task ownership doesn't become ambiguous."
---

# multi-agent-handoff-check

## Instructions

Check what context crosses the handoff boundary — task, constraints, prior findings — not just a narrow sub-task string. Check whether the delegator still verifies the outcome or assumes the receiver did. Check the defined response when the receiving agent fails or times out.

## Inputs

- `target`: the agent handoff/delegation point to check.

## Outputs

A finding on missing context, ambiguous ownership, or an undefined failure/timeout response.

## Constraints

- A gap where both agents assume the other handles error-checking silently drops error handling a single-agent design wouldn't lose.

## Examples

### Example 1

Input: an orchestrator delegating "draft a reply to this support ticket" to a sub-agent without passing the customer's plan or the refund policy.

Output: Flagged — the sub-agent can't apply plan-specific rules it never received; pass the required context explicitly in the handoff instead of assuming shared memory.
