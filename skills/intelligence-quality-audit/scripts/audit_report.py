#!/usr/bin/env python3
"""Independent quality audit of an intelligence report. Designed to challenge, not to approve.

Checks:
  sections      the 13 required sections are present                                    (major)
  traceability  every [CLASS:id] tag resolves to an artefact or the evidence register     (critical)
  claims        each claims.json entry recomputed from the named artefact path            (critical on mismatch)
  independent   key metrics re-read from the TEXT (not from claims.json) and recomputed:
                NRR, GRR (company or segment scope), MRR growth, logo churn, collection rate,
                customer counts                                                            (critical on mismatch)
  uncited       sentences or table rows containing numbers with no evidence tag           (major)
  causal        causal wording (drives, caused, because, due to, leads to...)             (major)
  privacy       email addresses, phone numbers, credential-like strings                   (critical)
  bidim         priority recomputed from the row's own inputs, and against the BIDIM artefact (critical)
  calculability gross margin, CAC or LTV stated with a number                             (major)
  caveats       NRR/GRR without a window label; activation without a sample size;
                confidence without a reason                                                (minor)
  status        a report claiming approval it cannot grant itself                         (major)
  contradiction the same metric stated with different values                              (major)
Causal flags are deliberately strict (a noun such as 'the cause' is flagged too): a human decides.
Verdict: fail if any critical, needs-revision if any major, otherwise pass. A pass is a recommendation for
human approval, never an approval.

Usage: python3 audit_report.py report.md --artefact name=path [...] [--claims claims.json]
                               [--evidence-register evidence_register.json]
"""
import json
import re
import sys

SECTIONS = ["Executive summary", "Business context", "Data sources", "Methodology", "Metric definitions", "Key findings",
            "Cross-module insights", "Opportunities", "Risks", "Recommendations", "BIDIM prioritisation", "Limitations",
            "Next steps"]
