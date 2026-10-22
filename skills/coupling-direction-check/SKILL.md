---
name: coupling-direction-check
description: "Check that a new dependency respects the codebase's intended layering direction — e.g. a domain layer should not import from an API/presentation layer."
---

# coupling-direction-check

## Instructions

Identify the codebase's actual intended layering from its existing structure. Check whether the new import goes the wrong direction (an inner layer importing an outer-layer type).

## Inputs

- `target`: the new cross-layer import to check.

## Outputs

A finding naming the specific import and the layering rule it violates.

## Constraints

- Each individual violation looks small; the cost compounds as it becomes precedent for further violations.

## Examples

### Example 1

Input: a domain-layer service importing a DRF serializer class to reuse a validation helper.

Output: Flagged — move the validation helper into the domain layer itself so the dependency points outward from the API layer, not inward.
