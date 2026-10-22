---
name: currency-round-trip-check
description: "Check money-conversion code for round-trip rounding error: recomputing an amount by dividing an already-rounded intermediate value back through a conversion rate amplifies the rounding error instead of reproducing the original."
---

# currency-round-trip-check

## Instructions

Find any place a stored, already-rounded amount is divided back through the same rate to derive a related amount. Confirm the derived value instead comes from the original unrounded amount, not a reversal of the rounded one.

## Inputs

- `target`: file or function doing currency conversion.

## Outputs

A finding naming the specific `file:line` doing the reversal, with the fix (derive from the unrounded source value).

## Constraints

- Applies to any "round then reverse" chain, not only currency.

## Examples

### Example 1

Input: `payable_amount = converted_amount / conversion_rate` where `converted_amount` was already rounded.

Output: Flagged — `payable_amount` should be computed from the original pre-rounding amount, not derived by dividing the rounded `converted_amount` back through the rate.
