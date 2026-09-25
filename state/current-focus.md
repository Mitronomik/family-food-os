# Current focus

Updated: `2026-09-25`.

## Accepted state

PR90 / corrected Step 8 Contract Gate is merged into `main` at
`76ca8f8ffba589576af4e0fad4d7a4817a84089f`.

Russian-data integration Steps 1–7 and the Step 8 Contract Gate are accepted.

## Current bounded task

**Step 8 runtime/data publication — one recipe-dependency butter bundle.**

Branch:
`feat/step8-recipe-dependency-butter-runtime`.

Canonical contract:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Authorized scope

Publish exactly one reviewed production bundle:

```text
BUTTER_PEASANT_72_5_UNSALTED
→ FIC RU-NUT-DB code 1417 / DB/533
→ non-current FoodNutritionProfile
→ 17-value RU_NUTRIENT_REGISTRY_V2 vector
→ ATOMIC v1 / INPUT
```

Required source/form guards:

- exact FIC raw record SHA-256
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- exact `salt_ad=0.0` remains source-only form evidence for no added salt;
- `salt_ad` is not a V2 nutrient and sodium never infers salinity;
- non-zero/null/missing salt evidence fails closed;
- `water=null` remains unknown and WATER is absent from the vector;
- existing generic `BUTTER_UNSALTED` / USDA FDC 173430 remains unchanged.

## Architecture boundary

Reuse existing Step 3/4 reviewed nutrition publication service and project UoW.

Expected:
- no shared publication-service semantic change;
- no schema/migration;
- migration head remains 0038;
- reserved 0033 remains unconsumed.

## Hard stops

No:
- additional food;
- Step 9 RecipeVersion;
- Step 10 Planner integration;
- production transformation/yield/retention factors;
- API/UI/Retail/AI/Auth/PostgreSQL;
- generalized ingestion.

If implementation disproves the no-schema/shared-semantics assumption, stop and
reopen the Contract Gate.

## Stop boundary

Deliver Step 8 runtime/data PR to review-ready state, then stop.

Do not merge autonomously and do not start Step 9.
