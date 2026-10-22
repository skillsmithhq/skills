---
name: form-validation-timing-check
description: "Check when a form field's validation actually fires — on every keystroke, on blur, or only on submit — since the wrong timing makes a technically-correct validator feel punishing or feel broken."
---

# form-validation-timing-check

## Instructions

Match validation timing to error type: format/required checks on blur, not every keystroke; a request-backed check (e.g. username availability) debounced or on blur, never on every keystroke.

## Inputs

- `target`: form or field validation to check.

## Outputs

A finding on mismatched validation timing per field.

## Constraints

- A request-backed validator firing on every keystroke risks a request storm.

## Examples

### Example 1

Input: an email field showing "invalid email" while the user is still typing, before the `@` is entered.

Output: Flagged — move validation to fire on blur instead of on every keystroke.
