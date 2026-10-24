#!/usr/bin/env python3
"""Customer segmentation, retention by segment, support burden and health signals.

Consumes the JSON outputs of revenue-intelligence (required) and product-intelligence (optional) rather
than recalculating them, plus the customers table and (optionally) support tickets.

Health signals per active customer at the end month (each is an observation, not a prediction):
  contraction   MRR at end below MRR at start (still > 0)
  zero_usage    no valid product events in the end month (needs product output)
  overdue       overdue receivable at the as-of date
  ticket_load   >= 3 tickets in the 60 days to the as-of date
Customers with >= 2 signals are listed for review.

Profitability is reported only when --costs (customer_id,cost per period) is supplied.

Usage: python3 customer_segments.py --customers customers.csv --revenue revenue.json
         [--product product.json] [--tickets support_tickets.csv --ticket-normalise digits:C:3]
         [--entity-map MAP.csv] [--segments SMB,Mid-Market,Enterprise] [--costs costs.csv]
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
from collections import defaultdict


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def normaliser(spec):
    m = re.fullmatch(r"digits:([A-Za-z]*):(\d+)", spec or "")
    if not m:
        return lambda v: v.strip()
    prefix, width = m.group(1), int(m.group(2))
    return lambda v: f"{prefix}{int(re.sub(r'[^0-9]', '', v)):0{width}d}" if re.search(r"\d", v) else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", required=True)
    ap.add_argument("--revenue", required=True)
    ap.add_argument("--product")
    ap.add_argument("--tickets")
    ap.add_argument("--ticket-normalise")
    ap.add_argument("--entity-map")
    ap.add_argument("--segments", default="SMB,Mid-Market,Enterprise")
    ap.add_argument("--costs")
    a = ap.parse_args()
    rev = json.load(open(a.revenue))
    prod = json.load(open(a.product)) if a.product else None
    entity = {r["raw_id"]: r["entity_id"] for r in read(a.entity_map)} if a.entity_map else {}
    canonical = {s.lower(): s for s in a.segments.split(",")}
    start_m, end_m = rev["period"]["start"], rev["period"]["end"]
    as_of = dt.date.fromisoformat(rev["as_of"])

    segment, notes = {}, []
    records = read(a.customers)
    # Each entity takes the segment of its own record; merged duplicates only fill gaps or raise conflicts.
    for own_first in (True, False):
        for c in records:
            e = entity.get(c["customer_id"], c["customer_id"])
            if (c["customer_id"] == e) != own_first:
                continue
            seg = canonical.get(c["segment"].strip().lower())
            if seg is None:
                notes.append(f"{c['customer_id']}: unknown segment {c['segment']!r}")
                seg = "Unknown"
            if e not in segment:
                segment[e] = seg
            elif segment[e] != seg:
                notes.append(f"{e}: segment conflict with merged record {c['customer_id']} ({segment[e]} vs {seg})")
    cmrr = rev["customer_mrr"]
    recv = rev["collections"]["customer_receivables"]
    excluded = defaultdict(list)  # customers whose subscriptions revenue-intelligence excluded for data quality
    for x in rev.get("exclusions", []):
        excluded[entity.get(x["customer_id"], x["customer_id"])].append(x["reason"])

    tickets = defaultdict(list)
    unresolved = 0
    if a.tickets:
        norm = normaliser(a.ticket_normalise)
        for t in read(a.tickets):
            e = entity.get(norm(t["customer_ref"]), norm(t["customer_ref"]))
            if e in segment:
                tickets[e].append(dt.datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")).date())
            else:
                unresolved += 1
    since = as_of - dt.timedelta(days=60)

    rows = {}
    for e in sorted(segment):
        s, f = cmrr.get(e, {}).get(start_m, 0), cmrr.get(e, {}).get(end_m, 0)
        status = ("churned" if s > 0 and f == 0 else "new" if s == 0 and f > 0 else "expanded" if f > s > 0
                  else "contracted" if 0 < f < s else "flat" if s > 0
                  else "excluded-from-mrr" if e in excluded else "no-mrr-in-period")
        r = {"segment": segment[e], "mrr_start": s, "mrr_end": f, "status": status,
             "outstanding": recv.get(e, {}).get("outstanding", 0.0), "overdue": recv.get(e, {}).get("overdue", 0.0),
             **({"exclusion_reasons": excluded[e]} if e in excluded else {}),
             "tickets": len(tickets[e]) if a.tickets else None,
             "tickets_last_60d": sum(d > since for d in tickets[e]) if a.tickets else None}
        if prod and f > 0:
            r["zero_usage_end_month"] = e in prod["zero_usage_paying_accounts"]
        signals = []
        if status == "contracted":
            signals.append("contraction")
        if r.get("zero_usage_end_month"):
            signals.append("zero_usage")
        if r["overdue"] > 0:
            signals.append("overdue")
        if (r["tickets_last_60d"] or 0) >= 3:
            signals.append("ticket_load")
        r["signals"] = signals if f > 0 else []
        rows[e] = r

    total_end = sum(r["mrr_end"] for r in rows.values())
    segs = {}
    for seg in sorted({r["segment"] for r in rows.values()}):
        members = {e: r for e, r in rows.items() if r["segment"] == seg}
        cohort = [e for e, r in members.items() if r["mrr_start"] > 0]
        cs = sum(members[e]["mrr_start"] for e in cohort)
        ce = sum(members[e]["mrr_end"] for e in cohort)
        active = [e for e, r in members.items() if r["mrr_end"] > 0]
        t_active = sum(members[e]["tickets"] or 0 for e in active) if a.tickets else None
        segs[seg] = {"cohort": cohort, "cohort_start_mrr": cs, "cohort_end_mrr": ce,
                     "nrr_pct": round(100 * ce / cs, 2) if cs else None,
                     "logos_retained": f"{sum(members[e]['mrr_end'] > 0 for e in cohort)}/{len(cohort)}",
                     "active_at_end": active, "mrr_end": sum(members[e]["mrr_end"] for e in active),
                     "share_of_mrr_pct": round(100 * sum(members[e]["mrr_end"] for e in active) / total_end, 2) if total_end else None,
                     "tickets_active_accounts": t_active,
                     "tickets_per_active_account": round(t_active / len(active), 2) if a.tickets and active else None,
                     "sample_note": "n < 5 customers: describe, do not generalise" if len(cohort) < 5 else ""}

    churned = [e for e, r in rows.items() if r["status"] == "churned"]
    retained = [e for e, r in rows.items() if r["status"] in ("flat", "expanded", "contracted")]
    comparison = None
    if a.tickets and churned and retained:
        comparison = {"metric": "tickets per customer in period",
                      "churned": {"n": len(churned), "mean": round(statistics.mean(rows[e]["tickets"] for e in churned), 2)},
                      "retained": {"n": len(retained), "mean": round(statistics.mean(rows[e]["tickets"] for e in retained), 2)},
                      "confidence_cap": "Low" if len(churned) < 5 else "Medium",
                      "note": "Descriptive only. No test run; association, not cause."}
    profitability = {"assessed": False, "reason": "no customer-level cost allocation supplied"}
    if a.costs:
        cost = defaultdict(float)
        for r in read(a.costs):
            cost[entity.get(r["customer_id"], r["customer_id"])] += float(r["cost"])
        profitability = {"assessed": True, "basis": "supplied allocation; check its method before use",
                         "by_customer": {e: {"mrr_end": rows[e]["mrr_end"], "allocated_cost": cost.get(e, 0.0)} for e in rows}}

    review = [e for e, r in rows.items() if len(r["signals"]) >= 2]
    print(json.dumps({
        "skill": "customer-intelligence", "period": rev["period"], "as_of": rev["as_of"],
        "inputs": {"revenue": a.revenue and os.path.basename(a.revenue), "product": a.product and os.path.basename(a.product),
                   "tickets": a.tickets and os.path.basename(a.tickets), "entity_map": bool(entity)},
        "notes": notes, "unresolved_tickets": unresolved,
        "segments": segs, "customers": rows, "review_list": review,
        "churned_vs_retained": comparison, "profitability": profitability,
        "evidence": [{"id": f"cust-seg-{s.lower()}", "class": "CALC", "produced_by": "customer-intelligence",
                      "statement": f"{s}: NRR {v['nrr_pct']}%, logos {v['logos_retained']}, {v['share_of_mrr_pct']}% of {end_m} MRR"}
                     for s, v in segs.items()] +
                    [{"id": f"cust-health-{e.lower()}", "class": "CALC", "produced_by": "customer-intelligence",
                      "statement": f"{e} signals at {end_m}: {', '.join(rows[e]['signals'])}"} for e in review],
    }, indent=2))


if __name__ == "__main__":
    main()
