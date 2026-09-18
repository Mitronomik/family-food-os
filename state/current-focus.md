# Current focus

Updated: `2026-09-18`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- Post-PR54 state synchronization/cleanup = COMPLETE through merged PRs #55 and #56.
- Accepted PR8 implementation base: `3ca80a7815301689baa409b1c129471a03a01f68`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

`PR8 — Planner v0` is ACTIVE under Issue #57.

Suggested implementation branch:

`feature/pr8-planner-v0`

Goal: implement the simplest useful deterministic, explainable household week planner that produces either a complete seven-day MealPlan revision with individualized Servings and reproducible trace evidence, or an explicit bounded infeasibility result.

Issue #57 is the bounded implementation contract.

## PR8 bounded scope

- deterministic/versioned Planner configuration and request/trace models;
- deterministic Meal Pattern Recommender over curated published programs;
- compilation of accepted heterogeneous member meal-pattern selections;
- versioned `MealRole` → Recipe Catalogue suitability rules without changing Recipe truth;
- hard exclusion filtering before scoring;
- deterministic household reconciliation/sharedness heuristics;
- complete seven-day generation or explicit bounded failure;
- individualized Decimal Serving allocation through existing Nutrition truth;
- read-only Pantry signal where authoritative;
- preservation of user-fixed non-recipe events without autonomous non-recipe selection;
- append-only MealPlan revision creation;
- reproducible candidate/rejection/score/selection/warning trace;
- repository-backed Gate 1 fixture evidence for 3 households / 30 verified recipes / 80+ FoodIngredient.

## Architecture / migration boundary

- deterministic core works with `AI_ENABLED=false`;
- Planner consumes Household, Meal Pattern, Recipe, Nutrition, Pantry and MealPlan truth; it does not redefine those contexts;
- unknown nutrition/cost/supply remains unknown;
- Household-owned reads/writes remain Household-scoped;
- no OR-Tools, AI, Retail, new optimizer service or datastore;
- no new schema/migration is expected by default;
- migration `0033_recipe_template_catalogue` must not be consumed or renumbered by PR8 without a separate approved decision;
- generation-time exclusions/preferences may be explicit Planner request values because no canonical persisted member preference/exclusion model exists yet.

## Explicit non-goals

Do not add or start:

- PR9 Shopping Engine;
- Gate 1 closure;
- Prep / Freezer / PreparedBatch;
- authoritative leftover supply;
- Retail / ready-food provider truth;
- AI Gateway / LLM;
- Auth/PostgreSQL/shared deployment;
- frontend/onboarding/PDF;
- RecipeTemplate / RecipeAssembly implementation;
- automatic ORDER_OUT/EAT_OUT selection;
- advanced solver/optimization infrastructure;
- medical/therapeutic planning.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ PR7 MealPlan / Serving                     COMPLETE (#53 / PR #54)
→ PR8 Planner v0                             ACTIVE (#57)
→ GATE 1 — Planning Core                     NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

After PR8 is review-ready and merged, stop.

Gate 1 must be reviewed/closed separately using the required end-to-end fixture evidence. Do not begin PR9 automatically.
