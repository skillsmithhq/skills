---
name: alert-actionability-check
description: "Check that a new or changed alert fires on user-visible symptoms, has a clear owner and runbook, and won't page for noise. Use when reviewing alert rules, monitors, or on-call configuration."
---

# alert-actionability-check

## Instructions

For each alert, state what user-facing problem it represents. Prefer symptom alerts (error rate, latency, failed jobs) over cause alerts (CPU, memory) unless the cause reliably precedes an outage. Check the threshold and duration against recent data to estimate how often it would have fired. Confirm it names an owner, links a runbook, and that its severity matches whether someone must act right now.

## Inputs

- `target`: the alert rule or monitoring config.

## Outputs

Per alert: keep, tune (with suggested threshold/duration), downgrade to a ticket, or delete, with the reason.

## Constraints

- An alert nobody acts on trains people to ignore the one that matters.
- Every paging alert needs a runbook link, even a short one.

## Examples

### Example 1

Input: a new alert paging when CPU exceeds 80% for 1 minute

Output: Downgrade: CPU spikes during the nightly batch every day without user impact; page on p95 latency or error rate instead and keep CPU as a dashboard signal.
