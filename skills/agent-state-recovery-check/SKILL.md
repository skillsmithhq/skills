---
name: agent-state-recovery-check
description: "Check that a long-running agentic workflow can resume after a crash without losing all progress or re-executing already-completed side-effecting steps. Distinct from agent-memory-persistence-check, which is user-facing memory, not in-flight execution state."
---

# agent-state-recovery-check

## Instructions

Check that completed steps are checkpointed before the next step starts, not just at the end. Check resume replays from the last checkpoint, not the beginning. Check specifically for non-idempotent steps that a resume path could re-run.

## Inputs

- `target`: the long-running agent workflow to check.

## Outputs

A finding on missing checkpointing or a resume path that could re-execute a non-idempotent step.

## Constraints

- Cross-reference `idempotency-check` for any step a resume path might repeat.

## Examples

### Example 1

Input: a multi-step agent workflow that sends a notification in step 3, with no checkpoint before step 4.

Output: Flagged — a crash and resume after step 3 would re-run step 3, re-sending the notification; add a checkpoint marking step 3 complete before proceeding.
