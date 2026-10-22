---
name: bounded-context-check
description: "Check whether a shared-sounding concept (Customer, Request, Account) actually means the same thing across the services that use it, or has quietly diverged with no explicit translation between them."
---

# bounded-context-check

## Instructions

For any cross-service call or shared model, check whether both sides agree on the concept's definition. Where they differ, add an explicit translation/mapping layer at the boundary rather than renaming a field to paper over the mismatch.

## Inputs

- `target`: the shared concept or cross-service integration to check.

## Outputs

A finding naming the specific divergence in meaning and the recommended translation boundary.

## Constraints

- Renaming a field to "fix" the mismatch just relabels the problem instead of resolving it.

## Examples

### Example 1

Input: the orders service's "Account" (a paying customer) vs. the auth service's "Account" (a login identity that may belong to many customers).

Output: Flagged — the two meanings only partially overlap; add an explicit mapping at the integration boundary rather than assuming the shared name implies the same concept.
