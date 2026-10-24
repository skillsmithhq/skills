#!/usr/bin/env python3
"""Infrastructure and technology unit costs, linked to revenue-intelligence output.

Outputs per month: total cost by environment and service, month-over-month change, cost per active customer
(OPS-1, all environments and production only), and the infrastructure cost ratio (OPS-2 = cost / MRR).
OPS-2 is not gross margin: other cost of revenue (support staff, third-party services) is not included.

Optional savings scenario (JSON): savings are computed only against a stated baseline month, with explicit
assumptions and change rules. Without assumptions the scenario is refused.
  {"baseline_month": "2026-05", "assumptions": ["..."], "annualise": false,
   "changes": [{"match": {"environment": "staging", "service": "compute"}, "reduction_pct": 100}]}

Usage: python3 unit_costs.py --costs infrastructure_costs.csv --revenue revenue.json [--currency USD]
                             [--production-label production] [--scenario scenario.json]
"""
import argparse
import csv
import json
import sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--costs", required=True)
    ap.add_argument("--revenue", required=True)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--production-label", default="production")
    ap.add_argument("--scenario")
    a = ap.parse_args()
    rev = json.load(open(a.revenue))
    with open(a.costs, newline="", encoding="utf-8-sig") as f:
        lines = list(csv.DictReader(f))
    skipped = [l for l in lines if l["currency"].strip().upper() != a.currency]
    lines = [l for l in lines if l["currency"].strip().upper() == a.currency]
    by_month = defaultdict(lambda: {"total": 0.0, "by_environment": defaultdict(float), "by_service": defaultdict(float)})
    for l in lines:
        m = by_month[l["month"]]
        c = float(l["cost"])
        m["total"] += c
        m["by_environment"][l["environment"]] += c
        m["by_service"][f"{l['environment']}/{l['service']}"] += c
    rev_by_month = {m["month"]: m for m in rev["monthly"]}
    monthly, prev = [], None
    for month in sorted(by_month):
        m = by_month[month]
        r = rev_by_month.get(month)
        prod_cost = m["by_environment"].get(a.production_label, 0.0)
        row = {"month": month, "total": m["total"], "by_environment": dict(m["by_environment"]),
               "by_service": dict(sorted(m["by_service"].items())),
               "mom_change": None if prev is None else m["total"] - prev,
               "mom_change_pct": None if not prev else round(100 * (m["total"] - prev) / prev, 2)}
        if r and r["active_customers"]:
            row["active_customers"] = r["active_customers"]
            row["cost_per_active_customer"] = round(m["total"] / r["active_customers"], 2)
            row["production_cost_per_active_customer"] = round(prod_cost / r["active_customers"], 2)
        if r and r["mrr"]:
            row["infrastructure_cost_ratio_pct"] = round(100 * m["total"] / r["mrr"], 2)
        monthly.append(row)
        prev = m["total"]

    scenario = None
    if a.scenario:
        sc = json.load(open(a.scenario))
        if not sc.get("assumptions"):
            sys.exit("scenario refused: list the assumptions behind the savings")
        if sc.get("baseline_month") not in by_month:
            sys.exit("scenario refused: baseline_month must be a month present in the cost data")
        base_lines = [l for l in lines if l["month"] == sc["baseline_month"]]
        changes = []
        for ch in sc["changes"]:
            hit = [l for l in base_lines if all(l.get(k) == v for k, v in ch["match"].items())]
            base = sum(float(l["cost"]) for l in hit)
            changes.append({"match": ch["match"], "baseline_cost": base, "reduction_pct": ch["reduction_pct"],
                            "monthly_saving": round(base * ch["reduction_pct"] / 100, 2)})
        monthly_saving = sum(c["monthly_saving"] for c in changes)
        scenario = {"baseline_month": sc["baseline_month"], "baseline_total": by_month[sc["baseline_month"]]["total"],
                    "assumptions": sc["assumptions"], "changes": changes, "monthly_saving_vs_baseline": monthly_saving,
                    "annualised_saving": monthly_saving * 12 if sc.get("annualise") else None,
                    "caveat": "Hypothesis: valid only if the baseline lines would otherwise recur and the assumptions hold."}
    print(json.dumps({
        "skill": "operational-technology-intelligence", "currency": a.currency, "monthly": monthly,
        "skipped_lines_other_currency": len(skipped),
        "definitions": {"OPS-1": "cost / active customers at month end", "OPS-2": "cost / MRR at month end (not gross margin)"},
        "scenario": scenario,
        "evidence": [{"id": f"ops-cost-{m['month']}", "class": "CALC", "produced_by": "operational-technology-intelligence",
                      "statement": f"infrastructure {m['total']:.0f} {a.currency}; per active customer {m.get('cost_per_active_customer')}; "
                                   f"ratio to MRR {m.get('infrastructure_cost_ratio_pct')}%"} for m in monthly],
    }, indent=2))


if __name__ == "__main__":
    main()
