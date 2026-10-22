---
name: agent-tool-permission-scope-check
description: "Check that a new AI-agent/tool integration requests the minimum permission scope it needs, and that destructive/irreversible tool calls require confirmation rather than executing autonomously."
---

# agent-tool-permission-scope-check

## Instructions

Check the requested scope against the tool's stated purpose — flag read-only tools requesting write/admin scope. Check that destructive actions require an explicit, specific confirmation, not a generic "proceed?". Check that error responses don't leak more than a successful call would.

## Inputs

- `target`: the tool/integration definition to check.

## Outputs

A finding on excess scope, missing confirmation, or leaky error responses.

## Constraints

- The permission grant is the real safety boundary — a prompt instruction to "only read" is not a substitute.

## Examples

### Example 1

Input: a Slack-posting tool granted full workspace-admin scope when it only ever posts messages.

Output: Flagged — narrow the scope to `chat:write` only; admin scope is unnecessary and expands blast radius if the agent is manipulated.
