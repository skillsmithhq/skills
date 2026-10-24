#!/usr/bin/env python3
"""Lint executive decision briefs (JSON) before they go into a report.

Each recommendation must have: audience, decision, evidence (IDs), business_impact, confidence {level, reason},
alternatives (including doing nothing), risks, dependencies, next_action, measurement.
Blocks: guarantee or promised-return language, investment advice (buy/sell/hold, price targets, valuations),
numbers in the impact text with no evidence ID, evidence IDs missing from the supplied evidence register,
and confidence levels above the supporting evidence (no CALC/FACT -> at most Low).

Usage: python3 decision_brief_lint.py briefs.json [--evidence artefact.json ...]
"""
import json
import re
import sys

REQUIRED = ["audience", "decision", "evidence", "business_impact", "confidence", "alternatives", "risks",
            "dependencies", "next_action", "measurement"]
AUDIENCES = {"CEO", "CTO", "CBO", "Investor"}
LEVELS = ["Insufficient", "Low", "Medium", "High", "Very high"]
PROMISE = re.compile(r"\b(guarantee[sd]?|will (increase|grow|double|deliver|return|save)|risk[- ]free|certain to|assured)\b", re.I)
ADVICE = re.compile(r"\b(buy|sell|hold) (the )?(shares|stock|equity|position)|\bprice target\b|\bvaluation of\b|\b(should|recommend) (invest(ing)?|buy(ing)?|sell(ing)?)\b", re.I)
NUMBER = re.compile(r"(?<![\w.-])\d[\d,]*(?:\.\d+)?%?(?![\w-])")


def lint(briefs, known_ids=None):
    issues = []
    for i, r in enumerate(briefs.get("recommendations", [])):
        rid = r.get("id", f"#{i}")
        for k in REQUIRED:
            if not r.get(k):
                issues.append({"id": rid, "severity": "major", "issue": f"missing {k}"})
        if r.get("audience") and r["audience"] not in AUDIENCES:
            issues.append({"id": rid, "severity": "major", "issue": f"unknown audience {r['audience']!r}"})
        conf = r.get("confidence") or {}
        if conf and (conf.get("level") not in LEVELS or not conf.get("reason")):
            issues.append({"id": rid, "severity": "major", "issue": "confidence needs a valid level and a reason"})
        classes = {e.get("class") for e in r.get("evidence", [])}
        if conf.get("level") in LEVELS and LEVELS.index(conf["level"]) > 1 and not classes & {"CALC", "FACT"}:
            issues.append({"id": rid, "severity": "critical", "issue": "confidence above Low without CALC or FACT evidence"})
        alts = " ".join(r.get("alternatives", [])).lower()
        if r.get("alternatives") and "nothing" not in alts and "status quo" not in alts and "defer" not in alts:
            issues.append({"id": rid, "severity": "minor", "issue": "alternatives should include doing nothing or deferring"})
        text = " ".join(str(r.get(k, "")) for k in ("decision", "business_impact", "next_action", "measurement"))
        for m in PROMISE.finditer(text):
            issues.append({"id": rid, "severity": "critical", "issue": f"promise language: {m.group(0)!r}"})
        for m in ADVICE.finditer(text):
            issues.append({"id": rid, "severity": "critical", "issue": f"investment advice: {m.group(0)!r}"})
        if NUMBER.search(str(r.get("business_impact", ""))) and not r.get("evidence"):
            issues.append({"id": rid, "severity": "major", "issue": "impact contains numbers but no evidence IDs"})
        if known_ids is not None:
            for e in r.get("evidence", []):
                if e.get("class") in ("CALC", "FACT") and e.get("id") not in known_ids:
                    issues.append({"id": rid, "severity": "critical", "issue": f"evidence {e.get('id')} not in the evidence register"})
    return issues


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    briefs = json.load(open(a[0]))
    known = None
    if "--evidence" in a:
        known = set()
        for path in a[a.index("--evidence") + 1:]:
            data = json.load(open(path))
            known |= {e["id"] for e in (data if isinstance(data, list) else data.get("evidence", []))}
    issues = lint(briefs, known)
    blocking = [x for x in issues if x["severity"] in ("critical", "major")]
    print(json.dumps({"issues": issues, "blocking": len(blocking)}, indent=2))
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
