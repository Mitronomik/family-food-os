# Current focus

Updated: `2026-09-23`.

## Accepted state

PR84 is merged into `main` at
`3de3c58ee898284f8d2168af1aae04af754a6bfc`.

Russian-data integration Steps 1–5 are accepted.

Current bounded work is **Step 6 — persisted member reference-methodology
selection, corrected Implementation Contract Gate only**.

Canonical gate:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

## Corrected Step 6 split

The PR85 adversarial re-review blockers are resolved by a mandatory runtime split:

```text
Step 6A
MemberReferenceMethodologySelection persistence
→ expected migration 0036

Step 6B
MealPlan member reference-methodology pins + immutable member target-input snapshot
→ expected migration 0037
```

Step 6A and Step 6B are separate runtime PRs with a merge/review stop between
them.

## Ownership boundary

Member reference selection owns:

- required `FAMILY_FOOD_NUTRITION_V1` personal baseline;
- optional
  `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1` group-reference add-on.

It does **not** own `RU_SOURCE_NATIVE_*` food interpretation policy.

Source-native policy remains food/calculation truth and must be pinned later at
the owning calculation/plan receipt boundary when V2 food/recipe calculation is
integrated.

## Replay/concurrency boundary

Step 6A uses:

- persisted `acceptance_request_id` for exact command replay;
- `expected_current_selection_id` for ordinary optimistic concurrency;
- Household/member updated-at token revalidation.

Bundle equality alone cannot turn a stale command into replay.

Step 6B later freezes `MealPlan.week_start` as the target reference date and
pins authoritative member target inputs without backfilling historical plans.

## Current authorization

Docs/state Contract Gate only.

No 0036/0037 migration, runtime selection/pin tables, repository/service code,
Planner/API/UI default change, Step 7+ implementation before this gate is
reviewed and merged.

## Stop boundary

Deliver/review corrected PR85. After merge, stop. Step 6A runtime requires
separate explicit authorization.
