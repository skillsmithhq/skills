---
name: api-contract-compat-check
description: "Check whether a change to an API response shape or inter-service payload is additive (safe) or breaking (needs versioning/coordination) for every consumer of that contract."
---

# api-contract-compat-check

## Instructions

Identify every actual consumer of the changed contract, including ones in other repos. Classify the change as additive or breaking. For a breaking change, pick one explicit path: add-alongside-and-deprecate, version the endpoint, or coordinate a simultaneous deploy.

## Inputs

- `target`: the schema, serializer, or payload change to check.

## Outputs

A classification (additive/breaking) with the list of identified consumers and the chosen compatibility path for a breaking change.

## Constraints

- If a consumer can't be identified with confidence, say so rather than assuming the change is isolated.

## Examples

### Example 1

Input: renaming a field in an order-created event published by the orders service and consumed by the shipping service.

Output: Flagged as breaking — the shipping service reads the old field name; add the new field alongside the old one and deprecate on a timeline rather than renaming in place.
