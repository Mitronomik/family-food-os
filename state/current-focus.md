# Current focus

Updated: `2026-09-22`.

## Accepted state

PR81 is merged into `main` at
`be6eed3591752d38ece3de5892e4306134e8d762`.

Steps 1–3, the Step 4 contract gate and Step 4B semantic mapping closure are
accepted.

Current bounded work is **Step 4C — runtime publication of the first licensed
RU-NUT-DB five-food batch**.

## Exact batch

- `SUGAR` ← RU-NUT-DB code 1150, reuse existing identity, ATOMIC v2;
- `CARROT_RED_RAW` ← code 1187, create reviewed identity, ATOMIC v1;
- `CABBAGE_GREEN` ← code 1184, reuse existing identity, ATOMIC v2;
- `BEET` ← code 1204, reuse existing identity, ATOMIC v1;
- `RICE_GROATS` ← code 66, create reviewed identity, ATOMIC v1.

All new compositions use `MassState.INPUT`.

## Runtime contract

Implementation must:

- consume only the hash-pinned licensed FIC payload and the merged Step 4B
  18-field mapping;
- publish exactly 90 V2 values, 18 per food, including source-published numeric
  zeros;
- retain all 26 source fields per food in source observations;
- keep `carbh` and the other seven deferred fields non-canonical;
- create only non-current FIC profiles;
- preserve all existing current USDA profiles, including generic `CARROT`;
- keep public single-bundle Step 3 behavior unchanged;
- use one transaction-neutral bundle operation plus one five-food batch UoW;
- commit a fresh five-food batch exactly once;
- make exact replay zero-write with stable persisted IDs;
- roll back the whole batch on any food conflict/failure;
- introduce no schema/migration.

Canonical contract:
`docs/family-food/first-russian-food-batch-contract.md`.

Runtime payload:
`data/curation/ru-nut-db-step4-runtime/`.

## Scope boundary

No Step 5 Russian reference table, methodology persistence, transformation
applicability, recipe publication, Planner, Shopping, API/UI or AI authority.

## Stop boundary

Deliver the bounded runtime PR through exact-head verification and final review.
Do not merge autonomously and do not start Step 5 automatically.
