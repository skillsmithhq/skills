---
name: branch-environment-promotion-check
description: "Check that the mapping from branch/tag pattern to deployed environment is unambiguous, so a change can't accidentally deploy to production via an overly broad trigger."
---

# branch-environment-promotion-check

## Instructions

Check the actual glob/regex pattern each trigger matches, not just its intent. Check for overlapping triggers and confirm which wins. Check that a production trigger requires more than a branch-name pattern alone where risk warrants it (manual approval, specific tag format).

## Inputs

- `target`: the deploy trigger configuration to check.

## Outputs

A finding on an overly broad or overlapping trigger pattern.

## Constraints

- Pipeline systems differ on first-match vs. last-match vs. all-match for overlapping triggers — don't assume only one fires.

## Examples

### Example 1

Input: a production deploy trigger on pattern `release-*` that also matches a developer's branch `release-testing-something`.

Output: Flagged — tighten the pattern or add a manual approval gate before this trigger can reach production.
