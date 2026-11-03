---
name: bdd-feature-writing
description: "Turn a requirement, user story or ticket into BDD feature files in Gherkin: declarative Given/When/Then scenarios, one behaviour each, with Scenario Outlines for data variations, a short Background, and tags, following the repo's existing BDD framework and conventions. Use when asked to write BDD scenarios, feature files, Gherkin, or acceptance tests from a story."
---

# bdd-feature-writing

## Instructions

1. Detect the BDD setup first: the framework (for example Cucumber for JavaScript/Java/Ruby, Reqnroll for .NET, where older repos may still use SpecFlow, end-of-life since 31 December 2024; Behave or pytest-bdd for Python, Behat for PHP, Godog for Go), where `.feature` files live, the spoken language used in them, existing tags, and the step phrasing already in use. Reuse existing step wording wherever it fits, so new scenarios run with existing step definitions.
2. Read the requirement in full, including acceptance criteria and any comments that changed it. List the behaviours (business rules), and the questions the requirement leaves open. Ask about open questions rather than inventing answers.
3. Write one `Feature` per capability, with a short description of who benefits and why. Use `Rule` (Gherkin 6+) to group scenarios by business rule if the framework supports it.
4. For each rule, write scenarios that cover the main path, the important alternative and negative paths, and boundaries:
   - Declarative, in business language: "When she submits the order", not "When I click the button with id submit".
   - One behaviour per scenario: one `When` (or one `When`/`Then` pair), and `Then` steps that check outcomes the user or system can observe.
   - `Given` sets up only the state that matters to this scenario; incidental details stay out.
   - Use `Scenario Outline` with `Examples` for the same behaviour with different data, including boundary values.
   - Keep `Background` to a few steps shared by every scenario in the file.
   - Scenario titles describe the behaviour and its result.
5. Tag scenarios the way the repo does (for example by ticket, priority, `@smoke`, or `@wip`).
6. Run the framework's dry-run or undefined-step check if it has one, and list which steps already exist and which need step definitions.

## Inputs

- `requirement`: story, ticket text, or acceptance criteria.
- `feature_path` (optional): where the feature file should go.

## Outputs

The `.feature` file(s), a short list of open questions, and the steps that still need definitions (with suggested signatures).

## Constraints

- Feature files are specifications, not test scripts. No UI selectors, URLs, SQL or waits in steps.
- Don't invent business rules the requirement doesn't state; ask.
- Keep each scenario independent; it must not rely on another scenario having run.

## Examples

### Example 1

Input: "Customers get free shipping on orders of 50 or more; otherwise shipping is 5."

Output:
```gherkin
Feature: Shipping charges
  Customers know the shipping cost before they pay.

  Rule: Orders of 50 or more ship free

    Scenario Outline: Shipping charge depends on the order total
      Given a cart totalling <total>
      When the customer goes to checkout
      Then the shipping charge is <shipping>

      Examples:
        | total | shipping |
        | 49.99 | 5.00     |
        | 50.00 | 0.00     |
        | 120   | 0.00     |
```
Open question: does the total include discounts and tax? Two new steps are needed; "the customer goes to checkout" already exists.
