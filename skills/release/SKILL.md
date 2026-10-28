---
name: release
description: "Create a release branch: ask which branch to cut it from, what to name it, and which commits to bring in, then cherry-pick them and resolve any merge conflicts. Use when asked to create a release branch, cut a release, or cherry-pick commits onto a new branch."
---

# release

## Instructions

### 1. Check the repo is safe to work in

- Run `git status`. If there are uncommitted changes, stop and ask whether to stash them (`git stash push -u -m "release-skill"`), commit them, or abort. Never discard them.
- If a cherry-pick, merge or rebase is already in progress, stop and tell the user.
- Run `git fetch --all --prune` so remote branches and commits are current.

### 2. Ask for the three inputs

Use `AskUserQuestion` (one call, up to three questions) unless the user already gave the answer in their request:

1. **Base branch** — where to create the release branch from. Offer `main` / `master` / `develop` and the most recently updated `release/*` branches found with `git branch -a --sort=-committerdate`. Prefer the remote copy (`origin/<branch>`) so the branch starts from the latest state.
2. **Branch name** — suggest names following the repo's existing convention (look at `git branch -a` and `git tag --sort=-creatordate | head`), e.g. `release/v1.4.0` where the version is the next one after the latest tag. Check the name doesn't already exist locally or on the remote; if it does, ask again.
3. **Commits** — which commits to include. List candidates first with
   `git log --oneline --no-merges <base>..<source>` (source is usually `main` or the branch the user names), and let the user pick: all of them, specific SHAs, a range (`A..B`), or commits matching a ticket ID / message pattern (`git log --grep`). Show the final list (SHA + subject, oldest first) and confirm before applying.

### 3. Create the branch and apply the commits

```
git switch -c <branch-name> <base>
git cherry-pick -x <sha1> <sha2> ...        # oldest first
```

- Use `-x` so each commit records where it came from.
- For a merge commit the user explicitly wants, use `-m 1`.
- Skip commits already on the base (`git cherry <base> <source>` marks them with `-`) and say which were skipped.

### 4. Resolve conflicts

When a cherry-pick stops with conflicts:

1. `git status` and `git diff --name-only --diff-filter=U` to list conflicted files.
2. For each file, read the conflict hunks and understand both sides: `git show <sha>` (what the commit intended) and `git log --oneline <base> -- <file>` (what changed on the base). Resolve by keeping the base's current code and applying the commit's intended change on top of it — not by blindly picking "ours" or "theirs".
3. Lockfiles / generated files: regenerate them with the project's tool (`npm install`, etc.) instead of hand-merging.
4. Check no conflict markers remain: `git diff --check` and `grep -rn '^<<<<<<<\|^>>>>>>>' <files>`.
5. Run the project's build/typecheck/tests if they exist and are quick. Fix anything the resolution broke.
6. `git add <files>` then `git cherry-pick --continue --no-edit`.
7. If a commit becomes empty (already applied), `git cherry-pick --skip` and report it.

If the intent is genuinely ambiguous (both sides changed the same logic in incompatible ways, or the commit depends on an earlier commit that wasn't selected), stop and ask the user — show the hunk, both versions, and your recommended resolution. Offer to add the missing dependency commit.

### 5. Finish

- Show `git log --oneline <base>..HEAD` and a summary: commits applied, commits skipped, conflicts resolved (file + how).
- Ask before pushing. Only on a yes: `git push -u origin <branch-name>`.
- If you stashed changes in step 1, tell the user where they are; don't pop them onto the release branch.

## Inputs

- `base`: branch to create from (asked if not given).
- `branch`: new branch name (asked if not given).
- `commits`: SHAs, range, or pattern selecting the commits (asked if not given).

## Outputs

A new local branch with the selected commits applied, all conflicts resolved, and a summary of what was applied, skipped and resolved. Pushed only if the user confirms.

## Constraints

- Never force-push, `reset --hard`, or delete branches.
- Never push without asking.
- Don't modify the base branch.
- Don't add attribution trailers to commits; cherry-picks keep the original author and message.
- If something goes badly wrong mid-way, `git cherry-pick --abort` returns to the state before the current pick; tell the user what was and wasn't applied.

## Examples

### Example 1

Input: `/release`
Output: Asks base (`origin/main`), name (`release/v1.3.0`), and shows 6 commits since the last release tag to pick from; user picks 4. Creates the branch, cherry-picks them; one conflict in `src/types.ts` is resolved by keeping the base's new field and adding the commit's new type. Build passes. Asks whether to push.

### Example 2

Input: `/release from release/v1.2 as release/v1.2.1 with commits abc123 def456`
Output: Skips the questions, cherry-picks the two hotfix commits onto `release/v1.2.1`, reports the result, and asks before pushing.
