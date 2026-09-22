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

## Current blocker

**Runtime Step 4 is BLOCKED_PENDING_SCHEMA_DECISION.**

SUGAR publishes literal zero for source protein and fat. The zero semantics are
unresolved, but the current persisted observation state supports only
`value/missing/below_detection/method_incompatible`.

None truthfully represents this source state while keeping legacy
`protein_g/fat_g` nullable.

## Architecture decision required

Choose before runtime:

1. preserve the five-food batch by adding a persisted state such as
   `published_zero_unresolved` through a separate migration/domain contract; or
2. keep the schema unchanged and defer SUGAR, reducing the first batch to four.

This evidence PR does not choose or implement either option.

## Stop boundary

After the Step 4B evidence PR is review-ready/merged, stop for the explicit
architecture decision. Do not start migration/runtime publication or Step 5
automatically.
