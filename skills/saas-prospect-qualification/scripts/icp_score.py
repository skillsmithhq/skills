#!/usr/bin/env python3
"""Deterministic ICP score from a scorecard JSON file.

Score    = sum(score x weight) / sum(2 x weight), over known criteria only
Coverage = known weight / total weight
Band: strong (score >= 70 and coverage >= 60), possible (45-69, or strong on low coverage),
      weak (< 45), disqualified (any hard disqualifier present).

Usage: python3 icp_score.py scorecard.json
"""
import json
import sys

DEFAULT_WEIGHTS = {
    "recurring_revenue": 3, "size_band": 2, "multiple_systems": 3, "product_complexity": 2,
    "no_inhouse_bi": 2, "growth_signal": 1, "decision_maker_role": 1,
}


def score(card):
    weights = {**DEFAULT_WEIGHTS, **card.get("weights", {})}
    if card.get("disqualifiers"):
        return {"company": card.get("company"), "band": "disqualified", "disqualifiers": card["disqualifiers"],
                "score_pct": None, "coverage_pct": None, "problems": []}
    problems, points, max_points, known_w = [], 0, 0, 0
    criteria = card.get("criteria", {})
    for name, w in weights.items():
        c = criteria.get(name, {"score": None})
        s = c.get("score")
        if s is None:
            continue
        if s not in (0, 1, 2):
            problems.append(f"{name}: score must be 0, 1, 2 or null")
            continue
        if not c.get("evidence"):
            problems.append(f"{name}: scored without evidence; treated as unknown")
            continue
        points += s * w
        max_points += 2 * w
        known_w += w
    for name in criteria:
        if name not in weights:
            problems.append(f"{name}: unknown criterion ignored")
    total_w = sum(weights.values())
    coverage = round(100 * known_w / total_w, 1) if total_w else 0.0
    pct = round(100 * points / max_points, 1) if max_points else None
    if pct is None:
        band = "insufficient-information"
    elif pct >= 70 and coverage >= 60:
        band = "strong"
    elif pct >= 45:
        band = "possible"
    else:
        band = "weak"
    return {"company": card.get("company"), "score_pct": pct, "coverage_pct": coverage, "band": band,
            "points": points, "max_points": max_points, "problems": problems}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: icp_score.py scorecard.json")
    with open(sys.argv[1]) as f:
        print(json.dumps(score(json.load(f)), indent=2))
