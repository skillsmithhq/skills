---
name: rate-limit-check
description: "Check that expensive, abusable, or authentication-related endpoints have rate limits and that the limit key can't be trivially bypassed. Use when reviewing login, signup, password reset, OTP, search, export, or any endpoint that sends email/SMS or calls a paid API."
---

# rate-limit-check

## Instructions

Identify the repo's existing rate-limiting mechanism (gateway, middleware, library) before suggesting anything. For each sensitive endpoint, confirm a limit exists, what it is keyed on (user, IP, account, token), and whether the key can be spoofed (e.g. trusting `X-Forwarded-For` without a trusted proxy). Check that limited responses return a clear status and don't leak whether an account exists.

## Inputs

- `target`: endpoint or set of endpoints to check.

## Outputs

A table of endpoints with current limit, key, and a finding where the limit is missing or bypassable.

## Constraints

- Don't introduce a new rate-limiting system into a repo that has none; flag it as an architecture decision.
- A per-IP limit alone doesn't protect a single targeted account.

## Examples

### Example 1

Input: "check rate limiting on the password reset flow"

Output: Flagged: reset-email sending is limited per IP only, so an attacker rotating IPs can flood one user's inbox; add a per-account limit alongside it.
