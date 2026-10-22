---
name: aws-cost-estimate
description: "Estimate the monthly AWS bill for an architecture, feature, or infrastructure-as-code change, itemised by service with every usage assumption written down, using current prices from AWS's own sources. Use when asked what an AWS setup will cost, to compare architecture options by cost, or to budget a new workload."
---

# aws-cost-estimate

## Instructions

1. Inventory the resources: read the IaC (Terraform, CloudFormation, CDK, SAM, Pulumi, Serverless) or architecture description and list every billable resource with its region, size/class, and count.
2. For each resource, write down the usage drivers and the assumed values: hours running, requests, GB stored, GB transferred out, read/write units, Lambda invocations × duration × memory, and so on. Ask for traffic numbers if none are given; otherwise state the assumption.
3. Get current unit prices from AWS's own sources: the AWS Pricing Calculator, the service pricing pages, or the Price List API (`aws pricing get-products --region us-east-1 --service-code <code> --filters ...`). Record the region and the date prices were checked.
4. Compute monthly cost per line item. Include the commonly missed items: NAT Gateway hourly and per-GB processing, data transfer out and cross-AZ traffic, public IPv4 addresses, CloudWatch logs ingestion and retention, EBS snapshots, load balancer capacity units, and backup storage.
5. Note free-tier effects separately, since they expire and don't apply to every account.
6. Give a low / expected / high total based on the usage assumptions, and list the 3 biggest cost drivers with concrete ways to cut them (right-sizing, Graviton, Savings Plans or Reserved capacity, S3 storage classes and lifecycle rules, VPC endpoints instead of NAT for AWS service traffic, shorter log retention).

## Inputs

- `target`: IaC files, an architecture description, or a diagram.
- `usage` (optional): expected traffic, data volume, and growth.
- `region` (optional): defaults to the region in the IaC, otherwise ask.

## Outputs

An itemised table (service, resource, usage assumption, unit price, monthly cost), the low/expected/high monthly total, the region and price date, top cost drivers with savings options, and a list of assumptions to confirm.

## Constraints

- Never present prices from memory as current; prices change and vary by region. If live pricing can't be fetched, label figures as approximate and tell the user to confirm them in the AWS Pricing Calculator.
- Every cost line must name the usage assumption behind it.
- Exclude tax, support plans, and Marketplace fees unless asked, and say they're excluded.

## Examples

### Example 1

Input: "what will this Terraform cost per month in ap-south-1?" for 2 t4g.medium EC2 instances, an ALB, a db.t4g.medium RDS Multi-AZ, a NAT Gateway, and 200 GB of S3

Output: An itemised table where RDS Multi-AZ and the NAT Gateway are the two biggest lines, a low/expected/high total for 50/200/500 GB of monthly outbound traffic, and savings options: a VPC endpoint for S3 traffic currently going through NAT, and a 1-year Savings Plan once usage is stable.
