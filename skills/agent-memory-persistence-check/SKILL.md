---
name: agent-memory-persistence-check
description: "Check that an agent's persisted memory/state is scoped per user/tenant and doesn't grow unbounded, and that corrected facts don't sit alongside stale ones with no way to tell which is current."
---

# agent-memory-persistence-check

## Instructions

Check the memory store is scoped per caller, the same class of check as `cache-key-scoping-check` but for long-lived agent memory. Check for eviction/summarization of old entries. Check that a corrected fact replaces or supersedes the old one rather than both persisting.

## Inputs

- `target`: the agent memory/state storage to check.

## Outputs

A finding on scoping, unbounded growth, or stale-fact handling.

## Constraints

- Agent memory is easy to leave unscoped by default since it's often built as a system-level store.

## Examples

### Example 1

Input: an agent memory store keyed only by a fact string, with no user/tenant field.

Output: Flagged — two different users' corrected facts about the same topic would overwrite or merge with each other; add a per-user/tenant scope to the key.
