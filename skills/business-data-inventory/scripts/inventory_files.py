#!/usr/bin/env python3
"""Profile a folder of data files into a structural inventory, without printing data values.

Supports: .csv, .tsv, .json (array of objects), .jsonl, .xlsx (first sheet, standard library reader),
          .sql (CREATE TABLE statements only; schema, no data).
For each dataset: row count, columns, inferred type, null count, distinct count, candidate keys,
possible personal-data columns (by name or value shape; values are never printed),
exact duplicate rows, and identifier columns that contain duplicates.
Across datasets: columns that share a name (their meaning must be confirmed, not assumed) and
candidate join keys (columns ending in _id or containing 'account').

Usage: python3 inventory_files.py <folder> [--max-rows N]
"""
import csv
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE = re.compile(r"^\+?[\d\s().-]{8,}$")
PII_NAMES = re.compile(r"(email|e_mail|phone|mobile|first_name|last_name|full_name|address|postcode|zip|dob|birth|ssn|passport|national_id|ip_address)", re.I)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")
INT = re.compile(r"^-?\d+$")
DEC = re.compile(r"^-?\d+\.\d+$")
ID_NAME = re.compile(r"(^id$|_id$|_key$|_code$|_number$)", re.I)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_csv(path, delim=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=delim))


def read_json(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    return [r for r in data if isinstance(r, dict)]


def read_xlsx(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        sheets = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))
        root = ET.fromstring(z.read(sheets[0]))
    grid = []
    for row in root.iter(f"{{{NS['m']}}}row"):
        values = {}
        for c in row.findall("m:c", NS):
            col = re.match(r"[A-Z]+", c.get("r")).group(0)
            t = c.get("t")
            if t == "inlineStr":
                v = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
            else:
                node = c.find("m:v", NS)
                v = "" if node is None else node.text
                if t == "s":
                    v = shared[int(v)]
            values[col] = v
        grid.append(values)
    if not grid:
        return []
    cols = sorted(grid[0], key=lambda s: (len(s), s))
    header = [grid[0][c] for c in cols]
    return [{h: r.get(c, "") for h, c in zip(header, cols)} for r in grid[1:]]


def read_sql(path):
    tables = {}
    for m in re.finditer(r"CREATE\s+TABLE\s+([\w.\"]+)\s*\((.*?)\);", path.read_text(), re.S | re.I):
        cols = []
        for line in m.group(2).split(",\n"):
            parts = line.strip().split()
            if parts and parts[0].upper() not in ("PRIMARY", "FOREIGN", "CONSTRAINT", "UNIQUE"):
                cols.append({"name": parts[0].strip('"'), "declared_type": " ".join(parts[1:2]),
                             "primary_key": "PRIMARY KEY" in line.upper()})
        tables[m.group(1).strip('"')] = cols
    return tables


def infer(values):
    present = [v for v in values if v not in ("", None)]
    if not present:
        return "empty"
    kinds = set()
    for v in present:
        s = str(v).strip()
        if isinstance(v, bool) or s.lower() in ("true", "false"):
            kinds.add("boolean")
        elif INT.match(s):
            kinds.add("integer")
        elif DEC.match(s):
            kinds.add("decimal")
        elif DATE.match(s):
            kinds.add("date")
        elif DATETIME.match(s):
            kinds.add("datetime")
        else:
            kinds.add("text")
    if kinds <= {"integer", "decimal"} and "decimal" in kinds:
        return "decimal"
    return kinds.pop() if len(kinds) == 1 else "mixed(" + ",".join(sorted(kinds)) + ")"


def profile(rows):
    columns = list(rows[0].keys()) if rows else []
    out = []
    for col in columns:
        values = [r.get(col) for r in rows]
        present = [str(v) for v in values if v not in ("", None)]
        unique = bool(rows) and len(present) == len(rows) and len(set(present)) == len(rows)
        pii = []
        if PII_NAMES.search(col):
            pii.append("column-name")
        if present and sum(bool(EMAIL.match(v)) for v in present) / len(present) > 0.5:
            pii.append("email-shaped-values")
        if present and infer(values) == "text" and sum(bool(PHONE.match(v)) for v in present) / len(present) > 0.5:
            pii.append("phone-shaped-values")
        out.append({
            "name": col, "inferred_type": infer(values), "null_count": len(values) - len(present),
            "distinct_count": len(set(present)),
            "unique_non_null": unique,
            "candidate_key": unique and bool(ID_NAME.search(col)),
            "id_like_with_duplicates": bool(ID_NAME.search(col)) and len(set(present)) < len(present),
            "possible_personal_data": pii,
        })
    return out


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: inventory_files.py <folder> [--max-rows N]")
    folder = pathlib.Path(args[0])
    max_rows = int(args[args.index("--max-rows") + 1]) if "--max-rows" in args else None
    datasets, schemas, skipped = [], [], []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = str(path.relative_to(folder))
        try:
            if path.suffix in (".csv", ".tsv"):
                rows = read_csv(path, "\t" if path.suffix == ".tsv" else ",")
            elif path.suffix in (".json", ".jsonl"):
                rows = read_json(path)
            elif path.suffix == ".xlsx":
                rows = read_xlsx(path)
            elif path.suffix == ".sql":
                for table, cols in read_sql(path).items():
                    schemas.append({"source": rel, "table": table, "columns": cols})
                continue
            else:
                skipped.append({"file": rel, "reason": "unsupported format"})
                continue
        except Exception as e:  # report and continue: one bad file must not stop the inventory
            skipped.append({"file": rel, "reason": f"could not parse: {type(e).__name__}"})
            continue
        if max_rows:
            rows = rows[:max_rows]
        cols = profile(rows)
        datasets.append({"file": rel, "format": path.suffix.lstrip("."), "row_count": len(rows), "columns": cols,
                         "exact_duplicate_rows": len(rows) - len({tuple(sorted(r.items())) for r in rows}),
                         "id_columns_with_duplicates": [c["name"] for c in cols if c["id_like_with_duplicates"]]})

    by_name = {}
    for d in datasets:
        for c in d["columns"]:
            by_name.setdefault(c["name"], []).append(d["file"])
    shared = {k: v for k, v in sorted(by_name.items()) if len(v) > 1}
    join_candidates = {k: v for k, v in shared.items() if k.endswith("_id") or "account" in k}
    print(json.dumps({
        "folder": str(folder), "datasets": datasets, "schema_only_tables": schemas, "skipped": skipped,
        "shared_column_names": shared,
        "candidate_join_columns": join_candidates,
        "notes": ["Shared column names are not proof of shared meaning: confirm each with the data owner.",
                  "Values are not printed. possible_personal_data flags are heuristics; review them."],
    }, indent=2))


if __name__ == "__main__":
    main()
