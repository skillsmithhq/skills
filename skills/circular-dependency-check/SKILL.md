---
name: circular-dependency-check
description: "Check for a circular import/module dependency introduced by a change, including a longer cycle (A→B→C→A), not just a direct two-module cycle."
---

# circular-dependency-check

## Instructions

Check the new import against every module that already transitively imports the module being changed. When a cycle is found, extract the shared piece into a third module, or invert one side's dependency — don't just make the import lazy/deferred.

## Inputs

- `target`: the new import or moved module to check.

## Outputs

A finding naming the cycle's full chain and a recommended structural fix.

## Constraints

- A lazy/deferred import hides a cycle without removing the coupling it signals.

## Examples

### Example 1

Input: `services/billing.py` imports from `services/notifications.py`, which imports from `services/billing.py`.

Output: Flagged as a direct cycle — extract the shared type both need into a new `services/types.py`.
