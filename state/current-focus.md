# Current focus

Updated: `2026-09-17`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #31–#45 remain accepted historical research/governance evidence.
- PR #46 is MERGED; dataset-independence and web-corroboration governance is active.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR #52 / `POST-PR51-STATE-SYNC` = COMPLETE.
- Accepted implementation base for PR7: `ded1cca29e165e0c459288d8de58df114abdeabb`.
- Accepted SQLite migration head on that base: `0031_meal_pattern_catalogue`.
- Migration number `0032` is reserved for PR7 MealPlan / Serving persistence; future RecipeTemplate reservation is `0033_recipe_template_catalogue`.

## Current authorized operation

`PR7 — MealPlan / Serving` is ACTIVE under Issue #53.

Branch:

`feature/pr7-mealplan-serving`

Goal: establish Household-owned accepted member meal-pattern state and a manually constructible, revisioned seven-day MealPlan with explicit source kinds, individualized Servings and deterministic Serving/member/day/week nutrition reads before PR8 automation.

## PR7 bounded scope

- immutable/versioned `MemberMealPatternSelection` history;
- exact published MealPatternProgramVersion provenance or `CUSTOM`;
- resolved seven-day member schedule snapshot with heterogeneous/day-specific 1–6 opportunity support without a permanent DB max-six law;
- append-only MealPlan revisions and pinned member-selection provenance;
- Household meal events with explicit `MealRole` and source kind;
- `COOK_RECIPE` pins immutable RecipeVersion; non-recipe sources do not require fake RecipeVersions;
- member participation via individualized Decimal Servings;
- Serving nutrition plus member/day/week aggregation through the existing Nutrition contract with unknown propagation;
- Household-scoped repositories/UoW/read scopes using synchronous SQLAlchemy Core;
- forward migration `0032_meal_plan_serving` (or a more precise bounded suffix if implementation evidence requires it);
- focused + migration + full backend/launcher verification required before review-ready.

## Architecture boundary

- `MealPatternProgram` remains platform-owned catalogue truth.
- `MemberMealPatternSelection` is Household-owned accepted state.
- `MealRole != RecipeVersion.meal_type_code`.
- `Recipe != Serving`.
- `representable != Planner-selectable` for non-recipe sources.
- Nutrition Engine remains authoritative for nutrient truth; PR7 may scale/aggregate its outputs but must not duplicate formulas.
- true instants are UTC; plan dates are Household-local calendar dates.
- technical datasets/seeds remain replaceable artifacts, not domain invariants.
- deterministic core works with `AI_ENABLED=false`.

## Explicit non-goals

Do not add or start:

- PR8 automatic Planner generation/recommender ranking/reconciliation;
- Recipe Constructor / RecipeAssembly implementation;
- Shopping / Prep / authoritative leftover or PreparedBatch supply;
- Retail / ready-food provider integration;
- AI Gateway;
- Auth/PostgreSQL/shared deployment;
- frontend/onboarding UI;
- medical/therapeutic planning;
- legacy `Order` rename/reuse as MealPlan.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ POST-PR51-STATE-SYNC                       COMPLETE (#52)
→ PR7 MealPlan / Serving                     ACTIVE (#53)
→ PR8 Planner v0                             NOT STARTED
→ GATE 1 — Planning Core                     NOT STARTED
```

After PR7 is review-ready and merged, stop. Do not begin PR8 automatically; it requires separate explicit authorization.
