#!/usr/bin/env python3
"""Lint a proposal draft for honesty and completeness problems.

Flags:
  - guarantee or outcome-promise language
  - testimonial, case-study or credential claims (the user must confirm they are real)
  - money amounts outside a [PRICE: ...] placeholder (the user must confirm they set them)
  - missing required sections
  - missing DRAFT status line
The output is a list of items for a human to review, not an approval.

Usage: python3 proposal_lint.py proposal.md
"""
import json
import re
import sys

REQUIRED = ["context", "problem", "scope", "deliverables", "timeline", "responsibilities",
            "data requirements", "exclusions", "pricing", "acceptance criteria", "risks"]
GUARANTEE = re.compile(r"\b(guarantee[sd]?|will (increase|reduce|improve|double|eliminate)|ensures? (a|an|that)|proven|risk[- ]free|\d+x roi)\b", re.I)
SOCIAL_PROOF = re.compile(r"\b(testimonial|case stud(y|ies)|trusted by|clients include|certified|award[- ]winning)\b", re.I)
MONEY = re.compile(r"(?:USD|EUR|GBP|INR|£|€|₹|\$)\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|EUR|GBP|INR)\b")


def lint(text):
    findings = []
    lowered = text.lower()
    headings = " ".join(re.findall(r"^#+ (.+)$", text, re.M)).lower()
    for section in REQUIRED:
        if section not in headings:
            findings.append({"severity": "major", "type": "missing-section", "detail": section})
    if "status: draft" not in lowered:
        findings.append({"severity": "major", "type": "status", "detail": "no 'Status: DRAFT' line"})
    for n, line in enumerate(text.splitlines(), 1):
        for m in GUARANTEE.finditer(line):
            findings.append({"severity": "critical", "type": "guarantee-language", "line": n, "detail": m.group(0)})
        for m in SOCIAL_PROOF.finditer(line):
            findings.append({"severity": "major", "type": "social-proof-claim", "line": n, "detail": m.group(0)})
        stripped = re.sub(r"\[PRICE:[^\]]*\]", "", line)
        for m in MONEY.finditer(stripped):
            findings.append({"severity": "review", "type": "money-amount", "line": n, "detail": m.group(0)})
    return findings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: proposal_lint.py proposal.md")
    found = lint(open(sys.argv[1]).read())
    print(json.dumps({"findings": found, "blocking": sum(f["severity"] in ("critical", "major") for f in found)}, indent=2))
    sys.exit(1 if any(f["severity"] in ("critical", "major") for f in found) else 0)
