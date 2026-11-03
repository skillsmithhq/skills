---
name: bdd-step-definitions
description: "Write or fix the step definitions behind BDD feature files: reuse existing steps, match parameters with the framework's expressions or parameter types, keep steps thin by delegating to page objects, API clients or domain helpers, share state through the framework's context mechanism, and run the scenarios to prove they pass. Use when feature files have undefined, ambiguous or failing steps, or when wiring up new Gherkin scenarios."
---

# bdd-step-definitions

## Instructions

1. Detect the framework, language and test structure: where step definitions live, how they share state (for example the World object in Cucumber.js, context injection in Reqnroll, `context` in Behave, fixtures in pytest-bdd), existing helpers (page objects, API clients, test-data builders), and hooks for setup and teardown.
2. Run the framework's dry run or undefined-step report to list undefined, ambiguous and unused steps. Fix ambiguity (two definitions matching one step) before adding anything.
3. For each undefined step, first look for an existing step that means the same thing. If one exists, suggest rewording the feature step to match it rather than adding a near-duplicate.
4. Write new steps:
   - Match with the framework's expression style (for example Cucumber Expressions such as `{int}` and `{string}`, or regex where the repo uses regex). Add custom parameter types for domain values used in several places.
   - Keep each step thin: it translates the sentence into a call on a helper (page object, API client, domain service). It contains no business logic and no long assertion chains.
   - Pass state between steps through the framework's context mechanism, not through globals.
   - Prefer the fastest reliable layer that proves the behaviour, for example an API or service call for `Given` setup rather than clicking through the UI.
   - Use the framework's waiting or retry helpers for asynchronous UI; never fixed sleeps.
5. Make each scenario clean up after itself (hooks or transactions), so scenarios pass in any order and in parallel if the suite runs in parallel.
6. Run the affected scenarios and then the whole suite, and report the real results.

## Inputs

- `features`: feature file(s) or tags to make runnable.

## Outputs

The step definition and helper changes, the commands run, and the pass/fail result per scenario, including any scenarios still failing and why.

## Constraints

- Do not change what a scenario means to make it pass. If the behaviour is wrong, report it as a bug in the code.
- Do not mark failing scenarios as pending or skipped to get a green run without saying so.
- Never point step definitions at production systems or real third-party accounts; use test environments, stubs or sandboxes.

## Examples

### Example 1

Input: three undefined steps in `shipping.feature`

Output: "a cart totalling {float}" was added, and builds the cart through the cart API helper. "the shipping charge is {float}" reads the checkout summary from the page object. "the customer goes to checkout" already existed. `npx cucumber-js features/shipping.feature`: 3 scenarios passed. Full suite: 148 passed, 0 failed.
