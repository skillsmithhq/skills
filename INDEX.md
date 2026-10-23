# Skills index

101 skills in 12 categories. Each links to its `SKILL.md`. **For** lists who the skill is most useful to (Developer, Tester, Reviewer, Tech Lead, Manager) and which part of the stack it applies to (Backend, Frontend, DevOps, or Any stack).

## Security (14)

| Skill | What it does | For |
|---|---|---|
| [`authz-idor-check`](skills/authz-idor-check/SKILL.md) | Check that every endpoint that loads a resource by id confirms the caller is allowed to access that specific resource, not just that they are logged in. | Developer, Tester, Reviewer, Tech Lead · Backend |
| [`injection-check`](skills/injection-check/SKILL.md) | Check for SQL, shell, template, and query-language injection where user input reaches an interpreter. | Developer, Reviewer, Tech Lead · Backend |
| [`ssrf-check`](skills/ssrf-check/SKILL.md) | Check server-side code that fetches a URL supplied or influenced by a user (webhooks, previews, imports, image fetchers) for server-side request forgery. | Developer, Reviewer, Tech Lead · Backend |
| [`rate-limit-check`](skills/rate-limit-check/SKILL.md) | Check that expensive, abusable, or authentication-related endpoints have rate limits and that the limit key can't be trivially bypassed. | Developer, Reviewer, Tech Lead · Backend |
| [`session-token-check`](skills/session-token-check/SKILL.md) | Check how sessions and tokens (cookies, JWTs, API keys, refresh tokens) are issued, stored, validated, and revoked. | Developer, Reviewer, Tech Lead · Backend, Frontend |
| [`webhook-receiver-check`](skills/webhook-receiver-check/SKILL.md) | Check an incoming-webhook endpoint for signature verification, replay protection, idempotency, and fast acknowledgement. | Developer, Reviewer, Tech Lead · Backend |
| [`input-validation-check`](skills/input-validation-check/SKILL.md) | Check that request data is validated at the system boundary for type, length, range, format, and allowed values before business logic runs. | Developer, Tester, Reviewer · Backend, Frontend |
| [`csrf-cors-check`](skills/csrf-cors-check/SKILL.md) | Check CORS and CSRF configuration for overly permissive settings — wildcard origins, disabled CSRF, or credentials allowed alongside a wildcard origin. | Developer, Reviewer, Tech Lead · Backend, Frontend |
| [`security-boundary-review`](skills/security-boundary-review/SKILL.md) | Locate the repo's actual inter-service auth mechanism and confirm a changed endpoint uses it, then check the gaps that pass a casual read: permission classes that check auth but not resource/tenant ownership, serializer field exposure from a recently added column, and rate limiting only where a convention already exists. | Developer, Reviewer, Tech Lead · Backend |
| [`secrets-in-repo-check`](skills/secrets-in-repo-check/SKILL.md) | Scan a diff or repo for hardcoded secrets, keys, or tokens committed to source, and check that .gitignore actually covers the files that should never be tracked. | Developer, Reviewer, Tech Lead · Backend, Frontend, DevOps |
| [`secret-rotation-check`](skills/secret-rotation-check/SKILL.md) | After a secret is rotated, check it was actually replaced everywhere it's used — not just the primary secret store — since a partial rotation leaves a working old credential. | Developer, Reviewer, Tech Lead · Backend, DevOps |
| [`pii-response-leak-check`](skills/pii-response-leak-check/SKILL.md) | Check that error responses returned to API clients don't leak PII, internal stack traces, or DB error text — distinct from logging PII checks, since this is about what the client receives. | Developer, Reviewer, Tech Lead · Backend |
| [`dependency-vulnerability-check`](skills/dependency-vulnerability-check/SKILL.md) | Check a dependency manifest/lockfile change for known-vulnerable versions using the ecosystem's actual audit tool, distinguishing reachable vulnerabilities from unreachable ones. | Developer, Reviewer, Tech Lead · Backend, Frontend, DevOps |
| [`cert-trust-incident-check`](skills/cert-trust-incident-check/SKILL.md) | Check any machine (macOS, Linux, BSD, Windows) for exposure to a compromised certificate authority: test which TLS clients still trust it, inventory OS, browsers, runtimes and trust bundles, and list issues with actions. Ships with data for the October 2026 eMudhra intermediate compromise. | Developer, Tester, Tech Lead · DevOps |

