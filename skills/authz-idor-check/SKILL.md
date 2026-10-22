---
name: authz-idor-check
description: "Check that every endpoint that loads a resource by id confirms the caller is allowed to access that specific resource, not just that they are logged in. Use when reviewing a new or changed endpoint, handler, or GraphQL resolver that takes an id from the request."
---

# authz-idor-check

## Instructions

Identify the repo's authorization mechanism first (policy classes, decorators, middleware, row-level security). For each id taken from the path, query string, body, or headers, trace the lookup and confirm it is filtered by the caller's ownership or role before use. Check list endpoints for the same filter, and check that nested or related ids (e.g. `/orders/{id}/items/{item_id}`) are validated against the parent.

## Inputs

- `target`: endpoint, handler, resolver, or diff to check.

## Outputs

A `file:line` finding per lookup that trusts a caller-supplied id without an ownership or permission check.

## Constraints

- Authentication is not authorization: a valid session says nothing about which records the caller may see.
- Don't assume a sibling endpoint's check covers this one.

## Examples

### Example 1

Input: "review the new GET /invoices/{id} endpoint"

Output: Finding at `invoices_handler.py:22`: the invoice is fetched by id alone, so any logged-in user can read any invoice by changing the id; filter the lookup by the caller's account.
