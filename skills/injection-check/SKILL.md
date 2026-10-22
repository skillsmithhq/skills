---
name: injection-check
description: "Check for SQL, shell, template, and query-language injection where user input reaches an interpreter. Use when reviewing code that builds queries, shell commands, templates, or filters from request data."
---

# injection-check

## Instructions

Find every place request data reaches an interpreter: raw SQL, ORM raw/extra calls, shell or subprocess calls, template rendering of user strings, LDAP/NoSQL/search query builders, and dynamic sort/filter fields. Confirm each uses parameterization or an allowlist. For dynamic column or sort names, require an allowlist, since placeholders can't parameterize identifiers.

## Inputs

- `target`: diff, file, or feature to check.

## Outputs

A `file:line` finding per injection path, naming the interpreter and the parameterized or allowlisted fix.

## Constraints

- Escaping by hand is not a fix when the driver supports parameters.
- Input that was validated on the client is still untrusted on the server.

## Examples

### Example 1

Input: a report endpoint that builds `ORDER BY` from a `sort` query parameter

Output: Finding: the `sort` value is formatted straight into SQL; replace with an allowlist of sortable columns and reject anything else.
