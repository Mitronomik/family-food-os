# Current focus

Updated: 2026-09-26.

## Accepted state

PR94 / Step 10 Contract Gate is merged into main at:

`4f9331a8fa73f8488a07295076b0425c00e6654e`

Russian-data integration Steps 1–9 and the Step 10 implementation contract are accepted.

## Current bounded state

**PR95 / Step 10-A — Composition-backed Recipe Nutrition Authority is review-ready.**

Branch:

`feat/step10a-recipe-v2-nutrition`

Verified runtime head:

`3c779c7a0184be6f6838720b6fde78dbe482e8e8`

Semantic/runtime review:

`#5326633449 — READY TO MERGE STEP 10-A`

## Implemented authority

- migration `0039_recipe_ingredient_composition_binding`;
- Nutrition-owned immutable RecipeIngredient → exact FoodCompositionVersion binding;
- exact authority pins:
  - `RU_NUTRIENT_REGISTRY_V2`;
  - `RECIPE_V2_NUTRIENT_SET_V1`;
  - `FOOD_COMPOSITION_APPLICABILITY_V2`;
  - `RECIPE_COMPOSITION_NUTRITION_V1`;
- one exact Step 9 production binding publisher;
- canonical 54-code RecipeVersion V2 Nutrition;
- neutral legacy/V2 consumption projection;
- exact BY_DIFFERENCE-only legacy carbohydrate crosswalk;
- legacy `NutritionService.recipe_version()` preserved.

## Exact Step 9 truth

- Recipe remains inactive;
- binding targets required 10 g `BUTTER_PEASANT_72_5_UNSALTED`;
- exact Composition v1 / ATOMIC / INPUT;
- canonical result = PARTIAL;
- 17 accepted nutrients AVAILABLE;
- remaining requested concepts UNKNOWN;
- WATER UNKNOWN;
- CARBOHYDRATE_AVAILABLE UNKNOWN;
- CARBOHYDRATE_BY_DIFFERENCE UNKNOWN;
- legacy carbohydrates_g = None;
- legacy five-field status = INCOMPLETE.

## Step 10-A policy boundary

`RECIPE_COMPOSITION_NUTRITION_V1` supports only:
- required gram rows;
- untransformed INPUT-basis Composition;
- Decimal-only scaling/aggregation;
- exact base-serving division;
- one six-decimal result-boundary quantization.

Optional rows, ml/pcs rows and transformed/yielded roots fail closed.

## Verification

On runtime head `3c779c7a0184be6f6838720b6fde78dbe482e8e8`:

- Docs #404 — SUCCESS;
- DC1 #266 — SUCCESS;
- Russian nutrition methodologies #153 — SUCCESS (**380 passed**);
- Nutrient Registry V2 #257 — SUCCESS:
  - focused **352 passed**;
  - backend shards **1073 / 836 / 753 / 956 passed**;
  - launcher **643 passed, 2 skipped**;
- Partial nutrition profiles #197 — SUCCESS:
  - focused **300 passed**;
  - backend shards green;
  - launcher **643 passed, 2 skipped**;
- `AI_ENABLED=false`;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0;
- trailing whitespace=0;
- conflict markers=0;
- no added task-marker placeholders.

## Hard boundary

No Planner/MealPlan behavior change occurred.
No `planner-v0.3` runtime work occurred.
No Recipe activation occurred.
No Step 10-B work is authorized yet.

## Stop boundary

PR95 is ready for final review / explicit merge authorization.

Do not merge autonomously.

After PR95 merge, stop. Step 10-B requires a separate explicit authorization.
