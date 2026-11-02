---
name: saas-builder
description: "One entry point that takes a SaaS product from idea to a deployed, tested and maintained product, using a team of specialist sub-agents: research, spec, UI/UX, architecture, development, testing, CI/CD, budget, launch and marketing, maintenance, a scoped penetration test of the product's own build, and an independent reviewer. The main session orchestrates, runs agents in parallel where their work does not overlap, and stops at an approval gate after each stage. Defaults to free hosting and asks before anything that costs money or publishes. Use when asked to build a SaaS end to end, go from idea to launch, or plan and ship a new product."
---

# saas-builder

A single workflow that runs a new SaaS product through every stage, from research to maintenance. You (the main session) are the **orchestrator**: you talk to the user, own the gates and the status file, brief specialist sub-agents, merge their work, and are the only one who pushes or publishes. Specialists do the stage work in their own context and hand back files plus a short report.

## Ground rules (every stage, every agent)

- **Gates.** After each stage, summarise what was produced, the key decisions and the open risks, then ask with `AskUserQuestion`: continue, revise, or stop. If the user asked for an unattended run, record each gate in `STATUS.md` and continue, but always stop for anything under "Money and publishing", when the stage 1 verdict is pivot or stop, and for the stage 3 prototype click-through.
- **State.** Keep `docs/product/STATUS.md` with one line per stage: status (not started / in progress / approved / skipped), date, document path, and which agents ran. Read it first on every invocation so work resumes where it stopped.
- **Money and publishing.** Default to free tiers. Never sign up for a service, enter payment details, buy a domain, enable a paid plan, contact people, push, turn on scheduled pipelines, or make anything public without an explicit yes for that specific action. Sub-agents never do any of these; only the orchestrator does, after asking. Local commits are fine.
- **Evidence.** Every market, competitor, pricing or demand claim cites a source URL and the date it was checked. A source counts only if the page was actually opened and says what is claimed; a search-result snippet is not a source. If a number cannot be sourced, leave it out, write "unknown", or label it as an assumption with the reasoning. Never invent market sizes, user counts, quotes or survey results.
- **Honest marketing.** No fake or placeholder reviews, testimonials, customer logos, "as seen in" badges or user counts; no scarcity or countdown timers; no "secure", "compliant", "certified" or "free forever" claims; and no claim the product cannot back up with a passing test or a written fact.
- **Legal.** Agents do not write terms of service or privacy policies. They list what a qualified professional must provide (based on the data model, markets and payment setup) and leave clearly marked placeholders. Anything about personal data, payments, tax or regulated sectors carries a note that it needs professional review. The trademark check is an obvious-conflict search only, not legal clearance. Do not copy competitors' names, logos, copy or UI.
- **Fit the repo.** For an existing repo, detect its language, framework, package manager, test runner and CI host first, and work in those terms.
- **Report truthfully.** Test results, pipeline status and checks are reported as they actually ran. Anything skipped is listed as skipped.

## How the team works

**Launching a specialist.** Use the `Agent` tool (general-purpose type unless the user has a better-matched agent installed). Each brief contains:

1. The role and stage, copied from the stage section below.
2. Input file paths to read (the brief, earlier approved documents). Pass paths, not pasted content.
3. The exact output path(s) it may write, and that it must not edit anything else.
4. These ground rules, copied word for word: Money and publishing, Evidence, Honest marketing, Legal, Fit the repo, Report truthfully. Then add: "You cannot ask the user questions; put open questions in your report. Do not launch further agents. Do not push, publish, sign up for anything or spend money."
5. What to return: at most 200 words covering what was written, decisions made, open questions, and anything not done.

**Parallel waves.** Launch the agents of one wave in a single message so they run at the same time, and keep a wave to five agents or fewer (split larger waves into batches). Only put agents in the same wave if they write to different files. Wait for the whole wave, then merge: resolve contradictions yourself, ask the user if a contradiction is a product decision, and note the result in `STATUS.md`.

**Isolation.** Development agents that change code in parallel run with `isolation: "worktree"`. A worktree starts from the last commit, so commit the scaffold locally before the developer wave. Each developer commits on its own worktree branch and reports the branch name. Merge the branches one at a time and run the tests after each merge.

**Fresh-eyes review.** Before the push gate, an independent reviewer checks the work against these rules. Launch it as a fresh agent (for example general-purpose), never as a fork, because a fork inherits your context and your conclusions.

**Cost.** Each agent uses tokens from the user's plan. At stage 0, tell the user the expected count: 14 agents plus one per story group, plus up to eight more for test-and-fix and pen-test-and-fix rounds. Offer "lean" mode if they want fewer.

