---
name: responsive-layout-check
description: "Check that a UI change works across screen sizes, orientations, zoom levels, and touch input: no horizontal scroll, readable text, reachable controls, and adequate tap targets. Use when reviewing CSS, layout components, or a new page."
---

# responsive-layout-check

## Instructions

Identify the repo's breakpoints and layout system. Check fixed widths and heights that overflow narrow screens, tables and code blocks without overflow handling, text that doesn't wrap, tap targets under about 44×44 px, hover-only interactions with no touch equivalent, and content hidden at some sizes without an alternative. Check 200% browser zoom keeps content usable.

## Inputs

- `target`: page, component, or stylesheet to check.

## Outputs

A finding per breakpoint or input mode where layout or interaction fails, with the CSS or component fix.

## Constraints

- Testing only at desktop width and one phone width misses tablets and zoom.
- Hover menus are unreachable on touch devices.

## Examples

### Example 1

Input: a new pricing table with four fixed-width columns

Output: Flagged: the table forces horizontal page scroll below 900 px; stack plans vertically on narrow screens or give the table its own scroll container.
