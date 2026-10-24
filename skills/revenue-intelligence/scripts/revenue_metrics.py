#!/usr/bin/env python3
"""Deterministic revenue metrics from subscription, invoice and payment exports.

Definitions (see references/saas-metric-definitions.md): MRR-1, ARR-1, MOV-1, GROWTH-1, NRR-1, GRR-1,
CHURN-L1, CHURN-R1, ARPA-1, CONC-1, RECUR-1, COLL-1, AR-1.

Data rules applied, and reported in the output:
  - subscriptions with no start_date are excluded (cannot be placed in time)
  - currency codes normalised for case and whitespace only; non-ISO codes are excluded
  - only the reporting currency is summed (no FX conversion is attempted)
  - exact duplicate invoice IDs are counted once
  - an optional entity map (raw_id,entity_id,reason) merges duplicate customers

Input files in --data-dir: subscriptions.csv, invoices.csv, payments.csv, with the column names used in the
collection's fixtures. Rename client columns to these names in a working copy first (record the mapping).
Usage: python3 revenue_metrics.py --data-dir DIR --start YYYY-MM --end YYYY-MM --as-of YYYY-MM-DD
                                  [--currency USD] [--entity-map MAP.csv]
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import pathlib

ISO_SAMPLE = {"USD", "EUR", "GBP", "INR", "AUD", "CAD", "JPY", "CHF", "SEK", "NOK", "DKK", "NZD", "SGD", "ZAR", "BRL", "MXN"}


def month_end(ym):
    y, m = map(int, ym.split("-"))
    return dt.date(y, m, calendar.monthrange(y, m)[1])


def months(start, end):
    y, m = map(int, start.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= end:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def pct(x):
    return None if x is None else round(100 * x, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--as-of", required=True)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--entity-map")
    a = ap.parse_args()
    d = pathlib.Path(a.data_dir)
    as_of = dt.date.fromisoformat(a.as_of)
    entity = {}
    if a.entity_map:
        entity = {r["raw_id"]: r["entity_id"] for r in read(a.entity_map)}
    ent = lambda c: entity.get(c, c)
    cur_ok = lambda c: c.strip().upper() == a.currency

    exclusions, normalisations, subs = [], [], []
    for s in read(d / "subscriptions.csv"):
        amount = float(s["mrr_amount"])
        raw_cur = s["currency"]
        if not s["start_date"].strip():
            exclusions.append({"subscription_id": s["subscription_id"], "customer_id": s["customer_id"], "mrr": amount, "reason": "missing start_date"})
            continue
        if not cur_ok(raw_cur):
            reason = "non-reporting currency (no FX applied)" if raw_cur.strip().upper() in ISO_SAMPLE else f"invalid currency code {raw_cur!r}"
            exclusions.append({"subscription_id": s["subscription_id"], "customer_id": s["customer_id"], "mrr": amount, "reason": reason})
            continue
        if raw_cur != a.currency:
            normalisations.append({"subscription_id": s["subscription_id"], "from": raw_cur, "to": a.currency})
        subs.append({"id": s["subscription_id"], "customer": ent(s["customer_id"]), "mrr": amount,
                     "start": dt.date.fromisoformat(s["start_date"]),
                     "end": dt.date.fromisoformat(s["end_date"]) if s["end_date"].strip() else None})

    period = months(a.start, a.end)
    first_day = dt.date.fromisoformat(f"{a.start}-01")
    prior = (first_day - dt.timedelta(days=1)).strftime("%Y-%m")  # movements in the first month compare with this
    all_months = [prior] + period
    customers = sorted({s["customer"] for s in subs})
    cmrr = {c: {} for c in customers}
    for ym in all_months:
        pe = month_end(ym)
        for c in customers:
            cmrr[c][ym] = sum(s["mrr"] for s in subs if s["customer"] == c and s["start"] <= pe and (s["end"] is None or s["end"] > pe))
    first_start = {c: min(s["start"] for s in subs if s["customer"] == c) for c in customers}

    monthly = []
    for i, ym in enumerate(period):
        prev = all_months[i]
        mov = {"new": 0.0, "reactivation": 0.0, "expansion": 0.0, "contraction": 0.0, "churn": 0.0}
        who = {k: [] for k in mov}
        for c in customers:
            p, q = cmrr[c][prev], cmrr[c][ym]
            if p == 0 and q > 0:
                kind = "new" if first_start[c] > month_end(prev) else "reactivation"
                mov[kind] += q
            elif q > p > 0:
                kind = "expansion"
                mov[kind] += q - p
            elif 0 < q < p:
                kind = "contraction"
                mov[kind] += p - q
            elif p > 0 and q == 0:
                kind = "churn"
                mov[kind] += p
            else:
                continue
            who[kind].append(c)
        total = sum(cmrr[c][ym] for c in customers)
        active = [c for c in customers if cmrr[c][ym] > 0]
        row = {"month": ym, "mrr": total, "arr": total * 12, "active_customers": len(active),
               "arpa": round(total / len(active), 2) if active else None}
        prev_total = sum(cmrr[c][prev] for c in customers)
        bridge = prev_total + mov["new"] + mov["reactivation"] + mov["expansion"] - mov["contraction"] - mov["churn"]
        row["movements_reconcile"] = abs(bridge - total) < 0.005
        row["movements"] = mov
        row["movement_customers"] = {k: v for k, v in who.items() if v}
        monthly.append(row)

    start_m, end_m = period[0], period[-1]
    cohort = [c for c in customers if cmrr[c][start_m] > 0]
    s_mrr = sum(cmrr[c][start_m] for c in cohort)
    e_mrr = sum(cmrr[c][end_m] for c in cohort)
    expansion = sum(max(cmrr[c][end_m] - cmrr[c][start_m], 0) for c in cohort if cmrr[c][end_m] > 0)
    contraction = sum(cmrr[c][start_m] - cmrr[c][end_m] for c in cohort if 0 < cmrr[c][end_m] < cmrr[c][start_m])
    churned = [c for c in cohort if cmrr[c][end_m] == 0]
    churn_mrr = sum(cmrr[c][start_m] for c in churned)
    end_total = monthly[-1]["mrr"]
    ranked = sorted(((cmrr[c][end_m], c) for c in customers if cmrr[c][end_m] > 0), reverse=True)
    window = len(period) - 1
    retention = {
        "start_month": start_m, "end_month": end_m, "window_months": window,
        "label": f"{start_m} to {end_m} ({window}-month window)",
        "cohort_customers": cohort, "cohort_start_mrr": s_mrr, "cohort_end_mrr": e_mrr,
        "expansion": expansion, "contraction": contraction, "churned_mrr": churn_mrr, "churned_customers": churned,
        "nrr_pct": pct(e_mrr / s_mrr) if s_mrr else None,
        "grr_pct": pct((s_mrr - contraction - churn_mrr) / s_mrr) if s_mrr else None,
        "logo_churn_pct": pct(len(churned) / len(cohort)) if cohort else None,
        "gross_revenue_churn_pct": pct((contraction + churn_mrr) / s_mrr) if s_mrr else None,
        "warnings": ([f"window is {window} months; do not compare with 12-month benchmarks"] if window < 12 else []) +
                    ([f"only {len(churned)} churn events: group comparisons capped at Low confidence"] if len(churned) < 5 else []),
    }
    growth = {"from": start_m, "to": end_m, "mrr_start": monthly[0]["mrr"], "mrr_end": end_total,
              "growth_pct": pct((end_total - monthly[0]["mrr"]) / monthly[0]["mrr"]) if monthly[0]["mrr"] else None}
    concentration = {"month": end_m, "top1_customer": ranked[0][1] if ranked else None,
                     "top1_share_pct": pct(ranked[0][0] / end_total) if ranked else None,
                     "top3_customers": [c for _, c in ranked[:3]],
                     "top3_share_pct": pct(sum(v for v, _ in ranked[:3]) / end_total) if ranked else None}

    # Invoices and collections
    raw_inv = read(d / "invoices.csv")
    seen, invoices, dup_ids, dup_amount, bad_cur = set(), [], [], 0.0, []
    p_start, p_end = dt.date.fromisoformat(f"{start_m}-01"), month_end(end_m)
    for r in raw_inv:
        if r["invoice_id"] in seen:
            dup_ids.append(r["invoice_id"])
            dup_amount += float(r["amount"])
            continue
        seen.add(r["invoice_id"])
        if r.get("status") == "void":
            continue
        if not cur_ok(r["currency"]):
            bad_cur.append({"invoice_id": r["invoice_id"], "amount": float(r["amount"]), "currency": r["currency"]})
            continue
        if p_start <= dt.date.fromisoformat(r["invoice_date"]) <= p_end:
            invoices.append(r)
    paid_by_inv = {}
    for p in read(d / "payments.csv"):
        if dt.date.fromisoformat(p["paid_at"][:10]) <= as_of:
            paid_by_inv[p["invoice_id"]] = paid_by_inv.get(p["invoice_id"], 0.0) + float(p["amount"])
    recurring = sum(float(r["amount"]) for r in invoices if r["type"] == "recurring")
    one_off = sum(float(r["amount"]) for r in invoices if r["type"] != "recurring")
    total_inv = recurring + one_off
    paid = sum(min(paid_by_inv.get(r["invoice_id"], 0.0), float(r["amount"])) for r in invoices)
    receivables = {}
    for r in invoices:
        due = float(r["amount"]) - min(paid_by_inv.get(r["invoice_id"], 0.0), float(r["amount"]))
        if due > 0:
            c = ent(r["customer_id"])
            rec = receivables.setdefault(c, {"outstanding": 0.0, "overdue": 0.0, "invoices": []})
            rec["outstanding"] += due
            rec["invoices"].append(r["invoice_id"])
            if dt.date.fromisoformat(r["due_date"]) < as_of:
                rec["overdue"] += due
    collections = {
        "as_of": a.as_of, "raw_invoice_rows": len(raw_inv), "duplicate_invoice_rows_removed": dup_ids,
        "duplicate_amount_removed": dup_amount, "invalid_currency_invoices": len(bad_cur),
        "invalid_currency_amount": sum(b["amount"] for b in bad_cur),
        "invoiced_recurring": recurring, "invoiced_one_off": one_off, "invoiced_total": total_inv,
        "recurring_share_pct": pct(recurring / total_inv) if total_inv else None,
        "paid": paid, "outstanding": round(total_inv - paid, 2),
        "overdue": round(sum(v["overdue"] for v in receivables.values()), 2),
        "collection_rate_pct": pct(paid / total_inv) if total_inv else None,
        "customer_receivables": receivables,
    }

    end_ex = sum(e["mrr"] for e in exclusions)
    ev = lambda i, stmt, period_, defn: {"id": i, "class": "CALC", "statement": stmt, "period": period_,
                                         "method": f"revenue_metrics.py, definition {defn}", "produced_by": "revenue-intelligence"}
    evidence = [ev(f"rev-mrr-{m['month']}", f"MRR {m['mrr']:.0f} {a.currency}", m["month"], "MRR-1") for m in monthly]
    evidence += [
        ev("rev-growth", f"MRR growth {growth['growth_pct']}%", f"{start_m}..{end_m}", "GROWTH-1"),
        ev("rev-nrr", f"NRR {retention['nrr_pct']}% ({retention['label']})", retention["label"], "NRR-1"),
        ev("rev-grr", f"GRR {retention['grr_pct']}%", retention["label"], "GRR-1"),
        ev("rev-logo-churn", f"Logo churn {retention['logo_churn_pct']}% ({len(churned)} of {len(cohort)})", retention["label"], "CHURN-L1"),
        ev("rev-concentration", f"Top customer {concentration['top1_share_pct']}% of MRR; top 3 {concentration['top3_share_pct']}%", end_m, "CONC-1"),
        ev("rev-collections", f"Collection rate {collections['collection_rate_pct']}%; outstanding {collections['outstanding']:.0f}", a.as_of, "COLL-1/AR-1"),
    ]
    print(json.dumps({
        "skill": "revenue-intelligence", "currency": a.currency, "period": {"start": start_m, "end": end_m}, "as_of": a.as_of,
        "definitions": ["MRR-1", "ARR-1", "MOV-1", "GROWTH-1", "NRR-1", "GRR-1", "CHURN-L1", "CHURN-R1", "ARPA-1", "CONC-1", "RECUR-1", "COLL-1", "AR-1"],
        "exclusions": exclusions, "excluded_mrr_total": end_ex, "currency_normalisations": normalisations,
        "entity_map_applied": entity,
        "monthly": monthly, "growth": growth, "retention": retention, "concentration": concentration,
        "collections": collections, "customer_mrr": cmrr, "evidence": evidence,
    }, indent=2))


if __name__ == "__main__":
    main()
