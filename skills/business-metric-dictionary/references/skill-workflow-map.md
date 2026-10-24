# Skill workflow map

Canonical copy: `shared/references/skill-workflow-map.md`.

## 1. Main flow

```
market-opportunity-research
  → saas-prospect-qualification
    → client-discovery-synthesis
      → consulting-proposal-builder
        → business-data-inventory
          → data-readiness-assessment
            → business-metric-dictionary
              → cross-module-data-mapping
                → revenue-intelligence ─┐
                → customer-intelligence ├→ anomaly-hypothesis-validation
                → product-intelligence  │
                → operational-technology-intelligence ┘
                  → bidim-opportunity-scoring
                    → executive-decision-intelligence
                      → intelligence-report-builder
                        → intelligence-quality-audit ──(needs revision)──┐
                                    ↑                                   │
                                    └──────────── corrections ──────────┘
```

The flow is a dependency order, not a mandatory sequence. A small engagement may skip market research and prospect qualification. Nothing after `consulting-proposal-builder` may skip `data-readiness-assessment`.

## 2. Handoffs

| Producer | Artefact | Consumers | Contract |
|---|---|---|---|
| market-opportunity-research | Opportunity research report, hypotheses | saas-prospect-qualification | Handoff envelope; `payload.hypotheses[]` |
| saas-prospect-qualification | Prospect profile, ICP score | client-discovery-synthesis, consulting-proposal-builder | Handoff envelope; `payload.icp_score` |
| client-discovery-synthesis | Discovery summary, decision inventory, data requirements | consulting-proposal-builder, business-data-inventory, bidim-opportunity-scoring (strategic fit) | Handoff envelope; `payload.decisions[]`, `payload.data_requirements[]` |
| consulting-proposal-builder | Proposal draft, data request | Human approval, then business-data-inventory | Markdown proposal plus data request table |
| business-data-inventory | System, dataset and field inventory | data-readiness-assessment, cross-module-data-mapping | `inventory_files.py` JSON output plus the business-ownership table |
| data-readiness-assessment | Readiness scores, suitability per analysis | All analysis skills, bidim (data readiness D) | `assess_readiness.py` JSON output |
| business-metric-dictionary | Approved definitions | All analysis skills, report builder, audit | Dictionary JSON (`metric-dictionary.example.json`) |
| cross-module-data-mapping | Join map, entity-resolution map | All analysis skills | `profile_join.py` JSON per relationship plus the join register |
| revenue-intelligence | Revenue metrics, per-customer MRR | customer-, operational-technology-intelligence, anomaly, bidim, exec, report, audit | `revenue_metrics.py` JSON |
| product-intelligence | Usage metrics, per-account usage | customer-intelligence, anomaly, bidim, report | `product_adoption.py` JSON |
| customer-intelligence | Segments, health signals | bidim, exec, report | `customer_segments.py` JSON |
| operational-technology-intelligence | Unit costs, cost movements | anomaly, bidim, exec, report | `unit_costs.py` JSON |
| anomaly-hypothesis-validation | Anomaly records with tested hypotheses | bidim, exec, report | `detect_anomalies.py` JSON plus the hypothesis table |
| bidim-opportunity-scoring | Scored opportunity register | executive-decision-intelligence, report | `bidim_score.py` JSON |
| executive-decision-intelligence | Decision briefs per audience | intelligence-report-builder | Decision brief Markdown or JSON |
| intelligence-report-builder | Report plus evidence appendix | intelligence-quality-audit | Markdown report plus `claims.json` plus evidence register |
| intelligence-quality-audit | Verdict, issues, corrections | Report owner (human), report builder | `audit_report.py` JSON plus the reviewer narrative |

Every artefact is wrapped in the handoff envelope (`references/handoff-envelope.schema.json`) when it is passed between skills as JSON.

## 3. No simulated upstream work

A skill must not pretend another skill has run.

- If a required upstream artefact is missing, say so. Then either (a) ask for it, (b) run that skill explicitly and label its output as that skill's output, or (c) continue in **degraded mode**: mark the dependent conclusions `UNKNOWN` or `ASSUME` and cap confidence at Low.
- Never write "the readiness assessment found..." unless you hold its actual output.
- Record the upstream artefact IDs you consumed in `inputs[]` of your envelope.

## 4. Engagement working directory (suggested)

```
engagement-<id>/
  00-admin/         approvals, scope (no credentials)
  01-discovery/     notes, discovery-synthesis output
  02-data/raw/      client exports (read-only; never edited)
  02-data/work/     cleaned copies, entity-resolution map
  03-outputs/       script JSON outputs, one file per run
  04-report/        report drafts, claims.json, evidence register
  05-audit/         audit outputs
```

Keep one engagement per directory. Never mix clients.
