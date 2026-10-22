---
name: build-cache-invalidation-check
description: "Check that a CI build cache invalidates correctly when the lockfile changes, so a stale cache doesn't silently ship old dependency versions."
---

# build-cache-invalidation-check

## Instructions

Check the cache key includes a hash of the actual lockfile, not just the manifest. Check for the opposite failure too — an overly specific key (includes something irrelevant) that never hits, silently paying full install cost every run.

## Inputs

- `target`: the CI cache configuration to check.

## Outputs

A finding on the cache key's actual invalidation trigger versus what it should be.

## Constraints

- A manifest-only cache key can miss a lockfile change that resolves differently without the manifest itself changing.

## Examples

### Example 1

Input: a cache key based on `package.json` hash, not `package-lock.json`.

Output: Flagged — a lockfile-only dependency bump won't invalidate the cache; key on the lockfile hash instead.
