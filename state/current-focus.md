# Current focus

Updated: `2026-09-25`.

## Accepted state

PR89 / Step 7 transformation applicability runtime is merged into `main` at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Russian-data integration Steps 1–7 are accepted.

## Current bounded state

**PR90 / Step 8 Contract Gate blocker correction is under exact-head review.**

Branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Corrected form-authority decision

The previous review correctly found one gap: School2022 requires unsalted butter,
while FIC DB/533's display name does not itself say `несолёное`.

The gate now freezes the exact source-owned binding:

- FIC DB/533 / code 1417 is the selected 72.5% peasant-butter numeric authority;
- DB/533 exact source field `salt_ad = 0.0`;
- frozen source label: `Добавленная соль`;
- Step 4 disposition remains `SOURCE_ONLY_NO_V2_TARGET`;
- Step 8 uses that exact literal only as form-compatibility evidence for
  **no added salt**;
- `salt_ad` does not enter the V2 vector;
- sodium is never used to infer salinity;
- non-zero/null/missing salt evidence fails closed.

The frozen FoodIngredient remains
`BUTTER_PEASANT_72_5_UNSALTED`, where UNSALTED is explicitly defined for this
binding as no added salt.

## Preserved Step 8 contract

- future Step 9 target remains School2022 `53-19з`;
- exactly one Step 8 food dependency;
- FIC raw record hash remains
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- `water=null` remains unknown;
- expected V2 vector remains exactly 17 values;
- source profile remains non-current;
- ATOMIC v1 / INPUT;
- no yield/retention/transformation/applicability publication;
- no migration/schema; head remains 0038 and 0033 remains reserved.

## Hard boundaries

No Step 8 runtime/data publication before corrected PR90 is reviewed/merged.

No Step 9 RecipeVersion, Step 10 Planner integration, extra FIC foods,
production retention/yield factors, API/UI/Retail/AI/Auth/PostgreSQL.

## Stop boundary

Reverify corrected semantic head with Docs/DC1, then finalize PR90 for review.
No merge is performed autonomously.
