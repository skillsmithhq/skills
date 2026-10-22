---
name: audit-trail-purge-check
description: "Before deleting/purging records across multiple services, check whether each service's audit/log records are FK-cascaded (deleted with the parent) or decoupled (survive and need separate handling)."
---

# audit-trail-purge-check

## Instructions

For each service touched by the purge, check the actual FK relationship on its audit/log table. Where logs are decoupled, decide explicitly: purge separately, anonymize, or leave with a documented reason. Check for any discrete numbering/sequence counter tied to the purged records that could leave unexplained gaps.

## Inputs

- `target`: the purge script or deletion feature to review.

## Outputs

A per-service finding: cascaded vs. decoupled, and the explicit decision for decoupled logs.

## Constraints

- Don't assume all services behave the same way just because the data model looks similar.

## Examples

### Example 1

Input: a purge script deleting closed customer accounts across the accounts service and the billing service.

Output: Flagged — the accounts service's audit logs are decoupled (they survive the purge, now orphaned); the billing service's are FK-cascaded (deleted automatically). Recommend explicit handling for the orphaned logs.
