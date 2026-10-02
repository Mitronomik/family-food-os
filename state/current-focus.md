# Current focus

Updated: 2026-10-02.

## Accepted state

PR #126 / R1-C is merged into `main` at:

`8995e85e4cda2ae30fc62fdc63daaf441f4226bd`.

R1-C proved the ordinary production path end to end with
`planner-v0.4 / meal-role-recipe-v2`, persisted MealPlan/Serving history,
deterministic replay, bounded infeasibility and member-local hard exclusions.

Current active exact-energy Planner capacity before R2:

- BREAKFAST: 1 RecipeVersion — `HARD_BOILED_EGG`;
- MAIN: 3 RecipeVersions;
- `max_recipe_repetitions=3`;
- MAIN capacity: 9 opportunities/week;
- BREAKFAST capacity: 3 opportunities/week.

Issue #99 requires the next R2 batch to maximize marginal realistic weekly variety
and Planner capacity.

## Current bounded operation

**R2 — Breakfast Planner-capacity runtime batch.**

Issue: `#127`.

Branch: `feat/r2-breakfast-capacity`.

Accepted base:

`8995e85e4cda2ae30fc62fdc63daaf441f4226bd`.

Status:

`IMPLEMENTATION_ACTIVE`.

## Decision

Selected School2022 cards:

- `ru-school2022:recipe:54-1о` — Омлет натуральный —
  150 g / exact 225.5 kcal;
- `ru-school2022:recipe:54-9к` — Каша вязкая молочная овсяная —
  200 g / exact 272.9 kcal.

Both are bounded household-applicability reviews, not blanket School2022
authority.

If both activate, the ordinary breakfast pool becomes:

- `HARD_BOILED_EGG`;
- `SCHOOL2022_54_1O_NATURAL_OMELET`;
- `SCHOOL2022_54_9K_MILK_OAT_PORRIDGE`.

Projected BREAKFAST capacity becomes 9 opportunities/week under unchanged
repetition=3.

## Authority and identities

Reuse only the accepted prepared-output seam:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE; all other frozen nutrient codes remain UNKNOWN.

Create identity-only, without Nutrition/Composition authority:

- `MILK_2_5` — Молоко 2,5%;
- `OAT_GROATS` — Крупа овсяная.

Do not substitute nearby milk-fat forms or `OATS_ROLLED`.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add another Nutrition authority kind;
- infer raw→cooked Nutrition, yield or retention;
- add Nutrition/Composition to the new identities;
- change Planner algorithm/scoring/roles/repetition;
- add allergen automation;
- publish School2022 54-1р in this PR;
- infer missing USSR82 salt/energy linkage;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Verification target

R2 must prove:

- exact hash-pinned source/publication contract;
- fresh/replay/deactivation semantics;
- identity-only enforcement;
- tamper/partial/conflict fail-closed behavior;
- two active exact-energy breakfast RecipeVersions;
- ordinary pool = three exact-energy breakfasts;
- persisted seven-BREAKFAST week under repetition=3;
- hard FoodIngredient exclusion;
- migration head remains 0042;
- `AI_ENABLED=false`.

## Next step

Run exact-head focused R2 verification, fix only task-local defects, freeze the
reviewed proof/runtime head, then hand PR #128 (or the created R2 PR number) to
independent final review.

After R2 merge, reassess the next R2/R3 corpus batch. Do not start DC4,
Gate1-CLOSE or PR9 automatically.
