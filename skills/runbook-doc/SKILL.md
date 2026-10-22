---
name: runbook-doc
description: "Write an operational runbook for an alert, service, or routine task: how to recognise the problem, check it, mitigate it, and escalate. Use when asked to write a runbook, playbook, or on-call guide, or when an alert has no runbook link."
---

# runbook-doc

## Instructions

1. Read the alert definition, service config, and dashboards to ground every step in real names.
2. Write for an on-call engineer who has never seen this service, at 3 a.m.
3. Order steps from safest (look) to riskiest (restart, fail over, roll back), with the exact command or console path for each.
4. Mark which steps need approval and who to escalate to.
5. Save to the repo's existing runbooks/ops docs folder if it has one; otherwise `docs/runbooks/<short-slug>.md`.

## Inputs

- `subject`: the alert, service, or task the runbook covers.

## Outputs

A runbook with: Summary, Impact, Dashboards & logs, Diagnosis steps, Mitigation steps, Escalation, and Follow-up.

## Constraints

- Every command must be copy-pasteable and use real resource names from the repo or config.
- Never include secrets; point to where they are stored.

## Examples

### Example 1

Input: "write a runbook for the queue-backlog alert"

Output: `docs/runbooks/queue-backlog.md` covering how to check consumer health and lag, how to scale consumers, when to pause producers, and who to escalate to if the backlog keeps growing.
