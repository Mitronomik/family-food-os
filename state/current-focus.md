# Current focus

Updated: 2026-09-26.

## Accepted state

PR93 / Step 9 runtime is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Russian-data integration Steps 1–9 are accepted.

## Current bounded state

**PR94 / Step 10 Recipe V2 Nutrition / Planner Integration Contract Gate is review-ready.**

Branch:

docs/step10-v2-recipe-nutrition-contract

Semantic head:

761871e36a5a019621eb0c8e7900b2dfcf5e2773

Semantic review:

#5325759751 — READY TO MERGE CONTRACT GATE

Canonical gate:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

## Frozen implementation sequence

### Step 10-A — not yet authorized

After gate merge and separate authorization:

- migration 0039;
- immutable RecipeIngredient → exact FoodCompositionVersion binding;
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

On semantic head 761871e36a5a019621eb0c8e7900b2dfcf5e2773:

- Docs #366 — SUCCESS;
- DC1 #228 — SUCCESS;
- PR mergeable=true;
- 0 behind main;
- changed scope = docs/state only;
- section numbering 1–29 sequential;
- trailing whitespace = 0;
- conflict markers = 0;
- unresolved review threads = 0.

Registry/Partial are automatic broad workflows and are not required for this
docs-only gate under proportional verification. Runtime Step 10-A/B verification
requirements are frozen in the contract.

## Stop boundary

PR94 is ready for final review / explicit merge authorization.

Do not merge autonomously.
Do not start Step 10-A before PR94 is merged and separately authorized.
Step 10-B remains blocked until Step 10-A is reviewed and merged.
