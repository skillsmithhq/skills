---
name: security-boundary-review
description: "Locate the repo's actual inter-service auth mechanism and confirm a changed endpoint uses it, then check the gaps that pass a casual read: permission classes that check auth but not resource/tenant ownership, serializer field exposure from a recently added column, and rate limiting only where a convention already exists."
---

# security-boundary-review

## Instructions

Confirm the real inter-service auth mechanism before reviewing — don't assume from another repo. Check resource-ownership scope beyond authentication. Check any serializer, DTO, or response model that exposes all fields by default (e.g. DRF `fields = "__all__"`, returning ORM objects directly) against the model's current columns. If the system is multi-tenant, also confirm every query on the touched data is scoped to the caller's tenant.

## Inputs

- `target`: endpoint, view, or diff to review.

## Outputs

A `file:line` finding per gap.

## Constraints

- Don't propose a new rate-limiting mechanism for a repo that has none.

## Examples

### Example 1

Input: "review this new webhook endpoint for security"

Output: Finding at `serializer.py:8` — `fields = "__all__"` now exposes an internal `stripe_customer_id` column added since the serializer was last touched.
