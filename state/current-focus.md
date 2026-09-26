# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / deep-corrected Step 10 Recipe V2 Nutrition / Planner Integration Contract Gate is review-ready.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Corrected semantic head:

560cce41e1c1ce54212052bd95dfc8fe4b0cdb13

Corrected semantic review:

#5326161326 — READY TO MERGE DEEP-CORRECTED STEP 10 CONTRACT GATE

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
- exact Step 9 canonical result is PARTIAL: 17 AVAILABLE + remaining requested UNKNOWN;
- historical reads use pinned authority and do not depend on later FoodIngredient.is_active;
- publication/replay still requires active dependency.

## Frozen Step 10-B authority

- Planner algorithm version: exactly planner-v0.3;
- MealRole compatibility version: exactly meal-role-recipe-v2;
- neutral Nutrition projection is shared by Planner and MealPlan/Serving;
- no production Step 9 Recipe activation.

## Verification

On corrected semantic head 560cce41e1c1ce54212052bd95dfc8fe4b0cdb13:

- Docs #373 — SUCCESS;
- DC1 #235 — SUCCESS;
- Registry focused — 328 passed;
- Partial focused — 276 passed;
- exact 54/54 nutrient-set comparison — PASS;
- contract sections 1–29 sequential;
- adversarial acceptance 1–68 sequential;
- mergeable=true;
- 0 behind main;
- trailing whitespace=0;
- conflict markers=0;
- unresolved review threads=0.

Automatic broad Registry/Partial jobs are supplemental for this docs-only gate
under the canonical proportional verification policy.

## Stop boundary

PR94 is ready for final merge review.

Do not merge autonomously.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
