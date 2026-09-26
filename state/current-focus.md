# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / final compatibility-semantic blocker correction is implemented; exact-head verification is pending.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

Exhaustive exact-head review #5326205581 superseded the prior READY receipt and
found one remaining compatibility blocker.

## Correction implemented

The V2 → legacy Nutrition crosswalk is now exact and part of
`RECIPE_COMPOSITION_NUTRITION_V1`:

- kcal ← ENERGY_KCAL;
- protein_g ← PROTEIN;
- fat_g ← FAT_TOTAL;
- carbohydrates_g ← CARBOHYDRATE_BY_DIFFERENCE **only**;
- fiber_g ← FIBER_TOTAL_DIETARY.

No CARBOHYDRATE_AVAILABLE fallback exists.
STARCH + SUGARS_TOTAL cannot synthesize legacy carbohydrates.

For the exact Step 9 butter result:
- CARBOHYDRATE_BY_DIFFERENCE remains UNKNOWN;
- legacy carbohydrates_g remains None;
- legacy five-field status remains INCOMPLETE;
- exact ENERGY_KCAL may still satisfy the separately versioned Planner readiness
  path in Step 10-B.

## Frozen Step 10-A authority

- binding ownership: Nutrition;
- one Nutrition-owned UoW / one connection / one transaction;
- registry: RU_NUTRIENT_REGISTRY_V2;
- nutrient set: RECIPE_V2_NUTRIENT_SET_V1 = exact 54-code V2 registry snapshot;
- Composition calculation: FOOD_COMPOSITION_APPLICABILITY_V2;
- Recipe calculation: RECIPE_COMPOSITION_NUTRITION_V1;
- Recipe V1 supports required exact gram rows only;
- optional rows fail closed;
- transformed/non-INPUT root outputs fail closed;
- unknown nutrients remain explicit UNKNOWN;
- exact Step 9 canonical result is PARTIAL;
- historical reads use pinned authority and do not depend on later FoodIngredient.is_active;
- publication/replay still requires active dependency.

## Frozen Step 10-B authority

- Planner algorithm version: exactly planner-v0.3;
- MealRole compatibility version: exactly meal-role-recipe-v2;
- neutral Nutrition projection is shared by Planner and MealPlan/Serving;
- no production Step 9 Recipe activation.

## Stop boundary

Do not merge until corrected exact-head verification and re-review complete.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