| Stage | Agents (wave) | Writes |
|---|---|---|
| 0 Intake | orchestrator only | `00-brief.md`, `STATUS.md` |
| 1 Research | problem-evidence, competitors, channels-and-risks (one wave) | `research/*.md` → orchestrator merges into `01-research.md` |
| 2 Spec | product-spec (one) | `02-spec.md` |
| 3 UX + architecture | ux-designer, architect (one wave) | `03-ux.md`, `prototype/`, `04-architecture.md` |
| 4 Build | scaffolder (one), then developers per independent story group (one wave, worktrees) | source code and tests |
| 5 Quality + ops docs | tester, cicd-engineer, budget-analyst, launch-marketer, maintainer (one wave) | `05-testing.md`, CI config, `06-cicd.md`, `07-budget.md`, `08-launch.md`, `09-maintenance.md` |
| 6 Pen test | pen-tester (one), then developers for fixes | `10-pentest.md` |
| 7 Review | reviewer (one, fresh context) | `11-review.md` |
| 8 Push | orchestrator only | remote, pipeline, live site |

All documents live in `docs/product/`. Document numbers follow topics, not stages: stage 3 writes `03` and `04`, and stage 4 writes code only.

## Stage 0: Intake (orchestrator)

Ask in one `AskUserQuestion` call (skip anything already answered):

1. The idea in one sentence, and who has the problem.
2. Constraints: budget per month (default: free only), hours per week, deadline, and anything they will not do (for example cold outreach, being on camera, regulated domains).
3. Stack: existing repo or new, and any preferred language or framework.
4. Where the code will live (GitLab, GitHub or local only), and private or public.

Write `00-brief.md` and `STATUS.md`. State the expected number of agents.

Sub-agents cannot answer permission prompts, so any command they need that is not already allowed fails. This includes installs, builds, test runs, the local server and contrast checks. Tell the user which commands the run will need (based on the stack) so they can allow them up front. Otherwise, the orchestrator runs those commands itself after the agents report.

## Stage 1: Research (three agents in parallel)

- **problem-evidence** → `research/problem.md`: who has the problem, how often, what they use today, and what it costs them. It uses real evidence (forum threads, reviews of existing tools, job posts, search results) and links every source. No quote is longer than one sentence.
- **competitors** → `research/competitors.md`: at least five alternatives, including spreadsheets and doing nothing. For each, the pricing from its own pricing page (dated), its target user, and a gap.
- **channels-and-risks** → `research/channels-risks.md`: where buyers in this market look for tools, which of those channels fit the user's constraints, legal or regulatory exposure, platform dependency, how crowded the market is, and an obvious-conflict search for the product name (not legal clearance).

The orchestrator merges these into `01-research.md` and adds demand signals (what evidence exists that people would pay, and what is still missing) and kill criteria (what result from a cheap test, such as a landing page or waitlist, would show the idea is not worth building). It ends with a verdict: **go**, **pivot** (say to what) or **stop**, with reasons. If the evidence says stop, say so plainly.

**Optional demand test.** On a go or pivot verdict, offer a cheap test before the spec. The orchestrator builds a one-page landing page with an honest description, the planned price or "pricing not set", and a waitlist form. The form uses a provider the user approves, or a plain mailto link. Publishing the page, and any spend on traffic, needs a yes. The page must say the product is not built yet. Record the results against the kill criteria in `01-research.md` before stage 2.

## Stage 2: Spec (product-spec agent) → `02-spec.md`

- A product summary in one paragraph and the single core job the product does.
- MVP scope as Must / Should / Won't. Must is limited to what one person can build in the stated hours within about four weeks.
- User stories with Given / When / Then acceptance criteria for every Must item. Each story is tagged with a **story group** so that groups can be built independently.
- Data model: entities, fields, which fields are personal data, and retention.
- Non-functional requirements: security, privacy, accessibility (WCAG 2.2 AA), performance, and supported browsers or devices.
- Pricing and plans: free and paid tiers, what each includes, the trial (if any), and what happens on cancellation or non-payment. Prices stay `[PRICE: see 07-budget]` until stage 5.
- Analytics events: the few events needed to measure the success metrics. Collect no personal data in events unless the spec says why.
- Success metrics for the first 90 days, each with how it is measured.
- Effort as a range per story, with assumptions.

## Stage 3: UX and architecture (two agents in parallel)

- **ux-designer** → `03-ux.md` + `prototype/` (static HTML, no build step). It covers user flows per Must story; a screen list with each screen's empty, loading and error states; plain-language copy; error messages that say what to do next; design tokens with AA contrast (and dark mode if planned); and keyboard, focus, label and landmark notes.
- **architect** → `04-architecture.md`: the simplest architecture that meets the spec within budget. For free-only, prefer a static front end on free Pages hosting, with data in the browser or a free-tier backend. It states each free tier's limits and what happens when they are exceeded. The decision and rejected options are recorded as an ADR, together with folder layout, module boundaries per story group, and the test strategy.

