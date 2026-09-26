# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / corrected Step 10 Recipe V2 Nutrition / Planner Integration Contract Gate is review-ready.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Corrected semantic head:

c23bca0e6df4787f8f083a976fd6257e454d1777

Corrected semantic review:

#5325809090 — READY TO MERGE CORRECTED STEP 10 CONTRACT GATE

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

## Corrected authority contract

- RecipeIngredientCompositionBinding is Nutrition-owned derived calculation authority.
- Step 10-A uses one focused Nutrition-owned authority UoW, one connection and
  one transaction.
- Recipe/RecipeVersion/RecipeIngredient, FoodIngredient, Composition, vector and
  registry dependencies are read-only inside that UoW.
- FRESH and EXACT_REPLAY both re-resolve dependencies and require active
  FoodIngredient inside the authoritative UoW.
- external preflight is fail-fast only.
- calculation policy is exactly FOOD_COMPOSITION_APPLICABILITY_V2 and must match
  CompositionResult.calculation_version.
- adversarial acceptance covers deactivation-after-preflight, replay recheck,
  wrong policy and late binding rollback.

## Frozen implementation sequence

### Step 10-A — not yet authorized

After PR94 merge and separate authorization:

- migration 0039;
- immutable Nutrition-owned RecipeIngredient → exact FoodCompositionVersion binding;
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

## Critical boundaries

- production School2022 butter Recipe remains inactive;
- ROLE_COMPATIBILITY_V1 and meal-role-recipe-v2 remain unchanged;
- no automatic latest/current Composition selection;
- no partial required-row V1/V2 mixing;
- no WATER/carbohydrate inference;
- no current-profile switch or fake B1 assessment;
- no production activation in Step 10-A or Step 10-B;
- AI_ENABLED=false remains supported.

## Verification

On corrected semantic head c23bca0e6df4787f8f083a976fd6257e454d1777:

- Docs #368 — SUCCESS;
- DC1 #230 — SUCCESS;
- Registry focused — 328 passed;
- Partial focused — 276 passed;
- mergeable=true;
- 0 behind main;
- section numbering 1–29 sequential;
- trailing whitespace = 0;
- conflict markers = 0.

## Stop boundary

PR94 is ready for final merge review.

Do not merge autonomously.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
