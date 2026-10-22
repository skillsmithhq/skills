---
name: mocking-boundary-check
description: "Check that mocks are placed at the actual system boundary (external API, paid service), not on internal collaborators — over-mocking internal logic lets a test pass even when the real integration between two internal parts is broken."
---

# mocking-boundary-check

## Instructions

Check whether each mock stands in for something genuinely external, or for something internal the test is avoiding testing against for real. For the internal case, check whether a real integration test exists elsewhere; if not, that's the actual gap.

## Inputs

- `target`: the test's mocking setup to check.

## Outputs

A finding per internal-collaborator mock, noting whether a real integration test covers that path elsewhere.

## Constraints

- Mocking an external paid/third-party service is usually correct and not the target of this check.

## Examples

### Example 1

Input: a test mocking the internal database layer to unit-test a service method.

Output: Flagged as acceptable only if a separate integration test exercises the real database path — if none exists, that's the gap, not the mock itself.
