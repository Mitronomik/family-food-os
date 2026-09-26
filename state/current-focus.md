# Current focus

Updated: 2026-09-26.

## Accepted state

PR94 / Step 10 Contract Gate is merged into main at:

4f9331a8fa73f8488a07295076b0425c00e6654e

Russian-data integration Steps 1–9 and the Step 10 implementation contract are accepted.

## Current bounded state

**Step 10-A — Composition-backed Recipe Nutrition Authority runtime implementation.**

Branch:

feat/step10a-recipe-v2-nutrition

Draft PR:

#95

## Authorized scope

- migration 0039;
- Nutrition-owned immutable RecipeIngredient → exact FoodCompositionVersion binding;
- exact Step 9 production binding;
- canonical 54-code V2 RecipeVersion Nutrition;
- RECIPE_COMPOSITION_NUTRITION_V1;
- neutral compatibility/readiness projection;
- legacy NutritionService preservation;
- migration/publication/replay/adversarial verification.

## Hard boundaries

- no Planner/MealPlan behavior change;
- no planner-v0.3 runtime work;
- no Recipe activation;
- no MealRole compatibility change;
- no optional/ml/pcs/transformed-root expansion in Recipe V1;
- no source-corpus expansion;
- no API/UI/Shopping/Prep/Retail/Auth/PostgreSQL/AI scope.

## Current implementation

Initial runtime and exact production publication are implemented on the feature branch.

Verification is pending. Draft PR95 must remain unmerged until full Step 10-A acceptance passes.

## Stop boundary

Deliver Step 10-A to review-ready PR95 and stop.
Step 10-B remains unauthorized until Step 10-A is reviewed and merged.
