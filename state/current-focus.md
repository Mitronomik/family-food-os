# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**Step 10 Recipe V2 Nutrition / Planner Integration Contract Gate — docs-only.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

## Preflight findings

- general Nutrition still uses legacy current-profile / B1 authority;
- RecipeIngredient does not persist an exact FoodCompositionVersion binding;
- selecting latest/current Composition would break historical reproducibility;
- Step 9 meal_type=other is intentionally incompatible with current automatic MealRoles;
- Step 9 sparse V2 truth has exact energy but canonical carbohydrate remains unknown.

## Current gate decision

- future runtime adds immutable RecipeIngredient → CompositionVersion authority binding, expected migration 0039;
- legacy NutritionService.recipe_version() remains unchanged;
- new canonical V2 RecipeVersion Nutrition consumption is explicit;
- Planner receives a V2-safe exact-energy projection without globally relaxing legacy INCOMPLETE semantics;
- production Step 9 butter Recipe remains inactive;
- MealRole compatibility remains unchanged.

## Authorization boundary

This branch is documentation/preflight only.

No migration, runtime code, persisted binding, Recipe activation or Planner behavior change is authorized until this gate is reviewed and merged.

## Stop boundary

Deliver this Step 10 Contract Gate to review-ready state, then stop.

Do not merge autonomously and do not start Step 10 runtime.
