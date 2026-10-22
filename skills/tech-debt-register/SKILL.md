---
name: tech-debt-register
description: "Find, describe, and prioritise technical debt in a codebase area as a register of concrete items with cost, risk, and a suggested fix. Use when asked to assess tech debt, plan a cleanup, or justify refactoring time."
---

# tech-debt-register

## Instructions

Scan the target area for concrete debt: TODO/FIXME/HACK markers, duplicated logic, dead code, outdated dependencies, missing tests around frequently changed files (use git history to measure churn), oversized modules, and workarounds for bugs that are already fixed upstream. For each item, estimate the ongoing cost (how often it slows work or causes bugs) and the effort to fix. Rank by cost-to-effort ratio.

## Inputs

- `scope`: the directory, module, or service to assess.

## Outputs

A ranked table of items with location, description, ongoing cost, fix effort, and suggested fix.

## Constraints

- Every item must point to real files; no generic 'improve code quality' entries.
- Old code that never changes and never breaks isn't urgent debt.

## Examples

### Example 1

Input: "assess tech debt in the billing module"

Output: Top item: invoice rounding is implemented three times with different rules (`billing/invoice.py:88`, `reports/totals.py:41`, `exports/csv.py:120`), touched in 9 of the last 20 bug fixes; consolidate into one function with tests.
