---
name: onboarding-doc
description: "Write a getting-started guide that takes a new contributor from clone to running, testing, and shipping a first change, verified against the repo's actual tooling. Use when asked to write onboarding docs, improve a README's setup section, or document how to run the project."
---

# onboarding-doc

## Instructions

1. Read the build files, scripts, env examples, container files, and CI config to find the real setup steps.
2. List prerequisites with versions, as pinned in the repo (`.nvmrc`, `.tool-versions`, `pyproject.toml`, and so on).
3. Write setup, run, test, and lint commands exactly as they work; run them to check where possible.
4. Explain required environment variables with safe example values (never real secrets) and where real ones come from.
5. Add a short architecture overview, where to find things, and how changes get reviewed and deployed.
6. Save to the repo's existing docs location (`CONTRIBUTING.md`, `docs/`), matching its style.

## Inputs

- `scope` (optional): the repo or a sub-project.

## Outputs

An onboarding guide with Prerequisites, Setup, Running, Testing, Configuration, Project layout, and Workflow.

## Constraints

- Every command must be one the repo actually supports; don't invent scripts.
- Flag any step that failed or couldn't be checked instead of presenting it as working.
- Only run read-only checks (e.g. printing tool versions or listing scripts). Ask before running anything that installs dependencies, runs migrations or seeds, starts services, or changes the machine.

## Examples

### Example 1

Input: "write onboarding docs for this repo"

Output: `CONTRIBUTING.md` with Node 20 (from `.nvmrc`), `pnpm install`, `pnpm dev`, `pnpm test`, a table of the 6 required env vars from `.env.example`, and a note that `pnpm db:seed` needs a running Postgres from `docker compose up db`.
