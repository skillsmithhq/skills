#!/usr/bin/env python3
"""BIDIM opportunity scoring: transparent, guarded prioritisation (see references/bidim-framework.md).

Priority = (Impact x Confidence x Strategic fit) / (Effort x Risk), inputs integers 1-5.
Guards, in order:
  1. evidence guard        no CALC or FACT evidence -> confidence capped at 2
  2. confidence reason     confidence without a rationale is treated as missing
  3. data gate             data_readiness <= 2 -> status blocked-data, ranked after all unblocked
  4. missing values        priority range from least to most favourable values; rank on the lower bound
  5. tiebreak              shorter time to value, then higher confidence, then id
Sensitivity: each of I, C, S, E, R moved by +/-1 (within 1-5), one at a time; best and worst rank recorded;
a spread of more than one place -> rank-sensitive.
This is a heuristic for ordering discussion, not a valuation or a forecast.

Usage: python3 bidim_score.py register.json
"""
import json
import sys

INPUTS = ["impact", "confidence", "strategic_fit", "effort", "risk"]
BENEFIT = {"impact", "confidence", "strategic_fit"}


def clean(o):
    """Apply guards 1-2 and return (scores used, notes)."""
    s = {k: o["scores"].get(k) for k in INPUTS + ["data_readiness", "time_to_value"]}
    notes = []
    for k, v in s.items():
        if v is not None and (not isinstance(v, int) or not 1 <= v <= 5):
            raise SystemExit(f"{o['id']}: {k} must be an integer 1-5 or null")
    if s["confidence"] is not None and not o.get("rationale", {}).get("confidence"):
        s["confidence"] = None
        notes.append("confidence has no rationale: treated as missing")
    strong = any(e["class"] in ("CALC", "FACT") for e in o.get("evidence", []))
    cap = None if strong else 2
    if cap and s["confidence"] is not None and s["confidence"] > cap:
        notes.append(f"evidence guard: no CALC/FACT evidence, confidence capped {s['confidence']} -> {cap}")
        s["confidence"] = cap
    return s, cap, notes


def priority(s, cap=None, fill="low"):
    vals = {}
    for k in INPUTS:
        v = s[k]
        if v is None:
            v = (1 if k in BENEFIT else 5) if fill == "low" else (5 if k in BENEFIT else 1)
        if k == "confidence" and cap:
            v = min(v, cap)
        vals[k] = v
    return vals["impact"] * vals["confidence"] * vals["strategic_fit"] / (vals["effort"] * vals["risk"])


def rank(items):
    """items: list of dicts with id, lower, blocked, ttv, conf. Returns {id: rank}."""
    order = sorted(items, key=lambda x: (x["blocked"], -x["lower"], x["ttv"] if x["ttv"] is not None else 6,
                                         -(x["conf"] or 0), x["id"]))
    return {x["id"]: i + 1 for i, x in enumerate(order)}


def summarise(o, s, cap):
    blocked = s["data_readiness"] is not None and s["data_readiness"] <= 2
    return {"id": o["id"], "lower": priority(s, cap, "low"), "blocked": blocked, "ttv": s["time_to_value"], "conf": s["confidence"]}


def main():
    reg = json.load(open(sys.argv[1]))
    prepared = []
    for o in reg["opportunities"]:
        s, cap, notes = clean(o)
        prepared.append((o, s, cap, notes))
    base_items = [summarise(o, s, cap) for o, s, cap, _ in prepared]
    ranks = rank(base_items)

    results = []
    for idx, (o, s, cap, notes) in enumerate(prepared):
        missing = [k for k in INPUTS if s[k] is None]
        lo, hi = priority(s, cap, "low"), priority(s, cap, "high")
        seen = [ranks[o["id"]]]
        for k in INPUTS:
            if s[k] is None:
                continue
            for delta in (-1, 1):
                v = s[k] + delta
                if not 1 <= v <= 5:
                    continue
                trial = dict(s, **{k: v})
                items = list(base_items)
                items[idx] = summarise(o, trial, cap)
                seen.append(rank(items)[o["id"]])
        blocked = base_items[idx]["blocked"]
        labels = []
        if blocked:
            labels.append("blocked-data")
        if missing:
            labels.append("incomplete")
        if not blocked and not missing and (s["effort"] or 5) <= 2 and (s["time_to_value"] or 5) <= 2 and (s["confidence"] or 0) >= 3:
            labels.append("quick-win")
        if not blocked and (s["impact"] or 0) >= 4 and (s["strategic_fit"] or 0) >= 4 and (s["effort"] or 0) >= 4:
            labels.append("strategic-bet")
        if s["confidence"] is not None and s["confidence"] <= 2:
            labels.append("investigate-first")
        if max(seen) - min(seen) > 1:
            labels.append("rank-sensitive")
        results.append({
            "id": o["id"], "title": o["title"], "decision": o["decision"], "rank": ranks[o["id"]],
            "status": "blocked-data" if blocked else ("incomplete" if missing else "scored"),
            "scores_used": s, "missing_inputs": missing,
            "priority": round(lo, 2) if not missing else None,
            "priority_range": [round(lo, 2), round(hi, 2)],
            "normalised_score": round(lo / 125 * 100, 1),
            "sensitivity": {"best_rank": min(seen), "worst_rank": max(seen)},
            "labels": labels, "guard_notes": notes,
            "evidence": o.get("evidence", []), "rationale": o.get("rationale", {}),
            "assumptions": o.get("assumptions", []), "missing_evidence": o.get("missing_evidence", []),
            "next_action": o.get("next_action", ""),
        })
    results.sort(key=lambda r: r["rank"])
    print(json.dumps({
        "skill": "bidim-opportunity-scoring", "engagement_id": reg["engagement_id"], "impact_basis": reg["impact_basis"],
        "formula": "(impact x confidence x strategic_fit) / (effort x risk)", "disclaimer": "Prioritisation heuristic; not a valuation or forecast.",
        "ranking": results,
        "evidence": [{"id": f"bidim-{r['id'].lower()}", "class": "CALC", "produced_by": "bidim-opportunity-scoring",
                      "statement": f"{r['id']} rank {r['rank']}, priority {r['priority'] if r['priority'] is not None else r['priority_range']}, "
                                   f"labels {', '.join(r['labels']) or 'none'}"} for r in results],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: bidim_score.py register.json")
    main()
