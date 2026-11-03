---
name: csrf-cors-check
description: "Check CORS and CSRF configuration for overly permissive settings — wildcard origins, disabled CSRF, or credentials allowed alongside a wildcard origin."
---

# csrf-cors-check

## Instructions

Identify the framework's CORS and CSRF mechanism first. Check for a wildcard/overly broad CORS origin allowlist, especially combined with credentials — browsers reject a literal `*` with credentials, so the real risk is usually config that reflects the request's `Origin` header back while allowing credentials. Check for CSRF protection disabled on any state-changing endpoint. Confirm server-to-server-only endpoints aren't reachable from a browser context at all.

## Inputs

- `target`: CORS/CSRF config or new endpoint to check.

## Outputs

A finding per misconfiguration, naming the specific setting.

## Constraints

- A server-to-server endpoint doesn't need CORS/CSRF hardening if it's genuinely unreachable from a browser.

## Examples

### Example 1

Input: a CSRF exemption (e.g. Django's `csrf_exempt` decorator) left on an endpoint after a one-off integration fix.

Output: Flagged — the endpoint now accepts state-changing requests with no CSRF protection; check if the original integration issue has a proper token-based fix available.
