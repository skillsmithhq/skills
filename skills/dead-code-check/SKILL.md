---
name: dead-code-check
description: "Find code that is never executed or referenced (unused functions, exports, files, feature flags, config keys, and endpoints) and confirm it's safe to remove. Use when cleaning up a module, after a feature is retired, or when asked to find unused code."
---

# dead-code-check

## Instructions

Use the language's tooling where available (unused-export detectors, coverage reports, compiler warnings), then confirm each candidate with a repo-wide search including dynamic references: reflection, string-based lookups, templates, config files, routes, and other repos or clients that call public APIs. Check feature flags that have been fully on or off for a long time. For endpoints, check access logs if available before removing.

## Inputs

- `scope`: directory, module, or service to check.

## Outputs

A list of removal candidates, each marked confirmed-unused or needs-verification, with the evidence.

## Constraints

- A symbol with no static references may still be called dynamically or from outside the repo.
- Public API endpoints need usage evidence, not just a code search.

## Examples

### Example 1

Input: "find dead code in the notifications module"

Output: Confirmed unused: `send_legacy_digest()` and its template (no references; its flag has been off for 8 months). Needs verification: `GET /notifications/summary` has no internal callers but may be used by the mobile app.
