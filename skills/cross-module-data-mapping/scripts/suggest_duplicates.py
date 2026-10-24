#!/usr/bin/env python3
"""Suggest candidate duplicate entities in one table, for human confirmation.

Evidence types:
  shared_key   two rows share a value in a column that should identify one entity (for example a CRM account ID)
  similar_name normalised names (case, punctuation and legal suffixes removed) have a similarity ratio >= threshold
A suggestion is not a merge. Confirm each with the data owner and record it in an entity map
(raw_id,entity_id,reason), which profile_join.py and the analysis scripts accept.

Usage: python3 suggest_duplicates.py TABLE.csv ID_COLUMN --name-column COL [--shared-key COL ...] [--threshold 0.9]
"""
import csv
import difflib
import itertools
import json
import re
import sys

SUFFIXES = r"\b(ltd|limited|inc|incorporated|llc|plc|gmbh|pty|co|corp|corporation|company|group|bv|sa|ag)\b"


def norm_name(name):
    n = re.sub(r"[^\w\s]", " ", name.lower())
    n = re.sub(SUFFIXES, " ", n)
    return re.sub(r"\s+", " ", n).strip()


def main():
    a = sys.argv[1:]
    if len(a) < 2 or "--name-column" not in a:
        sys.exit(__doc__)
    path, id_col = a[0], a[1]
    name_col = a[a.index("--name-column") + 1]
    shared = [a[i + 1] for i, x in enumerate(a) if x == "--shared-key"]
    threshold = float(a[a.index("--threshold") + 1]) if "--threshold" in a else 0.9
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    pairs = {}
    for r1, r2 in itertools.combinations(rows, 2):
        evidence = []
        for col in shared:
            if r1.get(col) and r1.get(col) == r2.get(col):
                evidence.append({"type": "shared_key", "column": col})
        ratio = difflib.SequenceMatcher(None, norm_name(r1[name_col]), norm_name(r2[name_col])).ratio()
        if ratio >= threshold:
            evidence.append({"type": "similar_name", "ratio": round(ratio, 3)})
        if evidence:
            pairs[(r1[id_col], r2[id_col])] = {"ids": [r1[id_col], r2[id_col]], "names": [r1[name_col], r2[name_col]],
                                                "evidence": evidence,
                                                "strength": "strong" if len(evidence) > 1 else "weak"}
    print(json.dumps({"table": path, "candidates": list(pairs.values()),
                      "note": "Suggestions only. A merge needs owner confirmation and an entity-map entry with a reason."}, indent=2))


if __name__ == "__main__":
    main()
