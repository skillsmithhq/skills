#!/usr/bin/env python3
"""Measure receipt_ocr.py accuracy against hand-checked labels, and say whether the data supports a target.

Usage:
  python3 receipt_eval.py --pred results/ --truth labels/ [--target 0.9999]

labels/<stem>.json holds the true values, e.g. {"date": "2026-03-14", "currency": "INR", "total": "1180.00"}.
Only fields present in a label file are scored. Reports, per field:
  coverage            share of receipts where the field was auto-accepted
  accepted precision  share of accepted values that are correct (the number that matters for automation)
  95% lower bound     Wilson score lower bound on accepted precision
"""

import argparse
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


def norm(field, v):
    if v is None:
        return None
    s = str(v).strip()
    if field in {"subtotal", "tax", "tip", "discount", "total"}:
        try:
            return Decimal(s.replace(",", "")).normalize()
        except InvalidOperation:
            return s
    if field == "merchant":
        return re.sub(r"\s+", " ", s).casefold()
    return s.upper() if field == "currency" else s


def wilson_lower(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--target", type=float, default=0.9999)
    a = ap.parse_args()
    stats = {}
    receipts = 0
    for t in sorted(Path(a.truth).glob("*.json")):
        p = Path(a.pred) / t.name
        if not p.exists():
            print(f"missing prediction for {t.name}")
            continue
        receipts += 1
        truth = json.loads(t.read_text())
        page = json.loads(p.read_text())["pages"][0]
        for f, tv in truth.items():
            s = stats.setdefault(f, {"n": 0, "accepted": 0, "acc_ok": 0, "any_ok": 0})
            s["n"] += 1
            pf = page.get("fields", {}).get(f, {})
            ok = norm(f, pf.get("value")) == norm(f, tv)
            s["any_ok"] += ok
            if pf.get("status") == "accepted":
                s["accepted"] += 1
                s["acc_ok"] += ok
    print(f"{receipts} labelled receipts\n")
    print(f"{'field':10} {'coverage':>9} {'acc.prec':>9} {'95% low':>8} {'raw acc':>8}")
    tot_acc = tot_ok = 0
    for f, s in stats.items():
        cov = s["accepted"] / s["n"] if s["n"] else 0
        prec = s["acc_ok"] / s["accepted"] if s["accepted"] else float("nan")
        print(f"{f:10} {cov:9.2%} {prec:9.4%} {wilson_lower(s['acc_ok'], s['accepted']):8.4%} {s['any_ok'] / s['n']:8.2%}")
        tot_acc += s["accepted"]
        tot_ok += s["acc_ok"]
    low = wilson_lower(tot_ok, tot_acc)
    need = math.ceil(3 / (1 - a.target)) if a.target < 1 else None
    print(f"\nAll accepted fields: {tot_ok}/{tot_acc} correct, 95% lower bound {low:.4%}")
    if low >= a.target:
        print(f"Target {a.target:.4%} is supported by this sample.")
    else:
        print(f"Target {a.target:.4%} is NOT yet supported. With zero errors you need about {need} accepted fields "
              f"to show it at 95% confidence (rule of three); with errors, more.")


if __name__ == "__main__":
    main()
