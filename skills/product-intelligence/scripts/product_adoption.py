#!/usr/bin/env python3
"""Deterministic product usage metrics from users and product events.

Definitions (references/saas-metric-definitions.md): MAU-1, ADOPT-1, ZERO-1, ACT-1.
  - Events are valid only if the user exists and the timestamp lies in [2000-01-01, as_of end of day].
    Invalid events are counted by reason and excluded.
  - Event coverage = first to last valid event date. Missing days inside coverage are listed.
  - Activation cohort = users created from coverage start to (coverage end - window days), so every cohort
    user has a full observation window inside the data.
  - Paying accounts come from the revenue-intelligence output (customers with MRR > 0 at the month end).
    Without it, adoption is reported over accounts with users and labelled as such.

Usage: python3 product_adoption.py --data-dir DIR --month YYYY-MM --as-of YYYY-MM-DD
         [--revenue revenue.json] [--activation-event report_created] [--activation-days 14]
         [--weeks-from YYYY-MM-DD --weeks-to YYYY-MM-DD] [--entity-map MAP.csv]
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
from collections import defaultdict

MIN_TS = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def ts(v):
    try:
        t = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--as-of", required=True)
    ap.add_argument("--revenue")
    ap.add_argument("--activation-event", default="report_created")
    ap.add_argument("--activation-days", type=int, default=14)
    ap.add_argument("--weeks-from")
    ap.add_argument("--weeks-to")
    ap.add_argument("--entity-map")
    a = ap.parse_args()
    d = pathlib.Path(a.data_dir)
    as_of = dt.date.fromisoformat(a.as_of)
    upper = dt.datetime.combine(as_of + dt.timedelta(days=1), dt.time(), tzinfo=dt.timezone.utc)
    entity = {r["raw_id"]: r["entity_id"] for r in read(a.entity_map)} if a.entity_map else {}
    users = {u["user_id"]: {"account": entity.get(u["customer_id"], u["customer_id"]),
                            "created": dt.date.fromisoformat(u["created_at"][:10])} for u in read(d / "users.csv")}

    invalid = defaultdict(int)
    events = []
    for e in read(d / "product_events.csv"):
        t = ts(e["occurred_at"])
        if e["user_id"] not in users:
            invalid["unknown_user"] += 1
        elif t is None:
            invalid["unparseable_timestamp"] += 1
        elif not MIN_TS <= t < upper:
            invalid["implausible_timestamp"] += 1
        else:
            events.append({"user": e["user_id"], "account": users[e["user_id"]]["account"], "name": e["event_name"], "t": t})
    days = sorted({e["t"].date() for e in events})
    cov_start, cov_end = days[0], days[-1]
    present = set(days)
    missing = [(cov_start + dt.timedelta(i)).isoformat() for i in range((cov_end - cov_start).days + 1)
               if cov_start + dt.timedelta(i) not in present]

    month_events = [e for e in events if e["t"].strftime("%Y-%m") == a.month]
    mau_users = sorted({e["user"] for e in month_events})
    if a.revenue:
        rev = json.loads(pathlib.Path(a.revenue).read_text())
        paying = sorted(c for c, m in rev["customer_mrr"].items() if m.get(a.month, 0) > 0)
        basis = f"paying accounts (MRR > 0 at {a.month} end, from revenue-intelligence output)"
    else:
        paying = sorted({u["account"] for u in users.values()})
        basis = "all accounts with users (no revenue input: NOT paying accounts)"
    features = sorted({e["name"] for e in events})
    by_account = defaultdict(set)
    users_by_account = defaultdict(set)
    for e in month_events:
        by_account[e["account"]].add(e["name"])
        users_by_account[e["account"]].add(e["user"])
    adoption = {}
    for f in features:
        accts = sorted(acc for acc in paying if f in by_account.get(acc, set()))
        adoption[f] = {"accounts": len(accts), "of": len(paying), "pct": round(100 * len(accts) / len(paying), 2) if paying else None,
                       "account_ids": accts}
    zero = [acc for acc in paying if not by_account.get(acc)]

    window = a.activation_days
    cohort_end = cov_end - dt.timedelta(days=window)
    first_act = {}
    for e in events:
        if e["name"] == a.activation_event:
            first_act[e["user"]] = min(first_act.get(e["user"], e["t"]), e["t"])
    cohort = []
    for uid, u in sorted(users.items()):
        if cov_start <= u["created"] <= cohort_end:
            t = first_act.get(uid)
            delta = (t.date() - u["created"]).days if t else None
            cohort.append({"user_id": uid, "account": u["account"], "created": u["created"].isoformat(),
                           "days_to_activation": delta, "activated": delta is not None and 0 <= delta <= window})
    excluded_before = sum(u["created"] < cov_start for u in users.values())
    excluded_after = sum(u["created"] > cohort_end for u in users.values())
    act_n = sum(c["activated"] for c in cohort)

    weekly = []
    if a.weeks_from and a.weeks_to:
        w = dt.date.fromisoformat(a.weeks_from)
        w -= dt.timedelta(days=w.weekday())
        last = dt.date.fromisoformat(a.weeks_to)
        while w <= last:
            n = sum(w <= e["t"].date() < w + dt.timedelta(days=7) for e in events)
            weekly.append({"period": w.isoformat(), "value": n})  # weeks with no events are kept as 0
            w += dt.timedelta(days=7)

    warnings = []
    if len(cohort) < 30:
        warnings.append(f"activation cohort n={len(cohort)} (< 30): report the count and avoid rate comparisons")
    if missing:
        warnings.append(f"{len(missing)} days inside coverage have no events at all: likely collection gap; check before trend analysis")
    if excluded_before:
        warnings.append(f"{excluded_before} users created before event coverage starts: activation not measurable for them")
    print(json.dumps({
        "skill": "product-intelligence", "month": a.month, "as_of": a.as_of,
        "definitions": ["MAU-1", "ADOPT-1", "ZERO-1", "ACT-1"],
        "invalid_events": dict(invalid), "valid_events": len(events),
        "coverage": {"first": cov_start.isoformat(), "last": cov_end.isoformat(), "missing_days": missing},
        "mau": len(mau_users), "mau_users": mau_users,
        "adoption_basis": basis, "paying_accounts": paying, "feature_adoption": adoption,
        "zero_usage_paying_accounts": zero,
        "account_usage": {acc: {"active_users": len(users_by_account.get(acc, ())), "features": sorted(by_account.get(acc, ()))}
                          for acc in paying},
        "activation": {"event": a.activation_event, "window_days": window,
                       "cohort_rule": f"users created {cov_start.isoformat()}..{cohort_end.isoformat()}",
                       "cohort_size": len(cohort), "activated": act_n,
                       "rate_pct": round(100 * act_n / len(cohort), 2) if cohort else None,
                       "excluded_created_before_coverage": excluded_before, "excluded_window_incomplete": excluded_after,
                       "users": cohort},
        "weekly_events": weekly, "warnings": warnings,
        "evidence": [
            {"id": f"prod-mau-{a.month}", "class": "CALC", "statement": f"MAU {len(mau_users)}", "period": a.month, "produced_by": "product-intelligence"},
            {"id": f"prod-adoption-{a.month}", "class": "CALC", "statement": "; ".join(f"{k} {v['accounts']}/{v['of']}" for k, v in adoption.items()),
             "period": a.month, "produced_by": "product-intelligence"},
            {"id": f"prod-zero-usage-{a.month}", "class": "CALC", "statement": f"zero-usage paying accounts: {', '.join(zero) or 'none'}",
             "period": a.month, "produced_by": "product-intelligence"},
            {"id": "prod-activation", "class": "CALC", "statement": f"activation {act_n}/{len(cohort)}", "period": f"cohort {cov_start}..{cohort_end}",
             "produced_by": "product-intelligence"},
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
