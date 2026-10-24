#!/usr/bin/env python3
"""Rule-based data readiness assessment with a published scoring method.

Input: a JSON config describing tables and the checks that apply (see references/readiness-method.md
and the example config in the collection's fixtures). Output: JSON with check-level results,
dimension scores, weighted table scores, critical flags, readiness levels and suitability per analysis.

Scoring:
  check pass rate   = passing / applicable (checks with 0 applicable rows are skipped)
  dimension score   = mean pass rate of its checks x 100
  table score       = weighted mean of the dimensions that have checks (weights renormalised)
  level from score  = 5 if >= 95, 4 if >= 85, 3 if >= 70, 2 if >= 50, else 1
  critical flag     = primary key not unique, required field < 95% complete, or foreign key match < 90%
  major flag        = any other failing validity, uniqueness or coverage check
  final level       = min(level from score, 3) if any critical flag; min(level, 4) if any major flag
  Timestamps must fall in [2000-01-01, as_of + 1 day]; fields listed in "future_ok" may run 5 years ahead.

Usage: python3 assess_readiness.py config.json [--data-dir DIR]
"""
import csv
import datetime as dt
import json
import pathlib
import sys
from collections import Counter

WEIGHTS = {"completeness": 0.25, "validity": 0.20, "uniqueness": 0.20, "consistency": 0.10,
           "referential_integrity": 0.15, "timeliness_coverage": 0.10}
LEVELS = {5: "ready", 4: "minor issues", 3: "usable with caveats", 2: "major remediation needed", 1: "unusable"}
ISO_4217 = set("""AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD
CAD CDF CHF CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD
HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL
MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD
RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD
UYU UZS VES VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWL""".split())
MIN_TS = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)


