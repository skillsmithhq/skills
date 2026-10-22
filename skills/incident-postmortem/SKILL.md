---
name: incident-postmortem
description: "Write a structured incident postmortem for a customer-impacting production incident, distinct from a code-level RCA — covers detection, communication, and follow-up actions, not just root cause. Use when asked to \"write a postmortem\", \"document this incident\", or after a production incident affecting one or more tenants is resolved."
---

# incident-postmortem

## Instructions

1. Confirm the incident is actually resolved and its facts (impact, timeline, cause) are established before writing.
2. Write each required section (see Outputs), linking to an `rca-doc` for the technical root cause rather than duplicating it.
3. Explicitly address client communication given contractual/SLA obligations may apply.
4. Save to the repo's existing incidents/RCA folder if it has one; otherwise `docs/rca/<short-slug>-postmortem.md`.

## Inputs

- `incident`: an incident description or ticket reference.

## Outputs

A document with:

1. **Incident summary** — what happened, which customers or tenants, how long.
2. **Impact** — data/users affected, and whether data was lost/corrupted vs. delayed/incorrect display.
3. **Detection** — how it was found, time-to-detect, and whether detection was slower than it should have been.
4. **Timeline** — dated/timestamped sequence.
5. **Root cause** — link to the RCA doc if one exists.
6. **Remediation performed** — actual data/state fixes for affected customers.
7. **Follow-up actions** — owned, ticketed items.
8. **Client communication** — whether/how affected customers were or should be notified.

## Constraints

- Every follow-up action needs an owner or it doesn't count as tracked.
- Don't duplicate the technical RCA — link to it.
- Never include secrets, credentials, tokens, or personal data in the document, even if they appear in the code, logs, or tickets used as sources.

## Examples

### Example 1

Input: "write a postmortem for last night's signature-verification outage"

Output: A postmortem linking to the existing RCA, detailing that the cause was a database restore from another environment with a different signing key, remediation was re-signing the affected rows, and a follow-up ticket to add a pre-restore validation check.
