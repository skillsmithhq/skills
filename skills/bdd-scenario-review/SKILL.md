---
name: bdd-scenario-review
description: "Review existing BDD feature files and their step definitions for common problems: imperative UI-script steps, several behaviours in one scenario, incidental detail, order-dependent scenarios, duplicate or near-duplicate steps, logic in steps, missing negative and boundary cases, and tag drift. Use when reviewing a pull request that changes .feature files, or when a BDD suite has become slow, flaky or hard to read."
---

# bdd-scenario-review

## Instructions

1. Detect the BDD framework, where features and steps live, and the team's conventions (tag scheme, language, step phrasing).
2. Read the feature files in scope and check each scenario for:
   - Imperative steps that script the UI ("I click", "I fill in the field with id ...") instead of describing behaviour.
   - More than one behaviour in a scenario (several `When` steps, or `Then` followed by more actions).
   - Incidental detail that does not affect the outcome (names, exact amounts, dates) and makes scenarios brittle.
   - Steps joined with "and" inside one sentence, which hide two actions.
   - `Then` steps that check implementation details (database rows, internal calls) rather than observable outcomes.
   - Missing negative paths and boundary values for the rules the feature states.
   - A long `Background`, or one that not every scenario needs.
   - Titles that don't describe the behaviour, and scenarios that duplicate others.
   - Scenarios that depend on running order or on data left by another scenario.
3. Check the step definitions behind them for: near-duplicate steps with different wording, ambiguous matches, business logic or many assertions in steps, fixed sleeps, global state, and unused steps (from the framework's usage report or dry run).
4. Check tag hygiene: tags that no pipeline uses, `@wip` or `@skip` left on old scenarios, and smoke-test tags on slow scenarios.
5. If the suite is slow or flaky, find the slowest and most frequently failing scenarios from the CI history or the framework's report, and say whether the cause is UI-level setup, shared data, or waiting.

## Inputs

- `target`: feature files, a tag, or a pull request diff.

## Outputs

Findings grouped by file, each with the scenario or step, the problem, and a rewritten version. End with a short summary: number of scenarios reviewed, findings by type, and the three changes with the most value.

## Constraints

- Suggest rewrites that keep the scenario's meaning. Flag, rather than change, anything that looks like a business-rule question.
- A scenario that is hard to write declaratively often points to an unclear requirement; say so.

## Examples

### Example 1

Input: a scenario with 14 steps that logs in, navigates three pages, and fills a form by field id

Output: imperative and covers two behaviours (login and address change). Split it into "Customer updates delivery address" with a `Given` that creates a signed-in customer through the API. The form steps become "When she changes her delivery address to a valid address" and "Then her next order ships to the new address". The step "I wait 5 seconds" should use the framework's wait-for-element helper.
