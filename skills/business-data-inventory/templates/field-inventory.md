# Field inventory template

One row per field. Types, null and distinct counts come from `scripts/inventory_files.py`. Meaning comes from the client's documentation or the data owner, never from the field name alone.

| Dataset | Field | Inferred type | Nulls | Distinct | Candidate key? | Business meaning | Meaning source (doc / owner role / unconfirmed) | Unit / currency | Timezone | Personal data? | Shared name elsewhere | Same meaning confirmed? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

Grain statement per dataset: "One row per <entity> per <time unit>". Example: "invoices.csv: one row per invoice (but 1 exact duplicate row present)".
