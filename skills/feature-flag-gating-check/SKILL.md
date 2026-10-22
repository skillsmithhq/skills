---
name: feature-flag-gating-check
description: "Check whether a new tenant-visible behavior change should be gated behind the repo's existing feature-flag/tenant-configuration mechanism rather than shipping always-on."
---

# feature-flag-gating-check

## Instructions

Confirm whether the repo has a feature-flag or per-customer configuration mechanism. If the change alters visible behavior and one exists, gate it defaulting off unless told otherwise. Check for interaction with any existing flag on the same code path — enumerate the on/off combination explicitly.

## Inputs

- `target`: the change to check for flag-gating.

## Outputs

A recommendation: gate behind the existing mechanism, ship always-on (with reason), or flag that no mechanism exists.

## Constraints

- Don't invent a new flagging mechanism for a repo that has none — surface that as a bigger decision.

## Examples

### Example 1

Input: a change to search-ranking logic visible to all customers immediately on deploy.

Output: Flagged — gate it behind the existing flag system, defaulting off, so it can be piloted with one customer first.
