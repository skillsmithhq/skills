---
name: cicd-bypass-audit-check
description: "Check whether a merge/deploy can bypass a required CI check (admin override, \"skip ci\" tag, manual trigger) and whether that bypass is logged/audited."
---

# cicd-bypass-audit-check

## Instructions

Identify the actual override path and who can use it. Check that using it leaves an audit trail. Check whether the override is scoped to genuine emergencies or is broad enough to get used routinely, which means the check isn't actually required in practice.

## Inputs

- `target`: the bypass/override mechanism to check.

## Outputs

A finding on a bypass path with no audit trail, or one used routinely enough to defeat the required check.

## Constraints

- A bypass with no record of who used it and why is indistinguishable after the fact from the check never existing.

## Examples

### Example 1

Input: an admin merge button that skips required-check enforcement, with no log of when it's used.

Output: Flagged — add an audit log entry whenever the override is used, and review how often it's actually invoked to confirm the required check isn't being routinely bypassed.
