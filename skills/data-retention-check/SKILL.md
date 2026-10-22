---
name: data-retention-check
description: "Check that personal and sensitive data has a defined retention period and that deletion actually reaches every copy (backups excepted by policy, caches, search indexes, logs, analytics, third parties). Use when adding a new data field, store, or a delete-account feature."
---

# data-retention-check

## Instructions

List where the data is written: primary tables, replicas, caches, search indexes, logs, analytics events, file storage, and third-party services. For each, confirm a retention period and a deletion path. For delete-account flows, trace the deletion through every store and note which copies remain and why.

## Inputs

- `target`: the data field, feature, or deletion flow to check.

## Outputs

A table of stores with retention and deletion status, flagging any copy with no deletion path.

## Constraints

- Deleting the database row while the data lives on in logs and search is not deletion.
- Don't give legal advice; flag where a retention decision is needed and who should make it.

## Examples

### Example 1

Input: "we're adding phone numbers to user profiles"

Output: Flagged: phone numbers will also land in the analytics events and the support-tool sync; neither has a deletion path when a user closes their account.
