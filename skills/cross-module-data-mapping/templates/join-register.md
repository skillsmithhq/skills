# Join register

One row per validated or rejected relationship. Profile numbers come from `scripts/profile_join.py`.

| ID | Left dataset.field (entity, grain) | Right dataset.field (entity, grain) | Purpose (question) | Normaliser | Entity map | Row match | Key match | Expected cardinality | Observed | Fan-out | Unmatched (class, count, amount) | Collisions reviewed | Confidence | Risks if misused | Evidence ID |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Confidence: **High** = documented key, ≥ 98% match, expected cardinality, no unreviewed collisions. **Medium** = normalisation needed, 90–98% match, or reviewed collisions. **Low** = under 90% match, unexpected cardinality, or name-based matching.

Rejected relationships stay in the register with the reason (for example "account_name: free text; not an identifier").
