# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / Step 10 Contract Gate deep-review blocker correction is implemented; exact-head verification is pending.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

Deep independent review #5326074689 superseded the prior READY receipt and found
three additional semantic blockers.

## Corrections implemented

1. Canonical Recipe V2 request set is exact
   `RECIPE_V2_NUTRIENT_SET_V1`: all 54 codes of
   `RU_NUTRIENT_REGISTRY_V2`. Unknown concepts remain explicit UNKNOWN rather
   than disappearing by request omission.
2. Recipe-level calculation is separately versioned as
   `RECIPE_COMPOSITION_NUTRITION_V1`, above
   `FOOD_COMPOSITION_APPLICABILITY_V2`.
3. V1 recipe policy freezes exact input-mass scaling, unknown propagation,
   required-row aggregation, no optional rows, untransformed INPUT-basis scope,
   per-serving division and one six-decimal result-boundary rounding.
4. Step 10-B Planner version is exactly `planner-v0.3`;
   `meal-role-recipe-v2` remains the compatibility version.
5. Historical canonical reads after a binding exists do not depend on later
   mutable FoodIngredient active state; active remains a publication/replay guard.

## Frozen implementation sequence

### Step 10-A — not yet authorized

After PR94 merge and separate authorization:

- migration 0039;
- Nutrition-owned immutable RecipeIngredient → exact FoodCompositionVersion binding;
- exact RECIPE_V2_NUTRIENT_SET_V1;
- FOOD_COMPOSITION_APPLICABILITY_V2;
- RECIPE_COMPOSITION_NUTRITION_V1;
- exact Step 9 production binding;
- canonical V2 RecipeVersion Nutrition;
- neutral Nutrition consumption projection;
- legacy NutritionService preservation.

### Step 10-B — not yet authorized

Only after Step 10-A review/merge and separate authorization:

- Planner V2 exact-energy readiness;
- exact planner-v0.3 algorithm version;
- MealPlan/Serving neutral Nutrition consumption;
- meal-role-recipe-v2 compatibility unchanged;
- cross-context regression;
- no migration.

## Stop boundary

Do not merge until corrected exact-head verification and re-review complete.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
