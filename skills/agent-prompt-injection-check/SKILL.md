---
name: agent-prompt-injection-check
description: "Check that code feeding external/untrusted content into an LLM prompt treats it strictly as data, never as instructions, and that no destructive tool call executes based solely on model output influenced by that content."
---

# agent-prompt-injection-check

## Instructions

Confirm untrusted content is clearly delimited and framed as data in the prompt. Check what tools/actions are reachable from a response generated while processing untrusted content, and whether any are destructive without a separate confirmation step.

## Inputs

- `target`: the agent pipeline or prompt-construction code to check.

## Outputs

A finding on missing delimiting/framing, and on any destructive action reachable without confirmation.

## Constraints

- The real damage happens at the action boundary (a tool call), not the injected text itself — focus there.

## Examples

### Example 1

Input: an agent that summarizes a fetched webpage and can also send emails via a tool call, with no confirmation step.

Output: Flagged — a webpage with hidden text telling the agent to email the page contents to an outside address could trigger an unconfirmed email send; require explicit confirmation before any email tool call.
