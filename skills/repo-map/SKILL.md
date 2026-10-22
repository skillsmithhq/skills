---
name: repo-map
description: "Give agents a map of the codebase by writing an AGENTS.md into each significant directory: what that directory is responsible for, and an index of its files with a one-line brief each. Use when asked to map a repo, document the codebase for agents, create or refresh AGENTS.md files, or \"give agents enough context to understand this system\". Also use after a change that adds, removes, renames, or repurposes files in a directory that already has a map."
---

# repo-map

## Instructions

1. List the repo's directories, skipping generated, vendored, and dependency folders (respect `.gitignore`).
2. Pick the significant directories: ones holding source, config, or tests that a contributor would need to navigate. Skip trivial ones with one obvious file.
3. For each, read its files and write `AGENTS.md` with: a 2-3 sentence responsibility statement, the key entry points, and an index of files with a one-line brief each.
4. Note any convention a newcomer would miss (naming rules, where tests live, what must not be imported from here).
5. When refreshing, update only the entries for files that changed, and remove entries for files that no longer exist.

## Inputs

- `scope` (optional): a directory to map; defaults to the whole repo.

## Outputs

One `AGENTS.md` per significant directory, plus a short summary of which directories were mapped and which were skipped.

## Constraints

- Never write to the repository root unless asked; root files usually already exist and are hand-maintained.
- Describe what files actually do, from reading them, not from their names.
- Don't overwrite hand-written sections of an existing AGENTS.md; update the index only.

## Examples

### Example 1

Input: "map this repo so agents can find their way around"

Output: `AGENTS.md` files in `src/api/`, `src/domain/`, `src/jobs/`, and `tests/`, each with a responsibility statement and file index; `scripts/` skipped because it holds one self-explanatory file.
