---
name: agent-orchestration-topology-check
description: "Check that a multi-agent system's control-flow shape (fixed pipeline, hierarchical supervisor, peer negotiation) actually matches how structured or open-ended the underlying task is."
---

# agent-orchestration-topology-check

## Instructions

Determine whether the task is fixed-sequence, needs dynamic replanning, or has bounded task-type variation, and check the implementation's topology matches. Check that a supervisor's routing is deterministic code when the routing rule itself is simple and static, not a model call on every request.

## Inputs

- `target`: the multi-agent design to check.

## Outputs

A finding on topology mismatch, naming the task shape and the recommended structure.

## Constraints

- A free-form multi-agent conversation for a fixed-sequence task adds cost and non-determinism with no benefit.

## Examples

### Example 1

Input: a document-extraction pipeline with fixed steps (extract text → parse fields → validate) implemented as a free-form multi-agent chat.

Output: Flagged — the steps never change order; replace the chat with a deterministic pipeline that calls the model once per step.
