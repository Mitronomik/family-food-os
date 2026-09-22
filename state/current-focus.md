# Current focus

Updated: `2026-09-22`.

## Accepted state

PR80 is merged into `main` at `f7ac885dde055900b3a6397aa64a15fe698abe5b`.

Steps 1–3 and the Step 4 Implementation Contract Gate are accepted.

Current bounded work is **Step 4B — licensed RU-NUT-DB source-semantic mapping
closure**.

Evidence:
`data/curation/ru-nut-db-step4-semantic-closure/`.

## Mapping result

For the exact five records
`SUGAR / CARROT_RED_RAW / CABBAGE_GREEN / BEET / RICE_GROATS`:

- 130 source nutrient observations retained;
- 87 published numeric + 43 published zero;
- 18 source fields approved for positive-value V2 mapping;
- 74 positive candidate V2 values total;
- every published zero remains nonnumeric;
- 8 fields remain deferred/source-only;
- no Book2002 numeric substitution.

Per-food positive V2 counts:
`7 / 17 / 17 / 17 / 16`.

## Mapping result

The exact five-food closure approves 18 source fields for every published numeric
literal, including source-published zero.

Result:

- 130 source observations retained;
- 90 V2 numeric candidate values — 18 per food;
- 8 fields remain deferred/source-only;
- SUGAR `prot=0` / `fat=0` use existing numeric VALUE semantics with literal
  zero and explicit provenance;
- no migration/schema change is required.

## Runtime readiness

After this evidence PR is merged/reviewed, Step 4 runtime may implement the
accepted five-food batch using the exact mapping manifest.

## Stop boundary

After the Step 4B evidence PR is review-ready/merged, stop for the explicit
architecture decision. Do not start migration/runtime publication or Step 5
automatically.
