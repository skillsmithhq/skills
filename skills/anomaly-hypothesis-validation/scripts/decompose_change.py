#!/usr/bin/env python3
"""Decompose the change in a total between two periods by one or more dimensions.

Used to test explanations: if a hypothesis says "the increase came from X", the decomposition shows how much
of the change sits in X. Contribution share = change in group / change in total (it can exceed 100% when other
groups moved the opposite way).

Usage: python3 decompose_change.py DATA.csv --period-col month --value-col cost --dims environment[,service]
                                   --base 2026-04 --target 2026-05
"""
import argparse
import csv
import json
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--period-col", required=True)
    ap.add_argument("--value-col", required=True)
    ap.add_argument("--dims", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--target", required=True)
    a = ap.parse_args()
    dims = a.dims.split(",")
    with open(a.data, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    totals = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        idx = {a.base: 0, a.target: 1}.get(r[a.period_col])
        if idx is not None:
            totals[" / ".join(r[d] for d in dims)][idx] += float(r[a.value_col])
    base_total = sum(v[0] for v in totals.values())
    target_total = sum(v[1] for v in totals.values())
    change = target_total - base_total
    groups = sorted(({"group": g, "base": b, "target": t, "change": t - b,
                      "share_of_change_pct": round(100 * (t - b) / change, 2) if change else None}
                     for g, (b, t) in totals.items()), key=lambda x: -abs(x["change"]))
    print(json.dumps({"dims": dims, "base": a.base, "target": a.target, "base_total": base_total,
                      "target_total": target_total, "change": change, "groups": groups}, indent=2))


if __name__ == "__main__":
    main()
