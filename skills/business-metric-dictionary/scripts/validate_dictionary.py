#!/usr/bin/env python3
"""Validate a client metric dictionary (JSON) for completeness and internal consistency.

Checks every metric for the required attributes, a known definition ID (from
references/saas-metric-definitions.md, or marked "custom"), approval details when approved,
a reason when not calculable, unique IDs, and, if an inventory JSON from
business-data-inventory is supplied, that every required field exists in the data.

Usage: python3 validate_dictionary.py dictionary.json [--inventory inventory.json]
"""
import json
import pathlib
import re
import sys

REQUIRED = ["id", "name", "definition_id", "business_definition", "formula", "source_systems", "required_fields",
            "grain", "time_period", "inclusions", "exclusions", "currency_handling", "timezone_handling",
            "known_limitations", "business_owner", "use_cases", "status"]
STATUSES = {"draft", "approved", "not-calculable", "deprecated"}
DEFS = pathlib.Path(__file__).resolve().parent.parent / "references" / "saas-metric-definitions.md"


def known_definition_ids():
    if not DEFS.exists():
        return set()
    return set(re.findall(r"^\| ([A-Z]+(?:-[A-Z]+)?-?\d+) \|", DEFS.read_text(), re.M))


def validate(dictionary, inventory=None):
    errors, warnings = [], []
    known = known_definition_ids()
    fields = None
    if inventory:
        fields = {f"{pathlib.Path(d['file']).stem}.{c['name']}" for d in inventory["datasets"] for c in d["columns"]}
    seen = set()
    for i, m in enumerate(dictionary.get("metrics", [])):
        mid = m.get("id", f"#{i}")
        for key in REQUIRED:
            if key not in m or m[key] in ("", None) or (isinstance(m[key], list) and not m[key] and key not in ("exclusions", "inclusions")):
                errors.append(f"{mid}: missing or empty '{key}'")
        if mid in seen:
            errors.append(f"{mid}: duplicate id")
        seen.add(mid)
        status = m.get("status")
        if status not in STATUSES:
            errors.append(f"{mid}: status must be one of {sorted(STATUSES)}")
        if status == "approved" and not (m.get("approved_by") and m.get("approved_on")):
            errors.append(f"{mid}: approved metrics need approved_by (role) and approved_on")
        if status == "not-calculable" and not m.get("not_calculable_reason"):
            errors.append(f"{mid}: not-calculable metrics need not_calculable_reason")
        did = m.get("definition_id", "")
        if did != "custom" and known and did not in known:
            errors.append(f"{mid}: definition_id {did!r} is not in saas-metric-definitions.md (use 'custom' and define it fully)")
        if did == "custom" and len(m.get("formula", "")) < 10:
            errors.append(f"{mid}: custom definitions need an explicit formula")
        if fields is not None and status != "not-calculable":
            for f in m.get("required_fields", []):
                if f not in fields:
                    errors.append(f"{mid}: required field {f} not found in the inventory")
        if status == "draft":
            warnings.append(f"{mid}: still draft. Results using it must be labelled 'definition not yet approved'")
    return errors, warnings


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: validate_dictionary.py dictionary.json [--inventory inventory.json]")
    inv = json.load(open(args[args.index("--inventory") + 1])) if "--inventory" in args else None
    errs, warns = validate(json.load(open(args[0])), inv)
    print(json.dumps({"valid": not errs, "errors": errs, "warnings": warns}, indent=2))
    sys.exit(1 if errs else 0)
