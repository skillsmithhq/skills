---
name: jira-sprint-hygiene-check
description: "Audit a sprint/board for hygiene issues — tickets with no acceptance criteria, no estimate, or stale in \"In Progress\" — as a board-level check distinct from reviewing one ticket at a time. Use before sprint planning, mid-sprint review, or closing a sprint."
---

# jira-sprint-hygiene-check

## Instructions

Pull the sprint's tickets via whatever Jira access is available (Atlassian MCP tools, the REST API, or a JQL query such as `sprint = <id>`); if there is none, ask the user for an export instead of guessing. Find out where this team keeps acceptance criteria and estimates (a custom field, the description, story points or time) before judging them missing. Check each ticket against: missing acceptance criteria on an unstarted story, missing estimate on a committed item, staleness in "In Progress" (ask the team's threshold if unstated), and unassigned tickets in the sprint. Report grouped by rule, not per-ticket narrative. Never edit tickets to fix issues found.

## Inputs

- `board_or_sprint`: the board/sprint to audit.

## Outputs

A report grouped by hygiene rule, listing violating ticket keys under each.

## Constraints

- This is a report for a human to triage, not an auto-fix.

## Examples

### Example 1

Input: "check sprint health before we close it"

Output: "No acceptance criteria: PROJ-501, PROJ-512. No estimate: PROJ-498. Stale in-progress (>5 days no update): PROJ-490."
