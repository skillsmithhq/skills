---
name: accessibility-check
description: "Check UI changes for common accessibility failures: missing labels, keyboard traps, focus handling, colour contrast, semantic structure, and screen-reader announcements. Use when reviewing a new component, page, form, or modal in any web or mobile UI framework."
---

# accessibility-check

## Instructions

Check that every interactive element is reachable and operable by keyboard with a visible focus indicator, form fields have associated labels, images have meaningful alt text (or empty alt if decorative), headings form a logical order, colour isn't the only signal, text contrast meets WCAG AA, and dynamic changes (errors, toasts, loading) are announced. For modals, check focus moves in, is trapped, and returns on close. Run the repo's existing a11y linter or test tooling if present.

## Inputs

- `target`: component, page, or diff to check.

## Outputs

A `file:line` finding per failure, each mapped to the WCAG criterion it violates.

## Constraints

- A `div` with an `onClick` is not a button to a keyboard or screen-reader user.
- Automated tools catch only part of the problems; check keyboard flow by reading the code too.

## Examples

### Example 1

Input: a new modal dialog for confirming account deletion

Output: Findings: focus stays on the page behind the modal, Escape doesn't close it, and the destructive button is distinguished only by red colour; move and trap focus, handle Escape, and add explicit text.
