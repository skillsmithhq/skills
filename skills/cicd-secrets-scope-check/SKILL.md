---
name: cicd-secrets-scope-check
description: "Check that CI/CD secrets are scoped to only the specific job/stage that needs them, not exposed pipeline-wide, and never printed to build logs."
---

# cicd-secrets-scope-check

## Instructions

Check the secret's actual scope against which job uses it, narrowing if broader than needed. Check for the secret leaking via a debug/verbose command echoing environment variables or config into logs.

## Inputs

- `target`: the pipeline config to check.

## Outputs

A finding on over-broad secret scope or a log-leak path.

## Constraints

- CI logs are often more widely readable than the secret store itself — a log leak is a real exposure.
- Never print a secret's full value in findings or chat: report its location, type, and a masked form showing at most the first and last four characters.

## Examples

### Example 1

Input: a deploy secret defined at the workflow level, used only in the final deploy job.

Output: Flagged — narrow the secret's scope to the deploy job only; earlier jobs (lint, test) don't need access to it.
