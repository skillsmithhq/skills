#!/usr/bin/env python3
"""Flag unusual points in a time series with a robust, documented method.

Method:
  baseline   = all points, or the periods between --baseline-from and --baseline-to (inclusive)
  robust z   = (x - median) / (1.4826 x MAD), where MAD is the median absolute deviation of the baseline
  flag       = |robust z| > --threshold (default 3.5)
  fallback   = if MAD is 0, flag points deviating from the median by more than --fallback-pct (default 50%)
  material   = |x - median| >= --materiality (optional; absolute units). Statistical and commercial
               significance are reported separately.
A flag means "unusual relative to this baseline", not "wrong" and not "important".

Input: CSV with period and value columns, or a JSON file plus --path to a list (for example the
product-intelligence output with --path weekly_events, or operational output with --path monthly
--period-key month --value-key total).

Usage: python3 detect_anomalies.py SERIES.(csv|json) [--path KEY] [--period-key period] [--value-key value]
         [--baseline-from P --baseline-to P] [--threshold 3.5] [--fallback-pct 50] [--materiality N]
         [--from P --to P] [--evidence-prefix anom-infra]
"""
import argparse
import csv
import json
import statistics


def load(a):
    if a.series.endswith(".json"):
        data = json.load(open(a.series))
        for key in (a.path or "").split(".") if a.path else []:
            data = data[key]
    else:
        with open(a.series, newline="", encoding="utf-8-sig") as f:
            data = list(csv.DictReader(f))
    points = [{"period": str(r[a.period_key]), "value": float(r[a.value_key])} for r in data]
    return [p for p in sorted(points, key=lambda p: p["period"])
            if (not a.from_ or p["period"] >= a.from_) and (not a.to or p["period"] <= a.to)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("series")
    ap.add_argument("--path")
    ap.add_argument("--period-key", default="period")
    ap.add_argument("--value-key", default="value")
    ap.add_argument("--baseline-from")
    ap.add_argument("--baseline-to")
    ap.add_argument("--threshold", type=float, default=3.5)
    ap.add_argument("--fallback-pct", type=float, default=50.0)
    ap.add_argument("--materiality", type=float)
    ap.add_argument("--from", dest="from_")
    ap.add_argument("--to")
    ap.add_argument("--evidence-prefix", help="emit a CALC evidence item <prefix>-<period> for each flagged point")
    a = ap.parse_args()
    pts = load(a)
    base = [p["value"] for p in pts
            if (not a.baseline_from or p["period"] >= a.baseline_from) and (not a.baseline_to or p["period"] <= a.baseline_to)]
    if len(base) < 3:
        raise SystemExit("baseline needs at least 3 points")
    med = statistics.median(base)
    mad = statistics.median(abs(v - med) for v in base)
    scale = 1.4826 * mad
    method = "robust_z" if mad > 0 else "pct_from_median_fallback"
    out = []
    for p in pts:
        dev = p["value"] - med
        row = {"period": p["period"], "value": p["value"], "deviation": dev,
               "pct_from_median": round(100 * dev / med, 2) if med else None}
        if mad > 0:
            row["robust_z"] = round(dev / scale, 2)
            row["flagged"] = abs(dev / scale) > a.threshold
        else:
            row["robust_z"] = None
            row["flagged"] = med != 0 and abs(100 * dev / med) > a.fallback_pct
        if a.materiality is not None:
            row["material"] = abs(dev) >= a.materiality
        out.append(row)
    warnings = []
    if len(base) < 12:
        warnings.append(f"small baseline (n={len(base)}): treat flags as prompts for investigation, not findings")
    if mad == 0:
        warnings.append("MAD is 0 (most baseline values identical): percentage fallback used")
    print(json.dumps({
        "method": {"name": method, "threshold": a.threshold, "fallback_pct": a.fallback_pct, "materiality": a.materiality,
                   "baseline": {"from": a.baseline_from or pts[0]["period"], "to": a.baseline_to or pts[-1]["period"], "n": len(base)}},
        "baseline_stats": {"median": med, "mad": mad, "scaled_mad": round(scale, 2)},
        "points": out, "flagged": [r["period"] for r in out if r["flagged"]], "warnings": warnings,
        "evidence": [{"id": f"{a.evidence_prefix}-{r['period']}", "class": "CALC", "produced_by": "anomaly-hypothesis-validation",
                      "statement": f"{r['period']} value {r['value']:g} vs baseline median {med:g} ({method}, "
                                   f"z={r['robust_z']}); flagged; baseline n={len(base)}"}
                     for r in out if r["flagged"]] if a.evidence_prefix else [],
    }, indent=2))


if __name__ == "__main__":
    main()