## AI & agents (17)

| Skill | What it does | For |
|---|---|---|
| [`agent-context-window-budget-check`](skills/agent-context-window-budget-check/SKILL.md) | Check that an agent's prompt construction doesn't blindly dump full documents/history into context without a size budget, risking silent truncation of exactly the part that mattered. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-eval-regression-check`](skills/agent-eval-regression-check/SKILL.md) | Check that a prompt or agent behavior change runs against a standing eval set before shipping, since a fix for one case can silently regress a different case that was working before. | Developer, Tester, Reviewer · Backend |
| [`agent-loop-termination-check`](skills/agent-loop-termination-check/SKILL.md) | Check that an autonomous agent's plan→act→observe loop has a hard termination condition — max iterations, a cost/time budget, or an explicit success/failure signal — rather than relying on the model to decide on its own when it's done. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-memory-persistence-check`](skills/agent-memory-persistence-check/SKILL.md) | Check that an agent's persisted memory/state is scoped per user/tenant and doesn't grow unbounded, and that corrected facts don't sit alongside stale ones with no way to tell which is current. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-observability-check`](skills/agent-observability-check/SKILL.md) | Check that an agentic pipeline logs each decision point — tool calls, reasoning/plan, results — in enough detail to reconstruct after the fact why the agent took a given action. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-orchestration-topology-check`](skills/agent-orchestration-topology-check/SKILL.md) | Check that a multi-agent system's control-flow shape (fixed pipeline, hierarchical supervisor, peer negotiation) actually matches how structured or open-ended the underlying task is. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-planning-execution-separation-check`](skills/agent-planning-execution-separation-check/SKILL.md) | Check whether a complex agentic task separates planning (decide the steps) from execution (carry them out), making the plan inspectable before real-world actions start. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-prompt-injection-check`](skills/agent-prompt-injection-check/SKILL.md) | Check that code feeding external/untrusted content into an LLM prompt treats it strictly as data, never as instructions, and that no destructive tool call executes based solely on model output influenced by that content. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-state-recovery-check`](skills/agent-state-recovery-check/SKILL.md) | Check that a long-running agentic workflow can resume after a crash without losing all progress or re-executing already-completed side-effecting steps. | Developer, Reviewer, Tech Lead · Backend |
| [`agent-tool-permission-scope-check`](skills/agent-tool-permission-scope-check/SKILL.md) | Check that a new AI-agent/tool integration requests the minimum permission scope it needs, and that destructive/irreversible tool calls require confirmation rather than executing autonomously. | Developer, Reviewer, Tech Lead · Backend |
| [`ai-cost-per-request-check`](skills/ai-cost-per-request-check/SKILL.md) | Check that an AI-powered feature's per-request cost has been estimated against expected production traffic, since a feature cheap to prototype can become expensive to run at scale. | Developer, Tech Lead, Manager · Backend |
| [`llm-output-validation-check`](skills/llm-output-validation-check/SKILL.md) | Check that code consuming an LLM's output validates it before acting — executing a generated query, writing to a database, or calling another API — rather than trusting it like a deterministic internal source. | Developer, Tester, Reviewer · Backend |
| [`model-fallback-degradation-check`](skills/model-fallback-degradation-check/SKILL.md) | Check that an AI-dependent feature defines a degraded mode for when the model API is unavailable, slow, or returns a low-confidence/malformed result — distinct from a general infrastructure SPOF check, since a "successful" call can still return unusable output. | Developer, Reviewer, Tech Lead · Backend |
| [`multi-agent-handoff-check`](skills/multi-agent-handoff-check/SKILL.md) | Check that when one agent delegates to another, the handoff carries enough context to act correctly, and that task ownership doesn't become ambiguous. | Developer, Reviewer, Tech Lead · Backend |
| [`non-determinism-boundary-check`](skills/non-determinism-boundary-check/SKILL.md) | Check where a system draws the line between deterministic business logic and non-deterministic model output — money, permissions, and irreversible actions should be enforced in deterministic code, with model output as input to that logic, never the final authority. | Developer, Reviewer, Tech Lead · Backend |
| [`prompt-versioning-check`](skills/prompt-versioning-check/SKILL.md) | Check that production prompts are tracked as versioned, reviewable artifacts in one place, not duplicated as inline strings across the codebase with no single source of truth. | Developer, Reviewer, Tech Lead · Backend |
| [`rag-retrieval-quality-check`](skills/rag-retrieval-quality-check/SKILL.md) | Check that a RAG pipeline can measure whether retrieved chunks are actually relevant, and that chunking doesn't split content in a way that breaks its meaning. | Developer, Tester, Tech Lead · Backend |

## APIs & integration (7)

| Skill | What it does | For |
|---|---|---|
| [`api-contract-compat-check`](skills/api-contract-compat-check/SKILL.md) | Check whether a change to an API response shape or inter-service payload is additive (safe) or breaking (needs versioning/coordination) for every consumer of that contract. | Developer, Tester, Reviewer, Tech Lead · Backend, Frontend |
| [`pagination-consistency-check`](skills/pagination-consistency-check/SKILL.md) | Check that a new list endpoint has pagination, and that offset-based pagination combined with concurrent writes can't produce skipped or duplicated rows across pages. | Developer, Tester, Reviewer · Backend, Frontend |
| [`idempotency-check`](skills/idempotency-check/SKILL.md) | Check whether an operation reachable via webhook, retry-prone API call, or an at-least-once task queue is safe to execute twice. | Developer, Reviewer · Backend |
| [`retry-backoff-check`](skills/retry-backoff-check/SKILL.md) | Check that a new call to an external service has retry/backoff on transient failure and doesn't silently swallow errors. | Developer, Reviewer · Backend |
| [`sse-endpoint-review`](skills/sse-endpoint-review/SKILL.md) | Check an SSE/streaming endpoint for an unbounded buffer, missing heartbeats, and leaked generators on disconnect, and state the connection-capacity implication in concrete worker-count terms. | Developer, Reviewer · Backend, Frontend |
| [`timeout-budget-check`](skills/timeout-budget-check/SKILL.md) | Check that every outbound call (HTTP, database, cache, queue, third-party SDK) has an explicit timeout, and that nested timeouts fit inside the caller's own deadline. | Developer, Reviewer · Backend |
| [`payload-size-check`](skills/payload-size-check/SKILL.md) | Check API responses, list endpoints, exports, and messages for unbounded size: missing pagination, over-fetching, large embedded blobs, and no request-body limits. | Developer, Reviewer · Backend, Frontend |

## Data & databases (12)

| Skill | What it does | For |
|---|---|---|
| [`migration-safety-check`](skills/migration-safety-check/SKILL.md) | Check whether code still running mid-rollout keeps working against a new migration, whether it locks a large table, and, for multi-schema or multi-tenant databases, whether it runs correctly in every schema, not just one. | Developer, Reviewer, Tech Lead · Backend, DevOps |
| [`data-backfill-safety-check`](skills/data-backfill-safety-check/SKILL.md) | Check a one-off data backfill or correction script for batching, idempotency, dry-run support, and rollback before it runs against production. | Developer, Reviewer, Tech Lead · Backend, DevOps |
| [`index-coverage-check`](skills/index-coverage-check/SKILL.md) | Check that new or changed queries are backed by suitable database indexes and that new indexes are worth their write cost. | Developer, Reviewer · Backend |
| [`query-audit`](skills/query-audit/SKILL.md) | Find related-object access inside a loop or serializer method, check it against actual select_related/prefetch_related coverage, and measure the real query count before/after. | Developer, Reviewer · Backend |
| [`transaction-boundary-check`](skills/transaction-boundary-check/SKILL.md) | Check that multi-step writes that must succeed or fail together run in one transaction, and that side effects (emails, events, API calls) fire only after commit. | Developer, Reviewer · Backend |
| [`check-then-act-race-check`](skills/check-then-act-race-check/SKILL.md) | Find read-then-write logic that checks a condition (a limit, a balance, a uniqueness rule) and writes without a DB-level lock or constraint, making it vulnerable to a race under concurrent requests. | Developer, Tester, Reviewer · Backend |
| [`soft-delete-consistency-check`](skills/soft-delete-consistency-check/SKILL.md) | Check that a soft-deleted record is excluded everywhere it needs to be — default manager, raw querysets, aggregations, serializers, and any cache built before the deletion. | Developer, Reviewer · Backend |
| [`cache-key-scoping-check`](skills/cache-key-scoping-check/SKILL.md) | Check that a cache key includes every dimension the cached value actually varies by (tenant, user, locale, permission level) — a key missing one dimension serves one caller's data to another. | Developer, Reviewer · Backend |
| [`timezone-consistency-check`](skills/timezone-consistency-check/SKILL.md) | Check datetime handling for naive-vs-aware mismatches and tenant-local-vs-UTC display bugs, especially relevant for a platform with tenants across multiple timezones. | Developer, Tester, Reviewer · Backend, Frontend |
| [`currency-round-trip-check`](skills/currency-round-trip-check/SKILL.md) | Check money-conversion code for round-trip rounding error: recomputing an amount by dividing an already-rounded intermediate value back through a conversion rate amplifies the rounding error instead of reproducing the original. | Developer, Tester, Reviewer · Backend, Frontend |
| [`audit-trail-purge-check`](skills/audit-trail-purge-check/SKILL.md) | Before deleting/purging records across multiple services, check whether each service's audit/log records are FK-cascaded (deleted with the parent) or decoupled (survive and need separate handling). | Developer, Reviewer, Tech Lead · Backend |
| [`data-retention-check`](skills/data-retention-check/SKILL.md) | Check that personal and sensitive data has a defined retention period and that deletion actually reaches every copy (backups excepted by policy, caches, search indexes, logs, analytics, third parties). | Developer, Tech Lead, Manager · Backend |

## Architecture (8)

| Skill | What it does | For |
|---|---|---|
| [`bounded-context-check`](skills/bounded-context-check/SKILL.md) | Check whether a shared-sounding concept (Customer, Request, Account) actually means the same thing across the services that use it, or has quietly diverged with no explicit translation between them. | Developer, Reviewer, Tech Lead · Backend |
| [`coupling-direction-check`](skills/coupling-direction-check/SKILL.md) | Check that a new dependency respects the codebase's intended layering direction — e.g. | Developer, Reviewer, Tech Lead · Backend, Frontend |
| [`circular-dependency-check`](skills/circular-dependency-check/SKILL.md) | Check for a circular import/module dependency introduced by a change, including a longer cycle (A→B→C→A), not just a direct two-module cycle. | Developer, Reviewer, Tech Lead · Backend, Frontend |
| [`strangler-fig-migration-check`](skills/strangler-fig-migration-check/SKILL.md) | Check that a legacy-to-new migration routes traffic incrementally rather than a big-bang cutover with no rollback path. | Developer, Reviewer, Tech Lead · Backend |
| [`single-point-of-failure-check`](skills/single-point-of-failure-check/SKILL.md) | Check a new architecture/design for a component with no redundancy that everything depends on, and confirm whether that's a deliberate, accepted tradeoff or an oversight. | Developer, Reviewer, Tech Lead · Backend, DevOps |
| [`dead-code-check`](skills/dead-code-check/SKILL.md) | Find code that is never executed or referenced (unused functions, exports, files, feature flags, config keys, and endpoints) and confirm it's safe to remove. | Developer, Reviewer · Backend, Frontend |
| [`tech-debt-register`](skills/tech-debt-register/SKILL.md) | Find, describe, and prioritise technical debt in a codebase area as a register of concrete items with cost, risk, and a suggested fix. | Developer, Tech Lead, Manager · Any stack |
| [`dependency-upgrade-plan`](skills/dependency-upgrade-plan/SKILL.md) | Plan a major dependency or framework upgrade: what breaks, in what order to change things, and how to ship it safely. | Developer, Tech Lead, Manager · Backend, Frontend |

## CI/CD & deployment (8)

| Skill | What it does | For |
|---|---|---|
| [`branch-environment-promotion-check`](skills/branch-environment-promotion-check/SKILL.md) | Check that the mapping from branch/tag pattern to deployed environment is unambiguous, so a change can't accidentally deploy to production via an overly broad trigger. | Developer, Reviewer, Tech Lead · DevOps |
| [`build-cache-invalidation-check`](skills/build-cache-invalidation-check/SKILL.md) | Check that a CI build cache invalidates correctly when the lockfile changes, so a stale cache doesn't silently ship old dependency versions. | Developer, Reviewer, Tech Lead · Frontend, DevOps |
| [`cicd-bypass-audit-check`](skills/cicd-bypass-audit-check/SKILL.md) | Check whether a merge/deploy can bypass a required CI check (admin override, "skip ci" tag, manual trigger) and whether that bypass is logged/audited. | Developer, Reviewer, Tech Lead · DevOps |
| [`cicd-secrets-scope-check`](skills/cicd-secrets-scope-check/SKILL.md) | Check that CI/CD secrets are scoped to only the specific job/stage that needs them, not exposed pipeline-wide, and never printed to build logs. | Developer, Reviewer, Tech Lead · DevOps |
| [`deploy-rollback-readiness-check`](skills/deploy-rollback-readiness-check/SKILL.md) | Before shipping a risky change, check that the deployment pipeline has a genuinely fast, tested rollback path — not just "revert and redeploy," which can be too slow for an incident. | Developer, Tech Lead, Manager · DevOps |
| [`env-config-rebuild-check`](skills/env-config-rebuild-check/SKILL.md) | Check whether an environment/config change actually takes effect with a restart, or requires a rebuild because the value is baked into the image/bundle at build time. | Developer, Reviewer, Tech Lead · Frontend, DevOps |
| [`feature-flag-gating-check`](skills/feature-flag-gating-check/SKILL.md) | Check whether a new tenant-visible behavior change should be gated behind the repo's existing feature-flag/tenant-configuration mechanism rather than shipping always-on. | Developer, Tech Lead, Manager · Backend, Frontend |
| [`pipeline-flakiness-check`](skills/pipeline-flakiness-check/SKILL.md) | Check whether a CI pipeline failure is a real regression or environment/infra flakiness, and that a flaky step isn't silently retried/ignored in a way that masks genuine failures. | Developer, Tester, Tech Lead · DevOps |

## Operations & reliability (6)

| Skill | What it does | For |
|---|---|---|
| [`structured-logging-check`](skills/structured-logging-check/SKILL.md) | Check that new log lines are structured, carry the context needed to debug (request id, user or account id, operation), use the right level, and never contain secrets or personal data. | Developer, Tech Lead · Backend, DevOps |
| [`alert-actionability-check`](skills/alert-actionability-check/SKILL.md) | Check that a new or changed alert fires on user-visible symptoms, has a clear owner and runbook, and won't page for noise. | Reviewer, Tech Lead · DevOps |
| [`slo-definition`](skills/slo-definition/SKILL.md) | Define service level indicators, objectives, and an error budget for a service or user journey, grounded in the metrics that already exist. | Tech Lead, Manager · Backend, DevOps |
| [`runbook-doc`](skills/runbook-doc/SKILL.md) | Write an operational runbook for an alert, service, or routine task: how to recognise the problem, check it, mitigate it, and escalate. | Developer, Tech Lead · DevOps |
| [`health-check-endpoint-check`](skills/health-check-endpoint-check/SKILL.md) | Check that liveness and readiness endpoints report what the orchestrator needs and don't cause outages themselves. | Developer, Tech Lead · Backend, DevOps |
| [`graceful-shutdown-check`](skills/graceful-shutdown-check/SKILL.md) | Check that a service finishes in-flight work and releases resources cleanly when it receives a termination signal during deploys and scaling. | Developer, Tech Lead · Backend, DevOps |

## Cloud cost & planning (4)

| Skill | What it does | For |
|---|---|---|
| [`aws-cost-estimate`](skills/aws-cost-estimate/SKILL.md) | Estimate the monthly AWS bill for an architecture, feature, or infrastructure-as-code change, itemised by service with every usage assumption written down, using current prices from AWS's own sources. | Developer, Tech Lead, Manager · DevOps |
| [`aws-budget-guardrails`](skills/aws-budget-guardrails/SKILL.md) | Set up cost guardrails for an AWS account or workload: AWS Budgets with alert thresholds, Cost Anomaly Detection, cost-allocation tags, and a review routine, as infrastructure-as-code where the repo has it. | Tech Lead, Manager · DevOps |
| [`effort-estimation`](skills/effort-estimation/SKILL.md) | Estimate the effort for a feature, ticket, or project as a range with explicit assumptions and risks, grounded in the actual codebase rather than the description alone. | Developer, Tech Lead, Manager · Any stack |
| [`cr-feasibility`](skills/cr-feasibility/SKILL.md) | Answer a fixed set of feasibility questions for a Change Request, and save the result under the Change Request folder. | Tech Lead, Manager · Any stack |

## Testing (6)

| Skill | What it does | For |
|---|---|---|
| [`mocking-boundary-check`](skills/mocking-boundary-check/SKILL.md) | Check that mocks are placed at the actual system boundary (external API, paid service), not on internal collaborators — over-mocking internal logic lets a test pass even when the real integration between two internal parts is broken. | Developer, Tester, Reviewer · Backend, Frontend |
| [`regression-test-for-bugfix-check`](skills/regression-test-for-bugfix-check/SKILL.md) | Check that a bug-fix PR includes a test that would have failed before the fix and passes after — without it, the bug can silently reappear. | Developer, Tester, Reviewer · Backend, Frontend |
| [`test-coverage-gap-check`](skills/test-coverage-gap-check/SKILL.md) | Check that new/changed business logic has a test covering the specific behavior change — not just that overall coverage percentage didn't drop. | Developer, Tester, Reviewer · Backend, Frontend |
| [`test-data-realism-check`](skills/test-data-realism-check/SKILL.md) | Check that test fixtures reflect realistic edge cases (nulls, boundary values, multi-tenant data) rather than only a clean happy-path shape. | Developer, Tester, Reviewer · Backend, Frontend |
| [`test-flakiness-root-cause-check`](skills/test-flakiness-root-cause-check/SKILL.md) | Find the actual cause of a flaky test (timing/order dependence, shared mutable state, unmocked clock/network) instead of retrying or skipping it. | Developer, Tester · Backend, Frontend, DevOps |
| [`test-isolation-check`](skills/test-isolation-check/SKILL.md) | Check that tests don't leak state between runs — shared DB rows, module-level caches, or global singletons not reset — causing order-dependent pass/fail. | Developer, Tester, Reviewer · Backend, Frontend |

## Frontend & UX (7)

| Skill | What it does | For |
|---|---|---|
| [`accessibility-check`](skills/accessibility-check/SKILL.md) | Check UI changes for common accessibility failures: missing labels, keyboard traps, focus handling, colour contrast, semantic structure, and screen-reader announcements. | Developer, Tester, Reviewer · Frontend |
| [`i18n-readiness-check`](skills/i18n-readiness-check/SKILL.md) | Check UI and message code for hard-coded strings, concatenated sentences, locale-unaware formatting of dates/numbers/currency, and layouts that break with longer text or right-to-left scripts. | Developer, Tester, Reviewer · Frontend |
| [`responsive-layout-check`](skills/responsive-layout-check/SKILL.md) | Check that a UI change works across screen sizes, orientations, zoom levels, and touch input: no horizontal scroll, readable text, reachable controls, and adequate tap targets. | Developer, Tester, Reviewer · Frontend |
| [`empty-state-check`](skills/empty-state-check/SKILL.md) | Check that a list/table/dashboard view has a designed empty state for both cases — genuinely no data yet, and a filter/search returning zero results — since these need different messaging and are commonly conflated or missed entirely. | Developer, Tester, Reviewer · Frontend |
| [`error-state-actionability-check`](skills/error-state-actionability-check/SKILL.md) | Check that a UI error message tells the user what to do next, not just what failed — distinct from checking whether the message leaks sensitive data. | Developer, Tester, Reviewer · Frontend |
| [`form-validation-timing-check`](skills/form-validation-timing-check/SKILL.md) | Check when a form field's validation actually fires — on every keystroke, on blur, or only on submit — since the wrong timing makes a technically-correct validator feel punishing or feel broken. | Developer, Tester, Reviewer · Frontend |
| [`loading-state-consistency-check`](skills/loading-state-consistency-check/SKILL.md) | Check for a race between a loading flag and stale data — a component that clears "loading" before new data has actually replaced the old, showing outdated content as if it were current. | Developer, Tester, Reviewer · Frontend |

## Docs & writing (10)

| Skill | What it does | For |
|---|---|---|
| [`pr-description`](skills/pr-description/SKILL.md) | Generate a PR description for the current branch's diff, using a fixed section template and an evidence-backed depth bar (measured query counts, equivalence proofs, before/after tables — not asserted claims). | Developer, Reviewer · Any stack |
| [`changelog-release-notes`](skills/changelog-release-notes/SKILL.md) | Write release notes or a changelog entry from the actual commits and merged PRs between two versions, grouped for the intended reader. | Developer, Tech Lead, Manager · Any stack |
| [`adr-doc`](skills/adr-doc/SKILL.md) | Write an Architecture Decision Record capturing a significant technical decision: context, options considered, the decision, and its consequences. | Developer, Tech Lead · Any stack |
| [`proposal-doc`](skills/proposal-doc/SKILL.md) | Draft a technical/architecture proposal document and save it under the Proposal folder (not RCA). | Tech Lead, Manager · Any stack |
| [`implementation-doc`](skills/implementation-doc/SKILL.md) | Draft an implementation document for an already-approved Change Request, and save it under the Implementation folder (not RCA, not Proposal). | Developer, Tech Lead · Any stack |
| [`rca-doc`](skills/rca-doc/SKILL.md) | Write a Root Cause Analysis document for a bug/incident that has already been diagnosed in this session, and save it under the RCA folder. | Developer, Tech Lead, Manager · Any stack |
| [`incident-postmortem`](skills/incident-postmortem/SKILL.md) | Write a structured incident postmortem for a customer-impacting production incident, distinct from a code-level RCA — covers detection, communication, and follow-up actions, not just root cause. | Tech Lead, Manager · DevOps |
| [`user-guide-doc`](skills/user-guide-doc/SKILL.md) | Draft an end-user-facing guide (not a technical doc) for a feature, and save it under the User Guide folder. | Developer, Tester, Manager · Frontend |
| [`onboarding-doc`](skills/onboarding-doc/SKILL.md) | Write a getting-started guide that takes a new contributor from clone to running, testing, and shipping a first change, verified against the repo's actual tooling. | Developer, Tech Lead · Any stack |
| [`repo-map`](skills/repo-map/SKILL.md) | Give agents a map of the codebase by writing an AGENTS.md into each significant directory: what that directory is responsible for, and an index of its files with a one-line brief each. | Developer, Tech Lead · Any stack |

## Project tracking (2)

| Skill | What it does | For |
|---|---|---|
| [`jira-epic-context`](skills/jira-epic-context/SKILL.md) | Before starting work on a Jira ticket, pull its full context through whatever Jira access is available (Atlassian MCP tools, the Jira REST API or CLI, or text the user pastes) — the ticket itself, its epic, linked tickets, and any linked Confluence page — and summarize what's relevant to the task at hand. | Developer, Tester, Tech Lead · Any stack |
| [`jira-sprint-hygiene-check`](skills/jira-sprint-hygiene-check/SKILL.md) | Audit a sprint/board for hygiene issues — tickets with no acceptance criteria, no estimate, or stale in "In Progress" — as a board-level check distinct from reviewing one ticket at a time. | Tech Lead, Manager · Any stack |
