---
name: model-fallback-degradation-check
description: "Check that an AI-dependent feature defines a degraded mode for when the model API is unavailable, slow, or returns a low-confidence/malformed result — distinct from a general infrastructure SPOF check, since a \"successful\" call can still return unusable output."
---

# model-fallback-degradation-check

## Instructions

Check the feature distinguishes a hard API failure, a schema-invalid response, and a well-formed-but-low-confidence response, each with its own defined behavior (retry, cached fallback, honest failure message) rather than collapsing all three into a crash or a silently wrong result.

## Inputs

- `target`: the AI-dependent feature to check.

## Outputs

A finding per failure mode without a defined behavior.

## Constraints

- An HTTP 200 from the model API does not mean the output is usable.

## Examples

### Example 1

Input: a product-tagging feature that saves whatever the model returns, with no check that the tags exist in the catalogue.

Output: Flagged — validate the response against the allowed tags, and on failure or timeout fall back to "untagged" with a retry queue rather than saving invalid data.
