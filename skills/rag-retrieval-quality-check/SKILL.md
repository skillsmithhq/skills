---
name: rag-retrieval-quality-check
description: "Check that a RAG pipeline can measure whether retrieved chunks are actually relevant, and that chunking doesn't split content in a way that breaks its meaning."
---

# rag-retrieval-quality-check

## Instructions

Check for a relevance-scoring/eval step on retrieval specifically, separate from evaluating the final answer. Check the chunking strategy for mid-sentence/mid-table splits from a fixed size; prefer natural boundaries (paragraph, section) when they conflict with a fixed chunk size.

## Inputs

- `target`: the RAG pipeline to check.

## Outputs

A finding on missing retrieval-quality measurement or a chunking strategy that breaks semantic units.

## Constraints

- A retrieval failure is silent — the model still generates a fluent, wrongly-grounded answer with no error.

## Examples

### Example 1

Input: a document chunker splitting on a fixed 500-character window with no boundary awareness.

Output: Flagged — a policy table gets split mid-row across two chunks; recommend chunking on section boundaries instead.
