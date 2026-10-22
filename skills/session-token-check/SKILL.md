---
name: session-token-check
description: "Check how sessions and tokens (cookies, JWTs, API keys, refresh tokens) are issued, stored, validated, and revoked. Use when reviewing authentication changes, token handling, logout, or 'remember me' features."
---

# session-token-check

## Instructions

Identify the auth library and token type in use. Check: cookies set `HttpOnly`, `Secure`, and an appropriate `SameSite`; JWT signature and algorithm are verified (no `none`, no algorithm taken from the token header), and `exp`/`aud`/`iss` are checked; tokens aren't stored in `localStorage` when a cookie would do; logout and password change actually revoke server-side state; refresh tokens rotate and are bound to the client.

## Inputs

- `target`: auth code, middleware, or diff to check.

## Outputs

A `file:line` finding per weakness, ranked by exploitability.

## Constraints

- Decoding a JWT is not verifying it.
- A short access-token lifetime doesn't help if the refresh token never expires or rotates.
- Never print a secret's full value in findings or chat: report its location, type, and a masked form showing at most the first and last four characters.

## Examples

### Example 1

Input: "review the new JWT middleware"

Output: Finding at `auth/middleware.ts:31`: the token is decoded with `jwt.decode` and `exp` is never checked, so expired tokens keep working; switch to `jwt.verify` with a pinned algorithm and audience.
