---
name: input-validation-check
description: "Check that request data is validated at the system boundary for type, length, range, format, and allowed values before business logic runs. Use when reviewing a new endpoint, form handler, CLI command, or message consumer."
---

# input-validation-check

## Instructions

Identify the repo's validation layer (schema library, serializers, DTOs, form objects). For each input field, confirm type, required/optional, length and size limits, numeric range, enum allowlists, and format. Check file uploads for size, type sniffing (not just extension), and storage path safety. Confirm validation errors return a clear 4xx with field-level messages, not a 500.

## Inputs

- `target`: endpoint, handler, or consumer to check.

## Outputs

A per-field table of missing validations, with `file:line` references.

## Constraints

- Client-side validation is a convenience, not a control.
- Unbounded strings and arrays are a denial-of-service risk as well as a data-quality one.

## Examples

### Example 1

Input: a new `POST /profile` endpoint accepting `bio`, `age`, and an avatar upload

Output: Flagged: `bio` has no max length, `age` accepts negatives, and the avatar type is trusted from the filename; add limits and sniff the file's content type.
