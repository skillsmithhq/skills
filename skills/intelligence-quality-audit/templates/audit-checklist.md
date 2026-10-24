# Manual audit checklist (covers what audit_report.py cannot check)

Record each failure as an issue: severity | category | location | detail | required correction.

## Calculations and scope
- [ ] Three or more numbers outside the script's coverage traced to their artefacts
- [ ] The scope of every metric matches its label (company / segment / cohort / period)
- [ ] De-duplicated entity counts are used; the entity rule is stated

## Joins
- [ ] Every cross-module finding uses a relationship from the join register
- [ ] No relationship rated Low supports a High-confidence finding
- [ ] Unmatched shares are disclosed beside the results that depend on them

## Statistics and forecasts
- [ ] Sample sizes are stated beside rates; n < 30 is flagged
- [ ] Comparisons with fewer than 5 events are capped at Low
- [ ] No significance claims without a named test
- [ ] Forecasts list assumptions and stay at Medium confidence or below

## Claims and language
- [ ] Each causal flag is either rephrased or backed by a causal design
- [ ] Interpretations are labelled, with an alternative reading
- [ ] No guarantees, investment advice or valuations

## Recommendations
- [ ] Each has an owner, dependencies, a next action and a measurement
- [ ] None requires production access or credentials without approval

## Limitations and scope honesty
- [ ] Exclusions (records and amounts), windows, coverage gaps and non-calculable metrics are disclosed
- [ ] Nothing material from readiness or mapping is missing from Limitations

## Confidentiality
- [ ] No personal data, credentials or other clients' data
- [ ] Aggregation is appropriate for the audience
