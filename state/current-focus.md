# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / final-corrected Step 10 Contract Gate is review-ready.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Corrected semantic head:

5e2d9a9336a94798327e3a9445e0dffd41e05ff9

Corrected semantic review:

#5326221930 — READY TO MERGE FINAL-CORRECTED STEP 10 CONTRACT GATE

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

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
- canonical Step 9 result is PARTIAL;
- legacy compatibility crosswalk is exact:
  - kcal ← ENERGY_KCAL;
  - protein_g ← PROTEIN;
  - fat_g ← FAT_TOTAL;
  - carbohydrates_g ← CARBOHYDRATE_BY_DIFFERENCE only;
  - fiber_g ← FIBER_TOTAL_DIETARY;
- CARBOHYDRATE_AVAILABLE and STARCH+SUGARS never substitute for legacy carbohydrates;
- exact Step 9 legacy carbohydrates_g is None and legacy status is INCOMPLETE;
- historical reads use pinned authority and do not depend on later FoodIngredient.is_active;
- publication/replay still requires active dependency.

## Frozen Step 10-B authority

- Planner algorithm version: exactly planner-v0.3;
- MealRole compatibility version: exactly meal-role-recipe-v2;
- neutral Nutrition projection is shared by Planner and MealPlan/Serving;
- no production Step 9 Recipe activation.

## Verification

On semantic head 5e2d9a9336a94798327e3a9445e0dffd41e05ff9:

- Docs #375 — SUCCESS;
- DC1 #237 — SUCCESS;
- Registry focused — 328 passed;
- Partial focused — 276 passed;
- contract sections 1–29 sequential;
- adversarial acceptance 1–74 sequential;
- mergeable=true;
- 0 behind main;
- trailing whitespace=0;
- conflict markers=0;
- unresolved review threads=0.

Automatic broad Registry/Partial regression is supplemental for this docs-only gate.

## Stop boundary

PR94 is ready for final merge review.

Do not merge autonomously.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
