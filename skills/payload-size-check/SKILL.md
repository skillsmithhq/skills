---
name: payload-size-check
description: "Check API responses, list endpoints, exports, and messages for unbounded size: missing pagination, over-fetching, large embedded blobs, and no request-body limits. Use when reviewing endpoints that return collections or accept uploads."
---

# payload-size-check

## Instructions

For each response, estimate its size at production data volumes. Confirm list endpoints paginate with a maximum page size, responses don't embed large fields that aren't needed (images, full histories), and compression is enabled where the stack supports it. Confirm request bodies and uploads have size limits enforced before the body is fully read.

## Inputs

- `target`: endpoint, serializer, or message producer to check.

## Outputs

A finding per unbounded payload with its estimated size at scale and the fix.

## Constraints

- An endpoint that's fine with 50 rows in dev can return 50 MB in production.
- A page-size parameter without a server-side maximum is not pagination.

## Examples

### Example 1

Input: a `GET /customers` endpoint returning all customers with their full order history

Output: Flagged: no pagination and order history is embedded; at current volumes that's about 40 MB; paginate with a max of 100 and return an order count with a link instead.
