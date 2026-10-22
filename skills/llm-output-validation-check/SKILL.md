---
name: llm-output-validation-check
description: "Check that code consuming an LLM's output validates it before acting — executing a generated query, writing to a database, or calling another API — rather than trusting it like a deterministic internal source."
---

# llm-output-validation-check

## Instructions

Check any generated SQL/query for parameterization rather than direct execution. Check any generated file path stays inside an intended directory. Check any numeric/enum field from model output against a range/allowlist before use in a business decision. Distinguish hallucination risk (needs review) from injection risk (needs validation regardless).

## Inputs

- `target`: the code consuming LLM output to check.

## Outputs

A finding per unvalidated use of model output, naming the specific risk (traversal, injection, or unchecked business value).

## Constraints

- A schema-constrained "structured" response is not automatically safe to execute without validation.

## Examples

### Example 1

Input: code that takes a model-generated SQL string and executes it directly against the database.

Output: Flagged — execute only a parameterized, allowlisted query shape derived from the model's structured intent, not the raw generated SQL string.
