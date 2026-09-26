# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / Step 10 Contract Gate blocker correction is implemented; exact-head verification is pending.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

Independent re-review #5325781916 superseded the earlier READY receipts and found
three contract gaps.

## Corrections implemented

1. RecipeIngredientCompositionBinding is explicitly Nutrition-owned derived
   calculation authority.
2. Step 10-A uses one focused Nutrition-owned authority UoW / one active
   connection and transaction for all dependency reads, classification and the
   binding write.
3. FRESH and EXACT_REPLAY both re-resolve exact Recipe/row, active FoodIngredient,
   Composition, V2 vector/registry and calculation inside that UoW.
4. External preflight is fail-fast only and cannot authorize publication.
5. The immutable calculation policy is exactly
   FOOD_COMPOSITION_APPLICABILITY_V2 and must equal the returned
   CompositionResult.calculation_version.
6. Adversarial acceptance now covers post-preflight deactivation, replay recheck,
   policy mismatch and late-write rollback.

## Frozen implementation sequence

### Step 10-A — not yet authorized

After gate merge and separate authorization:

- migration 0039;
- Nutrition-owned immutable RecipeIngredient → exact FoodCompositionVersion binding;
- exact Step 9 production binding;
- canonical V2 RecipeVersion Nutrition;
- neutral Nutrition consumption projection;
- legacy NutritionService preservation.

### Step 10-B — not yet authorized

Only after Step 10-A review/merge and separate authorization:

- Planner V2 exact-energy readiness;
- Planner algorithm version advance;
- MealPlan/Serving neutral Nutrition consumption;
- cross-context regression;
- no migration.

## Hard boundaries

- production School2022 butter Recipe remains inactive;
- ROLE_COMPATIBILITY_V1 and meal-role-recipe-v2 remain unchanged;
- no automatic latest/current Composition selection;
- no partial required-row V1/V2 mixing;
- no WATER/carbohydrate inference;
- no current-profile switch or fake B1 assessment;
- no production activation in Step 10-A or Step 10-B;
- AI_ENABLED=false remains supported.

## Stop boundary

Do not merge until corrected exact-head verification and re-review complete.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
