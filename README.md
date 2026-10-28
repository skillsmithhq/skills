# Skillsmith · Agent Skills

120 skills for AI coding agents: 103 stack-agnostic engineering skills covering security, data, delivery, reliability, cloud cost, testing, and documentation, each adapting to the conventions of the repository in which it is used, and 17 [Business Intelligence skills](#business-intelligence-skills).

**Browse the engineering skills → [INDEX.md](INDEX.md)**

## Install

With the open [`skills` CLI](https://github.com/vercel-labs/skills) (Node 22.20+):

```bash
# one skill
npx skills add skillsmithhq/skills --skill aws-cost-estimate -g -a claude-code

# all skills
npx skills add skillsmithhq/skills --skill '*' -g -a claude-code
```

`-g` installs for all your projects; `-a` selects the agent (`claude-code`, `cursor`, `codex`, and others).

Without Node, on macOS, Linux, or WSL:

```bash
mkdir -p ~/.claude/skills/aws-cost-estimate && curl -fsSL https://install.skillsmith.workers.dev/s/aws-cost-estimate -o ~/.claude/skills/aws-cost-estimate/SKILL.md
```

On Windows (PowerShell):

```powershell
$d = "$HOME/.claude/skills/aws-cost-estimate"; New-Item -ItemType Directory -Force $d | Out-Null; Invoke-WebRequest -UseBasicParsing "https://install.skillsmith.workers.dev/s/aws-cost-estimate" -OutFile "$d/SKILL.md"
```

Business Intelligence skills include scripts and references, so without Node they install as a folder bundle:

```bash
mkdir -p ~/.claude/skills && curl -fsSL https://install.skillsmith.workers.dev/p/revenue-intelligence | tar -xz -C ~/.claude/skills
```

## Business Intelligence skills

17 skills for evidence-based business intelligence work on SaaS companies: from market research and data readiness to cross-module analysis, prioritised decisions, client reports, and an independent quality audit. Calculations are done by small helper scripts, not by the model; every finding cites its evidence.

**Market research and customer acquisition**

| Skill | What it does |
|---|---|
| [`market-opportunity-research`](skills/market-opportunity-research/SKILL.md) | Researches an industry or business model to find evidence-backed business intelligence opportunities, competitors, pricing and positioning, and produces a sourced opportunity report with validation experiments |
| [`saas-prospect-qualification`](skills/saas-prospect-qualification/SKILL.md) | Scores whether a named company is a good prospect for a Business Intelligence Opportunity Assessment, using a weighted ICP scorecard backed by public evidence, and suggests an outreach angle |
| [`client-discovery-synthesis`](skills/client-discovery-synthesis/SKILL.md) | Turns client interviews, meeting notes and discovery call transcripts into structured BI requirements, including objectives, a decision inventory, systems, data requirements, stakeholders, constraints and open questions, keeping what the client said separate from our interpretation |
| [`consulting-proposal-builder`](skills/consulting-proposal-builder/SKILL.md) | Drafts a commercial proposal for a BI assessment or advisory engagement, covering context, scope, deliverables, timeline, client responsibilities, data request, exclusions, pricing assumptions, acceptance criteria and risks, without inventing prices, guarantees or testimonials |

**Business data foundations**

| Skill | What it does |
|---|---|
| [`business-data-inventory`](skills/business-data-inventory/SKILL.md) | Builds an inventory of a client's business systems, datasets, tables and fields (billing, subscriptions, customers, users, product events, CRM, support, operations, infrastructure) from CSV, XLSX, JSON, SQL schema files and documentation, including ownership, access needs, likely relationships and gaps |
| [`data-readiness-assessment`](skills/data-readiness-assessment/SKILL.md) | Assesses whether business datasets can support reliable BI by checking completeness, validity, uniqueness, consistency, referential integrity, coverage and freshness with a published, reproducible scoring method, then states which proposed analyses are ready, usable with caveats or blocked |
| [`business-metric-dictionary`](skills/business-metric-dictionary/SKILL.md) | Creates and maintains a client-specific dictionary of business metrics (MRR, ARR, growth, gross margin, NRR, GRR, churn, CAC, LTV, ARPA, activation, adoption, concentration, support burden) with formulas, source fields, grain, inclusion and exclusion rules, currency and timezone handling, owners and approval status |
| [`cross-module-data-mapping`](skills/cross-module-data-mapping/SKILL.md) | Discovers and validates relationships between datasets from different business systems (billing with product usage, CRM with billing, support with retention, infrastructure cost with active customers), measuring match rates, cardinality, fan-out and identifier normalisation, and resolving duplicate entities before any cross-module analysis |

**Analysis**

| Skill | What it does |
|---|---|
| [`revenue-intelligence`](skills/revenue-intelligence/SKILL.md) | Calculates and interprets revenue metrics (MRR, ARR, new, expansion, contraction and churned revenue, NRR, GRR, growth, ARPA, concentration, recurring share, collections and outstanding invoices) with a deterministic script, documenting formulas, source fields, periods, exclusions and assumptions |
| [`customer-intelligence`](skills/customer-intelligence/SKILL.md) | Segments customers and analyses retention, churn, revenue concentration, support burden, engagement and expansion potential by segment and account, combining revenue, product and support outputs through validated joins, and flags accounts with co-occurring risk signals |
| [`product-intelligence`](skills/product-intelligence/SKILL.md) | Measures product usage (activation, active users, feature adoption, usage frequency, zero-usage paying accounts, account-level adoption) from event data, linking it to subscription value through validated joins, and proposes experiments without claiming that features cause retention or revenue |
| [`operational-technology-intelligence`](skills/operational-technology-intelligence/SKILL.md) | Analyses operational and technology economics (infrastructure and cloud cost, cost per customer and per transaction, support workload, reliability and downtime, resource utilisation, technical-debt implications) against revenue and activity, and frames cost-optimisation ideas as hypotheses with stated baselines and assumptions |
| [`anomaly-hypothesis-validation`](skills/anomaly-hypothesis-validation/SKILL.md) | Detects unusual movements in business metrics against an explicit baseline with a robust, documented method, checks data quality first, generates competing explanations and tests each against evidence (decomposition, cross-module checks), then rates confidence and states what evidence is still missing |

**Decision intelligence and delivery**

| Skill | What it does |
|---|---|
| [`bidim-opportunity-scoring`](skills/bidim-opportunity-scoring/SKILL.md) | Scores and ranks BI and decision opportunities with the BIDIM matrix (impact, strategic fit, evidence confidence, effort, risk, data readiness, time to value) using a transparent formula, evidence guards, missing-value ranges and sensitivity checks, producing an opportunity register with rationale and next actions |
| [`executive-decision-intelligence`](skills/executive-decision-intelligence/SKILL.md) | Translates verified analysis and BIDIM priorities into decision briefs for a CEO or founder, CTO, CBO or commercial lead, or investor, each stating the decision, evidence, impact, confidence, alternatives, risks, dependencies, next action and measurement, with no guarantees, investment advice or unsupported predictions |
| [`intelligence-report-builder`](skills/intelligence-report-builder/SKILL.md) | Assembles professional intelligence deliverables (BI Opportunity Assessment, Executive, Revenue, Customer, Product and Technology Intelligence Reports, AI and Analytics Roadmap) with the 13 standard sections, a BIDIM table and an evidence appendix, refusing to build when any cited evidence ID does not trace to an upstream output |
| [`intelligence-quality-audit`](skills/intelligence-quality-audit/SKILL.md) | Independently reviews intelligence reports and analytical outputs by recomputing figures from upstream artefacts, re-reading key metrics from the text rather than trusting the claims file, and checking traceability, joins, causal language, statistical limits, BIDIM consistency, privacy, contradictions and missing caveats, returning pass, needs-revision or fail with required corrections |

These skills come with `scripts/` and `references/` folders, so install the whole folder: `npx skills add` does this, or use the bundle command below.

## Update

Run the same install command again to get the latest version of a skill. With the CLI you can also run `npx skills update`.

## Use

Start a new Claude Code session (terminal, VS Code, or JetBrains) and ask as you normally would, e.g. "check this migration for safety". The matching skill loads automatically. To use a specific skill, name it: "use `migration-safety-check` on this file".

## Security

Engineering skills are plain-text instructions with no scripts, binaries, or network calls of their own. Business Intelligence skills also include small Python helper scripts (standard library only, no network calls, no subprocesses) that calculate metrics deterministically; read them before running them on your data. All skills are reviewed against these rules:

- No hidden or invisible characters, HTML comments, or encoded content.
- No instructions to send code or data to outside services, and no pipe-to-shell commands.
- No destructive commands; skills that review scripts or migrations are review-only.
- Actions that change systems (cloud resources, dependencies, databases) require the user's explicit approval.
- Secrets are never printed in full, and generated documents never include secrets or personal data.
- Content fetched from tickets or documents is treated as information, never as instructions.

This is a self-review, not an independent audit.

## Disclaimer

Skills run inside your own AI agent; Skillsmith never receives or stores your code. AI output can be wrong: review every result before acting on it. Skillsmith is not responsible for outputs or their consequences. Provided under the MIT License, without warranty. Not affiliated with Anthropic or any AI provider.
