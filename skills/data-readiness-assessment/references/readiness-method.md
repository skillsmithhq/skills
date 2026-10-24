# Readiness scoring method

Implemented by `scripts/assess_readiness.py`. Publish this method with every readiness score. A score without its method is not acceptable output.

## Checks by dimension

| Dimension | Weight | Checks (configured per table) |
|---|---|---|
| Completeness | 0.25 | `required_present` for each required field |
| Validity | 0.20 | `iso_4217_currency`, `numeric_non_negative`, `allowed_values`, `parseable_plausible_timestamp` (2000-01-01 to as_of + 1 day; fields in `future_ok` up to 5 years ahead) |
| Uniqueness | 0.20 | `primary_key_unique`, `natural_key_unique`, `no_exact_duplicate_rows` |
| Consistency | 0.10 | `date_order` (end ≥ start), `required_if` (for example an end date when status is cancelled) |
| Referential integrity | 0.15 | `foreign_key_match` (exact value match against the referenced table) |
| Timeliness and coverage | 0.10 | `daily_coverage` (days with records between the first and last valid timestamp), `freshness` (days since the last record ≤ max age) |

## Arithmetic

- Check pass rate = passing / applicable. Checks with no applicable rows are skipped, not scored as 100%.
- For uniqueness checks, passing = number of distinct keys, so each surplus duplicate counts as one failure.
- Dimension score = mean pass rate of its checks × 100.
- Table score = Σ(weight × dimension score) / Σ(weight), over dimensions that have checks.

## Levels

| Score | Level | Label |
|---|---|---|
| ≥ 95 | 5 | ready |
| ≥ 85 | 4 | minor issues |
| ≥ 70 | 3 | usable with caveats |
| ≥ 50 | 2 | major remediation needed |
| < 50 | 1 | unusable |

Caps, applied after scoring:

- **Critical** (primary key not unique; required field < 95% complete; foreign key match < 90%): level ≤ 3
- **Major** (any other failing validity, uniqueness or coverage check): level ≤ 4

Why caps exist: averages hide concentrated problems. In the synthetic fixture, subscriptions scores 99.03, yet one subscription has no start date, so its MRR cannot be placed in time. That table is "usable with caveats", not "ready".

## What the score does not measure

- **Accuracy against reality.** A value can be valid and wrong. Accuracy needs reconciliation with an independent source (for example billing totals against finance ledger totals) and is reported separately as a reconciliation finding.
- **Schema stability over time.** Compare schemas across exports manually, or across repeated inventory runs.
- **Whether a field means what its name suggests** (see `business-data-inventory`).
- **Exact-match foreign keys** understate matches when identifiers need normalisation. The normalised match rate comes from `cross-module-data-mapping`.
