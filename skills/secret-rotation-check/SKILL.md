---
name: secret-rotation-check
description: "After a secret is rotated, check it was actually replaced everywhere it's used — not just the primary secret store — since a partial rotation leaves a working old credential."
---

# secret-rotation-check

## Instructions

Check for services caching the secret at startup needing a restart, CI/CD variables holding a separate copy, and any hardcoded fallback value. Confirm the old secret is actually revoked at the provider, not just superseded.

## Inputs

- `target`: the secret that was rotated.

## Outputs

A checklist of consumers confirmed updated, and confirmation the old secret is revoked.

## Constraints

- Adding a new key without disabling the old one leaves the old one still usable.
- Never print a secret's full value in findings or chat: report its location, type, and a masked form showing at most the first and last four characters.

## Examples

### Example 1

Input: a database password rotated in the secrets manager.

Output: Flagged — the CI pipeline holds its own copy of the old password in a separate variable and wasn't updated; the app also needs a restart to pick up the new value since it's cached at startup.
