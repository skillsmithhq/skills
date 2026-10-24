# ICP scorecard

Score each criterion 0, 1, 2 or `unknown`. Every score needs an evidence ID.

| Criterion | Weight | 0 | 1 | 2 |
|---|---|---|---|---|
| recurring_revenue | 3 | No recurring element | Mixed: recurring plus significant one-off or services | Subscription or usage-based recurring revenue is primary |
| size_band | 2 | Outside band by more than 2x | Near the band edge | Inside the target band (default 20–500 staff) |
| multiple_systems | 3 | Single system, or unknown tools | 2 operational systems evidenced | 3 or more systems evidenced (billing, CRM, product analytics, support...) |
| product_complexity | 2 | Single plan, single product | Several plans or some add-ons | Several modules, plans and integrations |
| no_inhouse_bi | 2 | Visible data or BI team | One analyst role, or unclear | No data roles visible, and evidence of manual reporting |
| growth_signal | 1 | Shrinking or no signal | Some hiring | Funding, expansion or significant hiring |
| decision_maker_role | 1 | No relevant role visible | Generic leadership only | A role owning operations, revenue or data is visible |

Absence of evidence (for example no data roles on a careers page) is weak evidence. Score it at most 1 unless it is corroborated.

Scorecard JSON for `scripts/icp_score.py`:

```json
{
  "company": "Example Fleet Software Ltd",
  "criteria": {
    "recurring_revenue": {"score": 2, "evidence": ["pros-efs-01"]},
    "size_band": {"score": null, "evidence": []}
  }
}
```

`null` means unknown. Weights default to the table above. Pass `"weights": {...}` to override them, and record why.