EXEMPT = {"Methodology", "Metric definitions"}
TAG = re.compile(r"\[(CALC|FACT|PATTERN|HYP|INTERP|REC|ASSUME|UNKNOWN):([^\]]+)\]")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\w)\+?\(?\d{2,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}(?!\w)")
SECRET = re.compile(r"(api[_-]?key\s*[=:]|secret\s*[=:]|password\s*[=:]|\bAKIA[0-9A-Z]{16}\b|\bsk_(live|test)_\w+)", re.I)
CAUSAL = re.compile(r"\b(drives?|drove|driven by|caus(e|es|ed)|because( of)?|due to|leads? to|led to|results? in|thanks to)\b", re.I)
NUM = re.compile(r"(?<![\w.-])\d[\d,]*(?:\.\d+)?%?(?![\w-])")


def strip_noise(text):
    text = TAG.sub(" ", text)
    text = re.sub(r"\b\d{4}-\d{2}(-\d{2})?\b", " ", text)          # dates
    text = re.sub(r"\b(19|20)\d{2}\b", " ", text)                   # years
    text = re.sub(r"\b[A-Z]{1,5}-?\d+\b", " ", text)                # IDs such as C006, OPP-01, H1, INV-1029
    text = re.sub(r"\b[A-Z]+-\d+\b", " ", text)
    return text


def get_path(data, path):
    for key in path.split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def parse_sections(md):
    """Return [(section_name, line_no, line)] for body lines; the appendix is labelled 'Appendix'."""
    current, out = None, []
    for n, line in enumerate(md.splitlines(), 1):
        m = re.match(r"^##\s+(?:\d+\.\s*)?(.+?)\s*$", line)
        if m:
            current = "Appendix" if m.group(1).lower().startswith("appendix") else m.group(1)
            continue
        out.append((current, n, line))
    return out


def units(line):
    if line.strip().startswith("|"):
        return [line]
    return [u for u in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", line) if u.strip()]


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    md = open(a[0]).read()
    artefacts, i = {}, 1
    claims, register_path = [], None
    while i < len(a):
        if a[i] == "--artefact":
            name, path = a[i + 1].split("=", 1)
            artefacts[name] = json.load(open(path))
            i += 2
        elif a[i] == "--claims":
            claims = json.load(open(a[i + 1]))
            i += 2
        elif a[i] == "--evidence-register":
            register_path = a[i + 1]
            i += 2
        else:
            sys.exit(f"unknown argument {a[i]}")
    known = {e["id"] for d in artefacts.values() for e in d.get("evidence", [])}
    if register_path:
        known |= {e["id"] for e in json.load(open(register_path))}

    issues, checks, unsupported = [], [], []

    def issue(sev, cat, loc, detail, fix):
        issues.append({"severity": sev, "category": cat, "location": loc, "detail": detail, "required_correction": fix})

    body = parse_sections(md)
    present = {s for s, _, _ in body if s}
    for s in SECTIONS:
        if s not in present:
            issue("major", "structure", "report", f"missing section '{s}'", f"add the '{s}' section (may state 'not in scope')")

    first = md.splitlines()[:5]
    if any(re.search(r"approved", l, re.I) and "AUDITED" not in l for l in first):
        issue("major", "status", "header", "report claims approval", "use 'DRAFT – not audited'; only a human sets approval")

    for cls, ids in TAG.findall(md):
        for eid in re.split(r"[;,]\s*", ids):
            if eid.strip() not in known:
                issue("critical", "traceability", f"[{cls}:{eid.strip()}]", "evidence ID does not resolve", "cite an existing evidence item or remove the claim")

    rev, cust, bidim = artefacts.get("revenue"), artefacts.get("customer"), artefacts.get("bidim")
    for c in claims:
        art, _, path = c["metric"].partition(":")
        try:
            actual = get_path(artefacts[art], path)
        except (KeyError, IndexError, ValueError):
            issue("major", "calculation", c["id"], f"cannot resolve {c['metric']}", "supply the artefact or fix the metric path")
            continue
        ok = abs(float(actual) - float(c["value"])) <= c.get("tolerance", 0.005)
        checks.append({"source": "claims.json", "claim": c["id"], "text": c["text"], "stated": c["value"], "recomputed": actual, "match": ok})
        if not ok:
            issue("critical", "calculation", c["id"], f"stated {c['value']}, recomputed {actual} ({c['metric']})", "correct the figure or its scope")

    segments = list(cust["segments"]) if cust else []
    seen_values = {}

    def compare(loc, unit, metric, stated, expected, label):
        stated_f = float(stated.replace(",", ""))
        decimals = len(stated.split(".")[1]) if "." in stated else 0
        ok = expected is not None and round(float(expected), decimals) == round(stated_f, decimals)
        checks.append({"source": "independent text scan", "location": loc, "metric": label, "stated": stated_f, "recomputed": expected, "match": ok})
        seen_values.setdefault(label, set()).add(stated_f)
        if not ok:
            issue("critical", "calculation", loc, f"{label}: text says {stated}, recomputed {expected}", "correct the figure, or state the scope it actually measures")
            unsupported.append({"location": loc, "text": unit.strip()[:200]})

    for section, n, line in body:
        if section in (None, "Appendix") or line.startswith("#") or line.strip().startswith("<!--"):
            continue  # title block, appendix, headings and comments are not claims
        loc = f"line {n} ({section})"
        for unit in units(line):
            seg = next((s for s in segments if re.search(rf"\b{re.escape(s)}\b", unit, re.I)), None)
            if rev:
                for metric, key in (("NRR", "nrr_pct"), ("GRR", "grr_pct")):
                    long = "net revenue retention" if metric == "NRR" else "gross revenue retention"
                    after = rf"(?:{long}|\b{metric}\b)[^%\[\n]{{0,60}}?(\d+(?:\.\d+)?)%"
                    before = rf"(\d+(?:\.\d+)?)%\s*(?:{long}|\b{metric}\b)"
                    for m in list(re.finditer(after, unit, re.I)) + list(re.finditer(before, unit, re.I)):
                        if seg and metric == "NRR" and cust:
                            compare(loc, unit, metric, m.group(1), cust["segments"][seg]["nrr_pct"], f"{seg} NRR")
                        elif not seg:
                            compare(loc, unit, metric, m.group(1), rev["retention"][key], f"company {metric}")
                        if "window" not in unit.lower():
                            issue("minor", "caveat", loc, f"{metric} without a window label", "state the measurement window, for example '5-month window'")
                for m in re.finditer(r"(?:grew|growth of|up|increased)\s+(?:by\s+)?(\d+(?:\.\d+)?)%", unit, re.I):
                    if re.search(r"\b(MRR|revenue|ARR)\b", line, re.I):
                        compare(loc, unit, "growth", m.group(1), rev["growth"]["growth_pct"], "MRR growth")
                for m in re.finditer(r"(?:logo|customer) churn[^%\[\n]{0,40}?(\d+(?:\.\d+)?)%", unit, re.I):
                    compare(loc, unit, "logo churn", m.group(1), rev["retention"]["logo_churn_pct"], "logo churn")
                for m in re.finditer(r"collection rate[^%\[\n]{0,60}?(\d+(?:\.\d+)?)%", unit, re.I):
                    compare(loc, unit, "collection rate", m.group(1), rev["collections"]["collection_rate_pct"], "collection rate")
                for m in re.finditer(r"(?<![\w-])(\d+)\s+(active\s+|paying\s+)?customers\b", unit, re.I):
                    active = rev["monthly"][-1]["active_customers"]
                    entities = len(cust["customers"]) if cust else None
                    stated = int(m.group(1))
                    allowed = {active} if m.group(2) else {active, entities}
                    ok = stated in allowed
                    checks.append({"source": "independent text scan", "location": loc, "metric": "customer count", "stated": stated,
                                   "recomputed": {"active_at_end": active, "entities": entities}, "match": ok})
                    if not ok:
                        issue("critical", "calculation", loc, f"customer count {stated} matches neither active customers ({active}) nor de-duplicated entities ({entities})",
                              "use the de-duplicated count and say which count it is")
                        unsupported.append({"location": loc, "text": unit.strip()[:200]})
                    elif not m.group(2):
                        issue("minor", "caveat", loc, "customer count without saying active or total entities", "qualify the count")
            if unit is units(line)[0] and re.search(r"Confidence:\**\s*(Very high|High|Medium|Low|Insufficient)\.?\s*$", line):
                issue("minor", "caveat", loc, "confidence level without a reason", "add 'Why: ...'")
            if section in EXEMPT:
                continue
            if NUM.search(strip_noise(unit)) and not TAG.search(unit):
                issue("major", "traceability", loc, f"number without evidence: {unit.strip()[:120]!r}", "cite the evidence ID or remove the number")
                unsupported.append({"location": loc, "text": unit.strip()[:200]})
            for m in CAUSAL.finditer(unit):
                issue("major", "causation", loc, f"causal wording {m.group(0)!r}: {unit.strip()[:120]!r}",
                      "rephrase as association, or cite a tested causal design")
            if re.search(r"\b(gross margin|CAC|LTV|lifetime value)\b[^.\n]{0,40}\d", unit, re.I):
                issue("major", "calculability", loc, "gross margin, CAC or LTV stated with a number", "check the metric dictionary; these were not calculable")
            if re.search(r"\bactivation\b[^.\n]{0,60}\d+(\.\d+)?%", unit, re.I) and not re.search(r"\bn\s*=|\bof \d+", unit):
                issue("minor", "caveat", loc, "activation rate without sample size", "state n")

    for n, line in enumerate(md.splitlines(), 1):
        for pat, what in ((EMAIL, "email address"), (PHONE, "phone number"), (SECRET, "credential-like string")):
            if pat.search(line):
                issue("critical", "privacy", f"line {n}", f"{what} in report", "remove it; reports carry no personal data or secrets")

    in_bidim = False
    for n, line in enumerate(md.splitlines(), 1):
        if line.startswith("## "):
            in_bidim = "BIDIM" in line
            continue
        if not in_bidim or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 11 or not re.fullmatch(r"OPP-\d+", cells[1]):
            continue
        oid, vals = cells[1], cells[3:8]
        stated = re.search(r"\d+(\.\d+)?", cells[10])
        if all(v.isdigit() for v in vals) and stated and "range" not in cells[10]:
            I, C, S, E, R = map(int, vals)
            recomputed = round(I * C * S / (E * R), 2)
            ok = abs(recomputed - float(stated.group(0))) <= 0.01
            checks.append({"source": "BIDIM row", "location": f"line {n}", "metric": f"{oid} priority", "stated": float(stated.group(0)),
                           "recomputed": recomputed, "match": ok})
            if not ok:
                issue("critical", "bidim", f"line {n}", f"{oid}: stated priority {stated.group(0)}, inputs give {recomputed}", "recompute with bidim_score.py")
        if bidim:
            ref = next((r for r in bidim["ranking"] if r["id"] == oid), None)
            if ref and ref["priority"] is not None and stated and abs(ref["priority"] - float(stated.group(0))) > 0.01:
                issue("critical", "bidim", f"line {n}", f"{oid}: report priority {stated.group(0)} differs from BIDIM output {ref['priority']}",
                      "use the BIDIM artefact's values")

    for label, vals in seen_values.items():
        if len(vals) > 1:
            issue("major", "contradiction", "report", f"{label} stated with different values: {sorted(vals)}", "use one value consistently")

    order = {"critical": 0, "major": 1, "minor": 2}
    issues.sort(key=lambda x: order[x["severity"]])
    counts = {s: sum(x["severity"] == s for x in issues) for s in order}
    verdict = "fail" if counts["critical"] else "needs-revision" if counts["major"] else "pass"
    print(json.dumps({
        "verdict": verdict, "summary": counts,
        "approval_recommendation": {"fail": "Do not release. Correct critical issues and re-audit.",
                                    "needs-revision": "Do not release yet. Resolve major issues and re-audit.",
                                    "pass": "No blocking issues found by automated checks. Recommend human review and approval; "
                                            "automated checks do not cover every claim."}[verdict],
        "issues": issues, "calculation_checks": checks, "unsupported_claims": unsupported,
    }, indent=2))
    sys.exit({"pass": 0, "needs-revision": 1, "fail": 2}[verdict])


if __name__ == "__main__":
    main()
