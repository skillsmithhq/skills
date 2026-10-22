---
name: aws-budget-guardrails
description: "Set up cost guardrails for an AWS account or workload: AWS Budgets with alert thresholds, Cost Anomaly Detection, cost-allocation tags, and a review routine, as infrastructure-as-code where the repo has it. Use when asked to set a budget for AWS, get alerted before a bill surprise, control spend for a project or team, or after an unexpected AWS charge."
---

# aws-budget-guardrails

## Instructions

1. Find out the scope (whole account, organisation, or one workload), the monthly amount, and who should get alerts. If the user doesn't know the amount, base it on the last 3 months in Cost Explorer (`aws ce get-cost-and-usage`) or on an estimate from `aws-cost-estimate`.
2. Check the repo's IaC tool and add the guardrails there (Terraform `aws_budgets_budget`, CloudFormation `AWS::Budgets::Budget`, CDK `CfnBudget`); fall back to CLI commands or console steps only if there's no IaC.
3. Create a monthly cost budget with alerts at 50%, 80%, and 100% of actual spend, plus a 100% forecasted-spend alert, sent to email and/or an SNS topic.
4. For a workload, scope the budget with a cost-allocation tag (e.g. `project` or `team`), make sure resources carry the tag, and note that the tag must be activated in the Billing console before it filters costs.
5. Enable Cost Anomaly Detection with a monitor for the account or the tagged workload and a daily or immediate alert subscription.
6. Optional, only when the user asks for hard limits: describe Budget Actions (apply an IAM policy or SCP, or stop EC2/RDS instances) and their risks before configuring any.
7. Suggest a short monthly review: top 5 services by cost, month-over-month change, and untagged spend.

## Inputs

- `scope`: account, organisation, or workload/tag to guard.
- `amount` (optional): monthly budget in USD.
- `recipients`: email addresses or SNS topic for alerts.

## Outputs

IaC (or CLI commands) creating the budget, alert thresholds, anomaly monitor, and subscription; a list of resources missing the cost tag; and the manual steps (tag activation, email confirmation) the user must do.

## Constraints

- AWS Budgets alert on spend; they don't stop it. Say this clearly, and never set up a Budget Action that stops or restricts resources without explicit approval.
- Billing data lags by several hours, so alerts can arrive after the spend; recommend thresholds that leave room.
- Don't hard-code account ids or email addresses in shared code; use variables.
- Write the IaC or CLI commands for the user to review; never run commands that create, change, or delete cloud resources without the user's explicit approval.
- Cost Explorer API calls are billed per request (about $0.01 each); prefer a few targeted queries.

## Examples

### Example 1

Input: "set a $300/month budget for our staging environment and alert the team"

Output: A Terraform budget filtered on `tag:env=staging` with 50/80/100% actual and 100% forecasted alerts to an SNS topic, an anomaly monitor for the same tag, a list of 4 staging resources missing the `env` tag, and a reminder to activate `env` as a cost-allocation tag and confirm the SNS email subscription.
