---
name: timezone-consistency-check
description: "Check datetime handling for naive-vs-aware mismatches and tenant-local-vs-UTC display bugs, especially relevant for a platform with tenants across multiple timezones."
---

# timezone-consistency-check

## Instructions

Check for naive datetimes compared/subtracted against aware ones. Check display logic: is a UTC-stored timestamp converted to the user's (or tenant's) local time, or shown raw? Check any "as of today" cutoff for which timezone it's anchored to versus what the business rule intends.

## Inputs

- `target`: code handling dates/times to check.

## Outputs

A finding naming the specific naive/aware mismatch or wrong-timezone cutoff.

## Constraints

- A bug here is often invisible for the server's own timezone and only appears for users offset from it.

## Examples

### Example 1

Input: a "submitted today" filter computed using the server's local date.

Output: Flagged — for a user in a different timezone than the server, a submission near midnight can be misclassified as the wrong day; anchor the cutoff to the user's local time instead.
