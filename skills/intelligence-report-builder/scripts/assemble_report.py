#!/usr/bin/env python3
"""Assemble an intelligence report from a report spec and upstream skill outputs, with traceability enforced.

The analyst (or agent) writes the narrative in the spec. This script:
  - collects the evidence register from every artefact listed in the spec (their "evidence" arrays) plus
    spec.extra_evidence (FACT / INTERP / HYP / ASSUME items with sources)
  - refuses to build if any [CLASS:id] tag in the narrative does not resolve to the register
  - renders the 13 required sections in order, a BIDIM table from the bidim artefact, and Appendix A (evidence)
  - writes report.md, evidence_register.json and claims.json (spec.claims: the numeric claims, for the audit)
Status is always "DRAFT – not audited". Only a human sets approval.

Usage: python3 assemble_report.py spec.json --out OUTPUT_DIR
"""
import json
import pathlib
import re
import sys

SECTIONS = ["Executive summary", "Business context", "Data sources", "Methodology", "Metric definitions", "Key findings",
            "Cross-module insights", "Opportunities", "Risks", "Recommendations", "BIDIM prioritisation", "Limitations",
            "Next steps"]
REPORT_TYPES = {"BI Opportunity Assessment", "Executive Intelligence Report", "Revenue Intelligence Report",
                "Customer Intelligence Report", "Product Intelligence Report", "Technology Intelligence Report",
                "AI and Analytics Roadmap"}
TAG = re.compile(r"\[(CALC|FACT|PATTERN|HYP|INTERP|REC|ASSUME|UNKNOWN):([^\]]+)\]")


def tags(text):
    for cls, ids in TAG.findall(text):
        for i in re.split(r"[;,]\s*", ids):
            yield cls, i.strip()


def render_finding(f):
    lines = [f"### {f['id']} {f['title']}"]
    for key, label in (("what", "What we found"), ("why", "Why it matters"), ("decision", "Decision it informs"),
                       ("actions", "Possible actions"), ("impact", "Expected impact"), ("confidence", "Confidence"),
                       ("missing", "Missing information")):
        if f.get(key):
            lines.append(f"- **{label}:** {f[key]}")
    return "\n".join(lines)


def section_body(name, spec, bidim):
    body = spec["sections"].get(name)
    if name == "Key findings":
        return "\n\n".join(render_finding(f) for f in spec.get("findings", [])) or body or "No findings."
    if name == "BIDIM prioritisation":
        if not bidim:
            return body or "Not in scope for this report."
        rows = ["Prioritisation heuristic, not a valuation. Formula: (I × C × S) / (E × R).", "",
                "| Rank | ID | Opportunity | I | C | S | E | R | D | T | Priority | Labels | Evidence |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in bidim["ranking"]:
            s = r["scores_used"]
            pr = f"{r['priority']:.2f}" if r["priority"] is not None else f"range {r['priority_range'][0]:.2f}–{r['priority_range'][1]:.2f}"
            cell = lambda k: "–" if s[k] is None else str(s[k])
            rows.append(f"| {r['rank']} | {r['id']} | {r['title']} | " + " | ".join(cell(k) for k in
                        ("impact", "confidence", "strategic_fit", "effort", "risk", "data_readiness", "time_to_value")) +
                        f" | {pr} | {', '.join(r['labels'])} | [CALC:bidim-{r['id'].lower()}] |")
        return (body + "\n\n" if body else "") + "\n".join(rows)
    return body or "Not in scope for this report."


def main():
    a = sys.argv[1:]
    if len(a) != 3 or a[1] != "--out":
        sys.exit(__doc__)
    spec_path = pathlib.Path(a[0])
    spec = json.loads(spec_path.read_text())
    out = pathlib.Path(a[2])
    out.mkdir(parents=True, exist_ok=True)
    if spec["report_type"] not in REPORT_TYPES:
        sys.exit(f"unknown report_type; use one of {sorted(REPORT_TYPES)}")
    register, bidim = {}, None
    for name, rel in spec["artefacts"].items():
        data = json.loads((spec_path.parent / rel).read_text())
        if data.get("skill") == "bidim-opportunity-scoring":
            bidim = data
        for e in data.get("evidence", []):
            register[e["id"]] = {**e, "artefact": name}
    for e in spec.get("extra_evidence", []):
        if not e.get("source"):
            sys.exit(f"extra evidence {e['id']} needs a source")
        register[e["id"]] = {**e, "artefact": "spec"}

    parts = [f"# {spec['report_type']}: {spec['client']}", "",
             f"Status: DRAFT – not audited | Audience: {spec['audience']} | Period: {spec['period']} | Prepared: {spec['prepared']}", ""]
    for n, name in enumerate(SECTIONS, 1):
        parts += [f"## {n}. {name}", "", section_body(name, spec, bidim), ""]
    parts += ["## Appendix A: Evidence register", "", "| ID | Class | Statement | Produced by |", "|---|---|---|---|"]
    text = "\n".join(parts)
    used = sorted({i for _, i in tags(text)})
    for i in used:
        if i in register:
            e = register[i]
            parts.append(f"| {i} | {e['class']} | {e.get('statement', '').replace('|', '/')} | {e.get('produced_by', e.get('artefact'))} |")
    report = "\n".join(parts) + "\n"

    unresolved = sorted({i for cls, i in tags(report) if i not in register})
    mismatched = sorted({f"{cls}:{i}" for cls, i in tags(report) if i in register and register[i]["class"] != cls})
    if unresolved or mismatched:
        sys.exit(json.dumps({"error": "traceability failure", "unresolved_ids": unresolved, "class_mismatch": mismatched}, indent=2))
    (out / "report.md").write_text(report)
    (out / "evidence_register.json").write_text(json.dumps([register[i] for i in used], indent=2))
    (out / "claims.json").write_text(json.dumps(spec.get("claims", []), indent=2))
    print(json.dumps({"report": str(out / "report.md"), "sections": len(SECTIONS), "findings": len(spec.get("findings", [])),
                      "evidence_items_cited": len(used), "claims": len(spec.get("claims", []))}, indent=2))


if __name__ == "__main__":
    main()
