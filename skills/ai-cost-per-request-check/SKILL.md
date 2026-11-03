---
name: ai-cost-per-request-check
description: "Check that an AI-powered feature's per-request cost has been estimated against expected production traffic, since a feature cheap to prototype can become expensive to run at scale. Use when reviewing a feature that calls an LLM or other paid model API."
---

# ai-cost-per-request-check

## Instructions

Identify the provider and model the feature actually calls (from config or code). Estimate tokens per call (input + output, including retries) × expected calls at real traffic, priced from the provider's current published pricing (look it up and note the date; don't rely on memory). Check specifically for an agentic loop with multiple calls per action, an uncapped retry path, or a per-row batch job.

## Inputs

- `target`: the AI-powered feature to check.

## Outputs

A cost estimate against expected traffic, with the pricing source and date and the assumptions used, or a flag that no estimate exists.

## Constraints

- The most common finding is that no estimate was done at all, not that an existing estimate is wrong.

## Examples

### Example 1

Input: a bulk CSV import that calls a categorisation model once per uploaded product row.

Output: Flagged — no cost estimate exists; at expected volume (~50k rows/month) estimate the monthly cost at current model pricing, confirm it's within budget, and consider batching rows per call before shipping.
