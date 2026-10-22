---
name: deploy-rollback-readiness-check
description: "Before shipping a risky change, check that the deployment pipeline has a genuinely fast, tested rollback path — not just \"revert and redeploy,\" which can be too slow for an incident."
---

# deploy-rollback-readiness-check

## Instructions

Check whether a faster path exists (redeploying a previous artifact, a feature-flag kill switch, traffic-routing rollback) versus the full CI pipeline every time. Check whether an accompanying migration/data change makes the rollback incomplete even if code reverts instantly.

## Inputs

- `target`: the deployment plan to check.

## Outputs

A finding on rollback speed and on any data/migration change that isn't covered by a code-only rollback.

## Constraints

- A rollback plan that's never been exercised isn't confirmed to work.

## Examples

### Example 1

Input: a risky release with a rollback plan of "revert the commit and let CI redeploy" (20-minute pipeline).

Output: Flagged — recommend a faster path (redeploy the previous image directly) for use during an active incident, and confirm the accompanying migration is backward compatible if rolled back.
