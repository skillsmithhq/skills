---
name: ssrf-check
description: "Check server-side code that fetches a URL supplied or influenced by a user (webhooks, previews, imports, image fetchers) for server-side request forgery. Use when reviewing any feature where the server makes an outbound request to a caller-controlled address."
---

# ssrf-check

## Instructions

Find every outbound request whose host, scheme, or path comes from user input. Confirm the target is resolved and checked against a deny list for private, loopback, link-local, and cloud metadata ranges after DNS resolution, that redirects are re-validated or disabled, and that only http/https schemes are allowed. Check timeouts and response size limits.

## Inputs

- `target`: the feature or code that makes outbound requests.

## Outputs

A finding per unprotected fetch, naming which check is missing (scheme, resolved-IP range, redirect, timeout, size).

## Constraints

- Checking the hostname string before DNS resolution is bypassable; validate the resolved address.
- Cloud metadata endpoints are the usual prize; treat them as the first thing to block.

## Examples

### Example 1

Input: "add a link-preview feature that fetches the page title"

Output: Flagged: the fetcher follows redirects and doesn't check resolved IPs, so a URL redirecting to the cloud metadata address would be fetched; block private ranges after resolution and re-check on each redirect.
