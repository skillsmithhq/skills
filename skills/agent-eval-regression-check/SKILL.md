---
name: agent-eval-regression-check
description: "Check that a prompt or agent behavior change runs against a standing eval set before shipping, since a fix for one case can silently regress a different case that was working before."
---

# agent-eval-regression-check

## Instructions

Check whether an eval set exists for the prompt/agent being changed. If not, flag it and suggest starting one from known-important cases, including the case that motivated this change. If one exists, confirm the change was actually run against it.

## Inputs

- `target`: the prompt/behavior change to check.

## Outputs

A finding: eval set exists and was run (pass), eval set exists but wasn't run, or no eval set exists at all.

## Constraints

- A single manually-checked example is not sufficient evidence the change is safe.

## Examples

### Example 1

Input: a prompt edit fixing one misrouted support-ticket category, checked against only that one ticket.

Output: Flagged — no eval set exists for this classification prompt; build one from labelled tickets across all categories before merging, so a fix for one category can't silently break another.
