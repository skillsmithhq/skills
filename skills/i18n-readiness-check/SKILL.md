---
name: i18n-readiness-check
description: "Check UI and message code for hard-coded strings, concatenated sentences, locale-unaware formatting of dates/numbers/currency, and layouts that break with longer text or right-to-left scripts. Use when reviewing user-facing text in an app that is or will be localised."
---

# i18n-readiness-check

## Instructions

Identify the repo's i18n library and message catalogue. Find user-visible strings not passed through it, sentences built by concatenating fragments (which breaks word order in other languages), plurals handled with `if count == 1`, and dates, numbers, and currency formatted manually. Check that layouts tolerate roughly 30-40% longer text and that RTL is handled if supported.

## Inputs

- `target`: component, template, or diff to check.

## Outputs

A `file:line` finding per issue, grouped by type (hard-coded, concatenation, plural, formatting, layout).

## Constraints

- String concatenation that reads fine in English often can't be translated correctly.
- If the repo has no i18n setup, report that once rather than flagging every string.

## Examples

### Example 1

Input: a notification banner rendering `"You have " + n + " new message" + (n > 1 ? "s" : "")`

Output: Flagged: concatenation and an English-only plural rule; use the i18n library's plural-aware message with a placeholder.
