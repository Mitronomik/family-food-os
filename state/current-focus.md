# Current focus

Updated: `2026-09-22`.

## Accepted state

PR82 is merged into `main` at
`aa5ebcb4c70c9adee0fd1242f520ef1298f6b167`.

Russian-data integration Steps 1–4 are accepted through the first licensed
RU-NUT-DB runtime publication.

Current bounded work is **Step 5 — reviewed Russian reference table,
Implementation Contract Gate / adversarial preflight only**.

## Step 5 proposed first table

Source:
`МР 2.3.1.0253-21`, pinned PDF SHA-256
`cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79`.

Frozen proposed table identity:

`RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`.

Bounded V1 scope:

- adult only;
- exact source header `Старше 18 лет` → completed age 19+;
- male/female only;
- KFA-independent rows only;
- source tables 11/12 and 16/17;
- exactly 24 reviewed canonical definitions × 2 sexes = 48 rows;
- scalar `ready_source_group_lookup` claims only.

Deferred:
energy/macros, percent-energy references, child rows, pregnancy/lactation,
footnote-dependent Vitamin D/Calcium, adequate-level tables 13/18 (including
fluoride), folate/Vitamin K definition mismatches and source nutrients without a
V2 target.

Canonical gate:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

## Current authorization

Docs/state Contract Gate only.

Do not publish numeric reference rows, wire a runtime provider, persist
methodology selection, change Planner/API/UI defaults or consume a migration
before this gate is reviewed and merged.

## Stop boundary

Deliver and review the Step 5 Contract Gate. Do not start runtime Step 5
automatically.
