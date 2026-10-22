---
name: prompt-versioning-check
description: "Check that production prompts are tracked as versioned, reviewable artifacts in one place, not duplicated as inline strings across the codebase with no single source of truth."
---

# prompt-versioning-check

## Instructions

Check whether the prompt lives in one version-controlled location versus multiple independently-edited copies. Check that prompt changes go through the same review/rollback path as code. Cross-reference `agent-eval-regression-check` — versioning enables tracing a bad change; the eval set confirms a change is safe before it ships.

## Inputs

- `target`: the prompt storage/change process to check.

## Outputs

A finding on prompt duplication or missing review/rollback path.

## Constraints

- A live-reloaded prompt config with no diff/history can't be traced back as "what changed right before behavior got worse."

## Examples

### Example 1

Input: the same categorization prompt duplicated with small differences across three call sites.

Output: Flagged — consolidate into one versioned prompt source; the three copies have already silently diverged.