The orchestrator checks that the screens and the architecture agree: every screen maps to a module, and every field shown on a screen exists in the data model. Then it asks the user to click through the prototype before approving.

## Stage 4: Build

1. **scaffolder** (one agent): sets up the repo in the chosen stack. It adds a README, the licence (the one the user chose), `.gitignore`, `.env.example` (no real secrets), linting and formatting, a test runner, and an empty app that builds and passes one test.
The orchestrator commits the scaffold locally once it builds and passes its test.

2. **developers** (one per story group, in batches of five or fewer, each with `isolation: "worktree"`): each builds its group's stories in small commits with tests. Inputs are validated at the boundary, authorisation is checked on every resource access, and secrets stay out of the repo and the client bundle. Each reports which acceptance criteria it checked and how.

   Cross-cutting pieces belong to their own story group, as the spec says:
   - Billing, if the product charges. Use the payment provider's test mode and test keys only. Live keys and live mode need the user's yes and are set up by the orchestrator. Build plan limits, upgrade and downgrade, failed-payment handling, and webhooks verified by signature.
   - Accounts and data rights, if there are user accounts. Users can export their data and delete their account, and deletion reaches every store the data model lists.
   - Observability. Add the analytics events from the spec, and error tracking on a free tier the user approves, with personal data stripped from error reports.
   - A kill switch. One flag that turns off any paid or external feature without a deploy.
3. The orchestrator merges the branches one by one, runs the full test suite after each merge, and sends failures back to the developer who owns them.

If any two story groups touch the same files, use one developer agent that works through them in order, rather than a parallel wave.

## Stage 5: Quality and operations (five agents in parallel)

