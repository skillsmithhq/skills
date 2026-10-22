---
name: adr-doc
description: "Write an Architecture Decision Record capturing a significant technical decision: context, options considered, the decision, and its consequences. Use when asked to write an ADR, record a decision, or after a design discussion concludes."
---

# adr-doc

## Instructions

1. Find the repo's existing ADR folder and numbering scheme (`docs/adr/`, `doc/architecture/decisions/`, or similar); follow its template if one exists.
2. State the context and forces neutrally, including constraints like team skills, cost, and deadlines.
3. List the real options considered, each with honest pros and cons.
4. State the decision and why it beat the alternatives.
5. List consequences, including the downsides being accepted and what would trigger revisiting it.
6. Save with the next number; otherwise `docs/adr/NNNN-<short-slug>.md`, status Proposed or Accepted.

## Inputs

- `decision`: the decision or discussion to record.

## Outputs

An ADR with Title, Status, Context, Options considered, Decision, and Consequences.

## Constraints

- Record the options actually considered, not a straw man next to the winner.
- Never edit an accepted ADR's decision; supersede it with a new one.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write an ADR for moving background jobs from cron to a queue"

Output: `docs/adr/0007-background-jobs-on-queue.md`: context (missed cron runs, no retries), options (keep cron, managed queue, self-hosted broker), decision (managed queue), and consequences (new infra cost, at-least-once delivery means handlers must be idempotent).
