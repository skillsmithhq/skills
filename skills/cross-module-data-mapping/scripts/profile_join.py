#!/usr/bin/env python3
"""Profile a candidate join between two CSV datasets before anyone relies on it.

Reports row and key counts, duplicate keys on each side, match rates (by rows and by distinct keys),
observed cardinality on matched keys, fan-out (rows a join would produce), unmatched keys, and
normalisation collisions (several raw values that become one key, which a human must review).

Normalisers (--normalise):
  none          exact match
  upper_trim    trim whitespace, upper-case
  alnum_upper   remove non-alphanumerics, upper-case       ("c-003" -> "C003")
  digits:P:W    keep digits only, as integer, re-format as prefix P plus zero-padded width W
                ("CUST-0009" with digits:C:3 -> "C009"). Aggressive: review the collisions.
--entity-map CSV with columns raw_id,entity_id,reason maps keys to resolved entities after normalising,
on both sides. Left rows that then share an entity are collapsed and counted as left_collapsed_rows.

Usage: python3 profile_join.py LEFT.csv LEFT_KEY RIGHT.csv RIGHT_KEY [--normalise N] [--entity-map MAP.csv]
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict


def normaliser(spec):
    if spec in (None, "none"):
        return lambda v: v
    if spec == "upper_trim":
        return lambda v: v.strip().upper()
    if spec == "alnum_upper":
        return lambda v: re.sub(r"[^0-9A-Za-z]", "", v).upper()
    m = re.fullmatch(r"digits:([A-Za-z]*):(\d+)", spec)
    if m:
        prefix, width = m.group(1), int(m.group(2))
        def f(v):
            digits = re.sub(r"\D", "", v)
            return f"{prefix}{int(digits):0{width}d}" if digits else v
        return f
    raise SystemExit(f"unknown normaliser {spec!r}")


def keys(path, column):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if rows and column not in rows[0]:
        raise SystemExit(f"{path}: no column {column!r}")
    return [r[column] for r in rows if (r.get(column) or "").strip()], len(rows)


def main():
    a = sys.argv[1:]
    if len(a) < 4:
        sys.exit(__doc__)
    left_path, left_key, right_path, right_key = a[:4]
    norm_spec = a[a.index("--normalise") + 1] if "--normalise" in a else "none"
    norm = normaliser(norm_spec)
    emap, reasons = {}, {}
    if "--entity-map" in a:
        with open(a[a.index("--entity-map") + 1], newline="") as fh:
            for r in csv.DictReader(fh):
                emap[norm(r["raw_id"])] = norm(r["entity_id"])
                reasons[r["raw_id"]] = r.get("reason", "")
    resolve = lambda v: emap.get(norm(v), norm(v))

    left_raw, left_rows = keys(left_path, left_key)
    right_raw, right_rows = keys(right_path, right_key)
    raw_by_norm = defaultdict(set)
    for v in left_raw + right_raw:
        raw_by_norm[resolve(v)].add(v)
    left_raw_counts = Counter(norm(v) for v in left_raw)
    groups = defaultdict(list)  # resolved entity -> normalised raw keys merged into it
    for raw in left_raw_counts:
        groups[emap.get(raw, raw)].append(raw)
    # An entity's left count is the largest count among its raw keys: keys merged by the entity map
    # collapse to one row, while genuine duplicates of a single raw key stay visible.
    left_counts = Counter({e: max(left_raw_counts[r] for r in rs) for e, rs in groups.items()})
    collapsed = sum(left_raw_counts.values()) - sum(left_counts.values()) if emap else 0
    right_counts = Counter(resolve(v) for v in right_raw)
    matched = set(left_counts) & set(right_counts)
    right_rows_matched = sum(right_counts[k] for k in matched)
    left_max = max((left_counts[k] for k in matched), default=0)
    right_max = max((right_counts[k] for k in matched), default=0)
    cardinality = {(1, 1): "1:1", (1, 2): "1:N", (2, 1): "N:1", (2, 2): "N:M"}.get((min(left_max, 2), min(right_max, 2)), "none")
    collisions = {k: sorted(v) for k, v in sorted(raw_by_norm.items()) if len(v) > 1}
    out = {
        "left": {"file": left_path, "key": left_key, "rows": left_rows, "blank_keys": left_rows - len(left_raw),
                 "distinct_keys": len(left_counts), "duplicate_keys": sorted(k for k, c in left_counts.items() if c > 1),
                 "left_collapsed_rows": collapsed},
        "right": {"file": right_path, "key": right_key, "rows": right_rows, "blank_keys": right_rows - len(right_raw),
                  "distinct_keys": len(right_counts), "duplicate_keys_count": sum(c > 1 for c in right_counts.values())},
        "normaliser": norm_spec, "entity_map_entries": len(emap),
        "match": {
            "right_rows_matched": right_rows_matched,
            "right_row_match_rate": round(right_rows_matched / len(right_raw), 4) if right_raw else None,
            "left_keys_with_match": len(matched),
            "left_key_match_rate": round(len(matched) / len(left_counts), 4) if left_counts else None,
            "unmatched_right_keys": sorted(set(right_counts) - matched),
            "unmatched_left_keys_count": len(set(left_counts) - matched),
        },
        "cardinality_on_matched_keys": cardinality,
        "fan_out_rows_if_joined": sum(left_counts[k] * right_counts[k] for k in matched),
        "normalisation_collisions": collisions,
        "warnings": [],
    }
    if out["left"]["duplicate_keys"]:
        out["warnings"].append("Left key is not unique: a join can multiply rows for those keys. Resolve entities first.")
    if collisions and norm_spec != "none":
        out["warnings"].append("Several raw values map to one key: confirm each group is the same entity before relying on the join.")
    if out["match"]["right_row_match_rate"] is not None and out["match"]["right_row_match_rate"] < 0.9:
        out["warnings"].append("Under 90% of right rows match: results based on this join will be incomplete.")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