File ownership in this wave: the tester owns the test files, `package.json` (or the stack's equivalent manifest) and the lockfile. The cicd-engineer owns all CI and dependency-bot config (for example Dependabot or Renovate), and asks for any scripts it needs through its report. The budget-analyst, launch-marketer and maintainer write their documents only.

- **tester** → tests in the repo + `05-testing.md`. It writes unit, integration and end-to-end smoke tests for the main flow (using the browser test tool already in the repo, or Playwright if there is none). It also runs an accessibility check (automated plus a keyboard-only pass), checks phone, tablet and desktop widths, and checks the empty, loading and error states. For performance, it measures page weight and Core Web Vitals (for example with Lighthouse, on the local build) against a budget it states in the report. It checks the latest Chrome, Firefox and Safari where it can, and says which it could not run. If billing exists, it covers billing flows with provider test cards and replayed test webhooks. For security, it runs the ecosystem's dependency audit and a secrets scan, and checks input validation, authorisation and security headers. It reports real commands and pass/fail counts. Bugs are listed, not fixed. The orchestrator sends them to a developer agent.
- **cicd-engineer** → CI config (`.gitlab-ci.yml` or `.github/workflows/`) + `06-cicd.md`. The pipeline installs, lints, tests and builds on every push and merge request, and deploys from the default branch only. It caches on the lockfile, keeps secrets as masked, protected variables scoped to the deploy job, and documents a rollback path. A scheduled job checks that the live URL responds, as free uptime monitoring.
- **budget-analyst** → `07-budget.md`. Every cost line (hosting, domain, email, backend, AI or API usage, payment fees, tools) comes from official pricing pages, with provider, plan, price, unit, URL and date checked. It gives the monthly cost now, at 10× usage and at 100× usage, with the assumptions. It lists the free-tier limits and the first thing that forces a paid plan. It checks whether the payment provider supports the user's country, plus its fees and payouts, from the provider's docs. It works out break-even, with price, conversion and churn labelled as assumptions, and says "revenue is not profit". It lists the budget alerts to set.
- **launch-marketer** → `08-launch.md`. It writes `[PRICE: see 07-budget]` wherever a price is needed, and lists every product claim it makes so the reviewer can check each one. It writes the positioning, plus landing-page and pricing-page copy that follows the honest-marketing rule. Channels must fit the user's constraints, each with weekly effort, cost and how success is measured. It includes a launch checklist (legal pages from a professional, privacy-respecting analytics, support contact, uptime check, backups) and a first-30-days plan tied to the stage 2 metrics.
- **maintainer** → `09-maintenance.md`. It writes a runbook (deploy, roll back, rotate secrets, restore data, incident response). It sets out monitoring and alerts with owners, and a routine: weekly automated dependency updates with a monthly review, security advisories, a quarterly restore test, and a monthly cost review. It describes the support and feedback loop into the backlog, and a quarterly keep, change or stop review. It recommends any automation config to the cicd-engineer instead of writing it.

The orchestrator loops tester → developer → tester until the Must stories pass. It stops after three rounds and reports whatever still fails. It then fills the price placeholders in `08-launch.md` from `07-budget.md`, and removes any claim that no longer matches a passing test.

## Stage 6: Penetration test (pen-tester agent) → `10-pentest.md`

A scoped, non-destructive security test of the product's own build, run after the stage 5 test loop passes. If `security-boundary-review`, `injection-check`, `authz-idor-check`, `csrf-cors-check`, `session-token-check`, `ssrf-check`, `rate-limit-check`, `pii-response-leak-check` or `dependency-vulnerability-check` are installed, the pen-tester uses them for the matching checks.

**Scope and safety (put this in the brief word for word):**

- Targets: only the app built in this run, served locally (for example `localhost`). The deployed URL is in scope only if the orchestrator has asked the user and they said yes, and only on a host the user controls.
- Never test third-party services the app depends on (payment providers, auth providers, model APIs, the hosting platform). Use mocks or test modes for them.
- No denial of service, load or stress testing, mass scanning, or brute force. Rate-limit checks use a small burst (tens of requests), against the local build only.
- Non-destructive: use test accounts and test data, prove each issue with the smallest possible request, and do not read, change or delete real data. Do not chain issues further than needed to show impact.
- Use the tools already in the repo, or free tools the user approves installing (for example OWASP ZAP baseline). No paid scanners.
- No persistence, backdoors, or code left behind. Any test files are removed or listed in the report.

**What it tests,** mapped to the OWASP Top 10 and the stack in use:

- Access control: IDOR, missing authorisation, privilege escalation, and forced browsing to hidden routes.
- Injection: XSS (stored, reflected, DOM), SQL or NoSQL, command and template injection, and prompt injection where the app calls an AI model.
- Authentication and sessions: login, logout, reset, token storage, cookie flags, expiry, and session fixation.
- Browser security: CSP and the other security headers, CORS, CSRF, clickjacking, and open redirects.
- Data exposure: secrets or keys in the client bundle and source maps, PII in responses and errors, verbose errors, and directory listings.
- Server-side: SSRF, file upload handling, and unsafe deserialisation where they apply.
- Dependencies: known vulnerabilities, separating reachable from unreachable.
- Configuration: debug modes, default credentials, exposed admin or health endpoints, and HTTPS settings on the deployed host (if in scope).

**Report:** for each finding, give the title, severity (critical, high, medium, low, informational) with the reason, affected file or route, steps to reproduce, evidence, and the suggested fix. It also lists what was tested and found clean, what was out of scope or not tested and why, and the tools and versions used. The report ends with this statement: "This is an automated, scoped test of one build. It is not a substitute for an independent professional penetration test, and the product must not be marketed as pen-tested or secure on the strength of it."

The orchestrator sends critical and high findings to developer agents. Then it runs the pen-tester again on just those findings, up to two rounds. Anything still open, and every medium finding, is recorded in `10-pentest.md` as fixed, accepted (with the user's yes) or deferred.

## Stage 7: Independent review (reviewer agent, fresh context) → `11-review.md`

Give it only the paths, not your conclusions. It checks:

- the code against the spec's acceptance criteria;
- every product claim in `08-launch.md` maps to a passing Must story in `05-testing.md`, and no copy calls the product secure or pen-tested;
- every critical or high finding in `10-pentest.md` is fixed or explicitly accepted by the user;
- every number in `01-research.md` and `07-budget.md` has a URL and date, or is labelled as an assumption;
- every document against the ground rules: misleading copy, placeholder social proof, and legal text that agents should not have written;
- secrets in the repo;
- CI deploy rules.

It writes only `11-review.md` and lists the findings by severity. The orchestrator fixes them (or has an agent fix them) and records what was fixed and what was accepted, with reasons.

## Stage 8: Push (orchestrator only)

1. Show the remote, branch and visibility, and ask. Never make a repo or site public without a yes.
2. Commit, push, and watch the pipeline until it passes or fails. Fix failures caused by this work and report anything else.
3. Final report: links to the repo, pipeline and live site; every stage's status from `STATUS.md`; the agents used; open risks; and the next three actions.

## After launch: feature mode

For a new feature or a significant change to a launched product, run a reduced cycle:

1. Spec addendum: append to `02-spec.md`.
2. UX and architecture deltas: only if screens or modules change.
3. Build, in a worktree.
4. Tester.
5. Pen-tester: only if the change touches auth, data access, payments, file handling, or external calls.
6. Reviewer.
7. Push.

Each step has the same gates and ground rules as a full run. Record each feature as a new row in `STATUS.md`. Update `07-budget.md` and `09-maintenance.md` if the change affects costs or operations.

## Inputs

- The product idea and constraints (asked in stage 0 if not given).
- Optional: a stage to start or resume from (for example "resume at stage 4"), "unattended" to run gates as checkpoints, "lean" to use one agent per stage instead of parallel waves (in stage 5, one agent does the five roles in order), or "feature: <description>" to run feature mode on an existing product.
