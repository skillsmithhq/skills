---
name: dependency-upgrade-plan
description: "Plan a major dependency or framework upgrade: what breaks, in what order to change things, and how to ship it safely. Use when asked to upgrade a framework, language runtime, or major library version."
---

# dependency-upgrade-plan

## Instructions

1. Read the official changelog and migration guide for every version being skipped.
2. Search the codebase for each breaking change and deprecated API, and count usages.
3. Check transitive dependencies and plugins for compatibility with the target version.
4. Order the work: fix deprecations on the current version first, then upgrade, then adopt new APIs.
5. Define verification (tests, smoke checks) and a rollback path, and say whether it can ship incrementally.

## Inputs

- `dependency`: the package and target version.
- `scope` (optional): the repo or service.

## Outputs

An upgrade plan listing breaking changes with usage counts and locations, blocking dependencies, ordered steps, and verification and rollback.

## Constraints

- Base the breaking-change list on the official migration guide plus a code search, not memory.
- Don't combine the upgrade with unrelated refactors in one change.

## Examples

### Example 1

Input: "plan the upgrade from React 17 to 18"

Output: Plan: 14 `ReactDOM.render` call sites to migrate to `createRoot`, one test helper relying on synchronous rendering, and one charting plugin without React 18 support; fix that plugin first, then upgrade.
