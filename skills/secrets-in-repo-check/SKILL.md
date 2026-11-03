---
name: secrets-in-repo-check
description: "Scan a diff or repo for hardcoded secrets, keys, or tokens committed to source, and check that .gitignore actually covers the files that should never be tracked. Use when reviewing a diff before merge, or when asked whether a repo has leaked credentials."
---

# secrets-in-repo-check

## Instructions

Use the repo's configured secret scanner if it has one (e.g. gitleaks, trufflehog, a pre-commit hook); otherwise grep the diff for secret shapes (API keys, private key headers, embedded passwords in connection strings). If a secret is already committed, flag that it must be rotated at the source, not just removed from the tree. Check `.gitignore` covers the actual local config naming convention in use.

## Inputs

- `target`: diff or path to scan.

## Outputs

A finding per detected secret or gitignore gap, with a rotation note if already committed.

## Constraints

- Deleting a committed secret in a new commit does not remove it from history — rotation is required.
- Don't rewrite git history or force-push to remove a secret; recommend it and leave it to the repo owner.
- Never print a secret's full value in findings or chat: report its location, type, and a masked form showing at most the first and last four characters.

## Examples

### Example 1

Input: a `settings.local.json` with a database password committed 3 commits ago.

Output: Flagged — the password is still retrievable from git history; rotate the DB credential, don't just delete the file now.