def parse_ts(value):
    try:
        if len(value) == 10:
            return dt.datetime.fromisoformat(value).replace(tzinfo=dt.timezone.utc)
        ts = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return ts if ts.tzinfo else ts.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def load(data_dir, spec):
    with open(data_dir / spec["file"], newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def check(dimension, name, passing, applicable, field=None, detail=None):
    return {"dimension": dimension, "check": name, "field": field, "passing": passing, "applicable": applicable,
            "pass_rate": round(passing / applicable, 6) if applicable else None, "failing": applicable - passing,
            **({"detail": detail} if detail else {})}


def assess_table(name, spec, rows, tables, as_of):
    out = []
    n = len(rows)
    blank = lambda v: v is None or str(v).strip() == ""
    for f in spec.get("required", []):
        out.append(check("completeness", "required_present", sum(not blank(r.get(f)) for r in rows), n, f))
    for f in spec.get("currency_fields", []):
        vals = [r[f] for r in rows if not blank(r.get(f))]
        bad = sorted({v for v in vals if v not in ISO_4217})
        case_only = sorted({v for v in bad if v.strip().upper() in ISO_4217})
        out.append(check("validity", "iso_4217_currency", len(vals) - sum(v in bad for v in vals), len(vals), f,
                         {"invalid_values": bad, "normalisable_by_case": case_only}))
    for f in spec.get("numeric_nonneg", []):
        vals = [r[f] for r in rows if not blank(r.get(f))]
        def ok(v):
            try:
                return float(v) >= 0
            except ValueError:
                return False
        out.append(check("validity", "numeric_non_negative", sum(map(ok, vals)), len(vals), f))
    for f, allowed in spec.get("allowed_values", {}).items():
        vals = [r[f] for r in rows if not blank(r.get(f))]
        bad = sorted({v for v in vals if v not in allowed})
        out.append(check("validity", "allowed_values", len(vals) - sum(v in bad for v in vals), len(vals), f, {"invalid_values": bad}))
    for f in spec.get("date_fields", []) + spec.get("datetime_fields", []):
        vals = [r[f] for r in rows if not blank(r.get(f))]
        horizon = as_of + dt.timedelta(days=366 * 5 if f in spec.get("future_ok", []) else 1)
        upper = dt.datetime.combine(horizon, dt.time(), tzinfo=dt.timezone.utc)
        parsed = [parse_ts(v) for v in vals]
        good = sum(p is not None and MIN_TS <= p <= upper for p in parsed)
        out.append(check("validity", "parseable_plausible_timestamp", good, len(vals), f,
                         {"plausible_range": [MIN_TS.date().isoformat(), horizon.isoformat()]}))
    keyed = [("primary_key_unique", spec["primary_key"], rows)] if spec.get("primary_key") else []
    keyed += [("natural_key_unique", key, [r for r in rows if not any(blank(r.get(k)) for k in key)])
              for key in spec.get("natural_keys", [])]
    for check_name, key, subset in keyed:
        counts = Counter(tuple(r.get(k) for k in key) for r in subset)
        # passing = rows minus surplus duplicates (a key seen twice contributes one failure)
        out.append(check("uniqueness", check_name, len(counts), len(subset), "+".join(key),
                         {"duplicate_keys": sorted("+".join(k) for k, c in counts.items() if c > 1)}))
    if spec.get("check_exact_duplicates", True):
        seen, dups = set(), 0
        for r in rows:
            t = tuple(r.items())
            dups += t in seen
            seen.add(t)
        out.append(check("uniqueness", "no_exact_duplicate_rows", n - dups, n))
    for rule in spec.get("rules", []):
        if rule["type"] == "date_order":
            pairs = [(parse_ts(r[rule["start"]]), parse_ts(r[rule["end"]])) for r in rows
                     if not blank(r.get(rule["start"])) and not blank(r.get(rule["end"]))]
            pairs = [(a, b) for a, b in pairs if a and b]
            out.append(check("consistency", "date_order", sum(b >= a for a, b in pairs), len(pairs), f"{rule['start']}<={rule['end']}"))
        elif rule["type"] == "required_if":
            subset = [r for r in rows if r.get(rule["when_field"]) in rule["in"]]
            out.append(check("consistency", "required_if", sum(not blank(r.get(rule["field"])) for r in subset), len(subset),
                             rule["field"], {"when": f"{rule['when_field']} in {rule['in']}"}))
    for fk in spec.get("foreign_keys", []):
        ref = {r[fk["ref_field"]] for r in tables[fk["ref_table"]]}
        vals = [r[fk["field"]] for r in rows if not blank(r.get(fk["field"]))]
        missing = sorted({v for v in vals if v not in ref})
        out.append(check("referential_integrity", "foreign_key_match", len(vals) - sum(v in missing for v in vals), len(vals),
                         fk["field"], {"references": f"{fk['ref_table']}.{fk['ref_field']}", "unmatched_values": len(missing)}))
    cov = spec.get("coverage")
    if cov:
        days = sorted({p.date() for p in (parse_ts(r[cov["field"]]) for r in rows if not blank(r.get(cov["field"])))
                       if p and MIN_TS <= p <= dt.datetime.combine(as_of + dt.timedelta(days=1), dt.time(), tzinfo=dt.timezone.utc)})
        if days:
            span = (days[-1] - days[0]).days + 1
            present = set(days)
            gaps = [(days[0] + dt.timedelta(d)).isoformat() for d in range(span) if days[0] + dt.timedelta(d) not in present]
            out.append(check("timeliness_coverage", "daily_coverage", span - len(gaps), span, cov["field"],
                             {"first": days[0].isoformat(), "last": days[-1].isoformat(), "missing_days": gaps}))
            if "max_age_days" in cov:
                age = (as_of - days[-1]).days
                out.append(check("timeliness_coverage", "freshness", int(age <= cov["max_age_days"]), 1, cov["field"],
                                 {"days_since_last": age, "max_age_days": cov["max_age_days"]}))
    return out


def score(checks):
    dims = {}
    for c in checks:
        if c["pass_rate"] is not None:
            dims.setdefault(c["dimension"], []).append(c["pass_rate"])
    dim_scores = {d: round(100 * sum(v) / len(v), 2) for d, v in dims.items()}
    wsum = sum(WEIGHTS[d] for d in dim_scores)
    total = round(sum(WEIGHTS[d] * 100 * sum(dims[d]) / len(dims[d]) for d in dims) / wsum, 2) if wsum else None
    return dim_scores, total


def level_for(score_value):
    if score_value is None:
        return 1
    for threshold, lvl in ((95, 5), (85, 4), (70, 3), (50, 2)):
        if score_value >= threshold:
            return lvl
    return 1


def flags_for(checks):
    flags = []
    for c in checks:
        if c["pass_rate"] is None:
            continue
        if c["check"] == "primary_key_unique" and c["pass_rate"] < 1:
            flags.append({"severity": "critical", "field": c["field"], "reason": "primary key not unique"})
        elif c["check"] == "required_present" and c["pass_rate"] < 0.95:
            flags.append({"severity": "critical", "field": c["field"], "reason": f"required field {100 * c['pass_rate']:.2f}% complete (< 95%)"})
        elif c["check"] == "foreign_key_match" and c["pass_rate"] < 0.90:
            flags.append({"severity": "critical", "field": c["field"], "reason": f"foreign key match {100 * c['pass_rate']:.2f}% (< 90%)"})
        elif c["pass_rate"] < 1:
            flags.append({"severity": "major" if c["dimension"] in ("validity", "uniqueness", "timeliness_coverage") else "minor",
                          "field": c["field"], "reason": f"{c['check']}: {c['failing']} of {c['applicable']} failing"})
    return flags


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: assess_readiness.py config.json [--data-dir DIR]")
    cfg_path = pathlib.Path(args[0])
    cfg = json.loads(cfg_path.read_text())
    data_dir = pathlib.Path(args[args.index("--data-dir") + 1]) if "--data-dir" in args else (cfg_path.parent / cfg.get("data_dir", "."))
    as_of = dt.date.fromisoformat(cfg["as_of"])
    tables = {name: load(data_dir, spec) for name, spec in cfg["tables"].items()}
    results = {}
    for name, spec in cfg["tables"].items():
        checks = assess_table(name, spec, tables[name], tables, as_of)
        dims, total = score(checks)
        flags = flags_for(checks)
        lvl = level_for(total)
        final = lvl
        if any(f["severity"] == "critical" for f in flags):
            final = min(final, 3)
        elif any(f["severity"] == "major" for f in flags):
            final = min(final, 4)
        results[name] = {"rows": len(tables[name]), "dimension_scores": dims, "score": total, "level_from_score": lvl,
                         "level": final, "level_label": LEVELS[final], "flags": flags, "checks": checks}
    suitability = {}
    for analysis, spec in cfg.get("analyses", {}).items():
        lvl, blockers, caveats = 5, [], []
        for table, fields in spec["requires"].items():
            lvl = min(lvl, results[table]["level"])
            for f in results[table]["flags"]:
                touches = f["field"] is None or any(x in f["field"] for x in fields)
                if touches and f["severity"] == "critical":
                    blockers.append(f"{table}.{f['field']}: {f['reason']}")
                elif touches and f["severity"] == "major":
                    caveats.append(f"{table}.{f['field'] or '(row)'}: {f['reason']}")
        suitability[analysis] = {"level": lvl, "label": LEVELS[lvl], "blocking_issues": blockers, "caveats": caveats}
    print(json.dumps({"as_of": cfg["as_of"], "method": {"weights": WEIGHTS, "levels": LEVELS,
                      "critical_rules": ["primary key not unique", "required field < 95% complete", "foreign key match < 90%"],
                      "critical_effect": "final level capped at 3", "major_effect": "final level capped at 4"},
                      "tables": results, "suitability": suitability,
                      "evidence": [{"id": f"dq-{name.replace('_', '-')}", "class": "CALC", "produced_by": "data-readiness-assessment",
                                    "statement": f"{name}: score {r['score']}, level {r['level']} ({r['level_label']}); "
                                                 f"{sum(f['severity'] == 'critical' for f in r['flags'])} critical flag(s)"}
                                   for name, r in results.items()]}, indent=2))


if __name__ == "__main__":
    main()
